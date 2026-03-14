"""Claude Vision-powered cover analysis.

Sends cover images to Claude for structured analysis of typography,
color, layout, genre signaling, and thumbnail readability.
"""

import json
import logging

from anthropic import Anthropic

from .config import Config
from .images import image_to_base64, make_thumbnail, get_media_type

logger = logging.getLogger(__name__)


FULL_ANALYSIS_PROMPT = """You are a professional book cover analyst specializing in Amazon Kindle market analysis.
Analyze this book cover image for the {genre} genre.

Consider: typography (font weight, size, case, readability), color palette (dominant colors, contrast),
layout (visual hierarchy, composition, whitespace), imagery (background, mood, elements),
genre signaling (does it look like a {genre} book?), and professional quality.

Return ONLY valid JSON (no markdown fences, no explanation):
{{
    "title_text": "<what you can read as the title, or 'unreadable' if not legible>",
    "author_text": "<what you can read as the author, or 'unreadable'>",
    "subtitle_text": "<subtitle if visible, or null>",
    "title_font_weight": "<thin|light|medium|bold|heavy>",
    "title_case": "<upper|title|lower|mixed>",
    "title_size_relative": "<small|medium|large|dominant>",
    "title_contrast": "<low|medium|high|extreme>",
    "dominant_colors": [
        {{"name": "<color name>", "hex": "<approximate #RRGGBB>", "area": "<background|text|accent>"}}
    ],
    "background_type": "<photographic|illustrated|gradient|solid|textured|composite>",
    "background_mood": "<one or two words describing the mood>",
    "layout_style": "<centered|top-heavy|bottom-heavy|asymmetric|split>",
    "visual_hierarchy": "<title-dominant|image-dominant|balanced>",
    "has_subtitle": <true|false>,
    "has_series_line": <true|false>,
    "has_decorative_elements": <true|false>,
    "genre_signals": ["<list of elements that signal this genre>"],
    "genre_match": "<strong|moderate|weak|mismatch>",
    "professional_quality": <1-10>,
    "notable_strengths": ["<up to 3 specific strengths>"],
    "notable_weaknesses": ["<up to 3 specific weaknesses>"],
    "overall_impression": "<one sentence summary>"
}}"""


THUMBNAIL_PROMPT = """You are evaluating a book cover at Amazon search-result thumbnail size (150px wide).
This is EXACTLY what a shopper sees when browsing Amazon search results.

Can you read the title? Can you identify the genre? Does it grab attention?

Return ONLY valid JSON (no markdown fences):
{{
    "title_readable": <true|false>,
    "title_text_if_readable": "<what you can make out, or null>",
    "author_readable": <true|false>,
    "genre_identifiable": <true|false>,
    "genre_guess": "<your best genre guess from the thumbnail alone>",
    "grabs_attention": <true|false>,
    "thumbnail_impact": <1-10>,
    "issues_at_thumbnail": ["<specific problems visible at this size>"]
}}"""


BATCH_COMP_PROMPT = """You are a professional book cover analyst. Analyze these {count} competitor book covers
from the {genre} genre. For EACH cover (labeled Cover 1 through Cover {count}), provide a brief analysis.

Return ONLY valid JSON (no markdown fences):
{{
    "covers": [
        {{
            "index": <1-based index>,
            "title_text": "<title if readable>",
            "title_font_weight": "<thin|light|medium|bold|heavy>",
            "title_case": "<upper|title|lower|mixed>",
            "title_size_relative": "<small|medium|large|dominant>",
            "title_contrast": "<low|medium|high|extreme>",
            "dominant_color_mood": "<e.g. dark/moody, bright/warm, muted/elegant>",
            "background_type": "<photographic|illustrated|gradient|solid|textured>",
            "layout_style": "<centered|top-heavy|bottom-heavy|asymmetric>",
            "genre_match": "<strong|moderate|weak>",
            "professional_quality": <1-10>,
            "standout_element": "<one thing this cover does well>"
        }}
    ],
    "category_trends": {{
        "dominant_color_scheme": "<what color scheme most comps use>",
        "typical_font_weight": "<what font weight is most common>",
        "typical_layout": "<most common layout pattern>",
        "typical_background": "<most common background type>",
        "average_quality": <1-10 average across all comps>
    }}
}}"""


def _call_claude_vision(images_with_labels, prompt, max_tokens=2000):
    """Send images to Claude Vision and get structured JSON response.

    Args:
        images_with_labels: list of (label, PIL.Image) tuples
        prompt: text prompt
        max_tokens: max response tokens

    Returns:
        Parsed JSON dict, or None on failure.
    """
    if not Config.has_anthropic_key():
        logger.warning("No Anthropic API key — cannot analyze covers")
        return None

    content = []
    for label, img in images_with_labels:
        b64 = image_to_base64(img)
        content.append({'type': 'text', 'text': f'--- {label} ---'})
        content.append({
            'type': 'image',
            'source': {
                'type': 'base64',
                'media_type': get_media_type('PNG'),
                'data': b64,
            },
        })
    content.append({'type': 'text', 'text': prompt})

    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=Config.MODEL,
        max_tokens=max_tokens,
        messages=[{'role': 'user', 'content': content}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith('```'):
        text = text.split('\n', 1)[1]
        if text.endswith('```'):
            text = text[:-3].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.debug(f"Raw response: {text[:500]}")
        return None


def analyze_cover(img, genre='thriller'):
    """Analyze a single cover image at full size.

    Returns a dict with structured analysis, or None on failure.
    """
    prompt = FULL_ANALYSIS_PROMPT.format(genre=genre)
    result = _call_claude_vision([('Your Cover', img)], prompt)
    if result:
        result['_analysis_type'] = 'full'
    return result


def analyze_thumbnail(img, genre='thriller'):
    """Analyze a cover at Amazon thumbnail size (150px wide).

    Returns a dict with thumbnail-specific analysis, or None on failure.
    """
    thumb = make_thumbnail(img, width=Config.AMAZON_THUMBNAIL_WIDTH)
    prompt = THUMBNAIL_PROMPT.format()
    result = _call_claude_vision([('Thumbnail', thumb)], prompt)
    if result:
        result['_analysis_type'] = 'thumbnail'
    return result


def analyze_comps_batch(images, genre='thriller', batch_size=4):
    """Analyze multiple competitor covers in batches.

    Args:
        images: list of (filename, PIL.Image) tuples
        genre: genre name for context
        batch_size: images per API call (4 is a good balance of cost/quality)

    Returns:
        dict with 'covers' list and 'category_trends' summary.
    """
    all_covers = []
    all_trends = []

    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        labeled = [(f'Cover {i + j + 1}: {name}', img) for j, (name, img) in enumerate(batch)]
        prompt = BATCH_COMP_PROMPT.format(count=len(batch), genre=genre)

        result = _call_claude_vision(labeled, prompt, max_tokens=3000)
        if result:
            all_covers.extend(result.get('covers', []))
            if 'category_trends' in result:
                all_trends.append(result['category_trends'])

    # Merge trends from all batches
    merged_trends = _merge_trends(all_trends) if all_trends else {}

    return {
        'covers': all_covers,
        'category_trends': merged_trends,
        'comp_count': len(all_covers),
    }


def _merge_trends(trends_list):
    """Merge category trends from multiple batches into a single summary."""
    if len(trends_list) == 1:
        return trends_list[0]

    # Average the quality scores
    avg_quality = sum(t.get('average_quality', 5) for t in trends_list) / len(trends_list)

    # Take the most common values for categorical fields
    return {
        'dominant_color_scheme': trends_list[0].get('dominant_color_scheme', 'unknown'),
        'typical_font_weight': trends_list[0].get('typical_font_weight', 'bold'),
        'typical_layout': trends_list[0].get('typical_layout', 'centered'),
        'typical_background': trends_list[0].get('typical_background', 'photographic'),
        'average_quality': round(avg_quality, 1),
    }
