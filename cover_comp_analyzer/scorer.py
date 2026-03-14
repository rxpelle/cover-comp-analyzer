"""Scoring engine for cover analysis.

Takes raw Claude Vision analysis data and produces dimensional scores,
actionable flags, and an overall grade. Compares user's cover against
comp set and genre conventions.
"""

from dataclasses import dataclass, field
from .config import Config
from .genres import get_genre


GRADE_THRESHOLDS = [
    (9.0, 'A', 'Excellent — competitive with top sellers'),
    (8.0, 'A-', 'Very strong — minor improvements possible'),
    (7.0, 'B+', 'Good — a few areas need attention'),
    (6.0, 'B', 'Solid — several improvements recommended'),
    (5.0, 'B-', 'Adequate — meaningful changes needed'),
    (4.0, 'C', 'Below average — significant issues'),
    (3.0, 'D', 'Weak — major redesign recommended'),
    (0.0, 'F', 'Not competitive — start over'),
]


@dataclass
class DimensionScore:
    """Score for a single analysis dimension."""
    name: str
    display_name: str
    score: float  # 0-10
    weight: float
    flags: list = field(default_factory=list)
    details: str = ''


@dataclass
class ScoreCard:
    """Complete scorecard for a cover analysis."""
    dimensions: list  # list of DimensionScore
    overall_score: float
    grade: str
    grade_description: str
    critical_flags: list  # CRITICAL issues
    warning_flags: list  # WARNING issues
    tip_flags: list  # TIP suggestions
    comp_summary: dict = field(default_factory=dict)

    @property
    def weighted_score(self):
        return sum(d.score * d.weight for d in self.dimensions)


def score_cover(full_analysis, thumbnail_analysis, genre='thriller', comp_data=None):
    """Score a cover based on its analysis data.

    Args:
        full_analysis: dict from analyze_cover()
        thumbnail_analysis: dict from analyze_thumbnail()
        genre: genre name for convention matching
        comp_data: optional dict from analyze_comps_batch()

    Returns:
        ScoreCard with dimensional scores and flags.
    """
    genre_profile = get_genre(genre)
    if not genre_profile:
        genre_profile = get_genre('thriller')

    weights = Config.SCORING_WEIGHTS
    dimensions = []

    # 1. Thumbnail readability (25%)
    dimensions.append(_score_thumbnail(thumbnail_analysis, weights['thumbnail_readability']))

    # 2. Title typography (15%)
    dimensions.append(_score_typography(full_analysis, genre_profile, weights['title_typography']))

    # 3. Color palette (15%)
    dimensions.append(_score_colors(full_analysis, genre_profile, weights['color_palette']))

    # 4. Layout composition (15%)
    dimensions.append(_score_layout(full_analysis, genre_profile, weights['layout_composition']))

    # 5. Genre signal (15%)
    dimensions.append(_score_genre_signal(full_analysis, genre_profile, weights['genre_signal']))

    # 6. Professional polish (10%)
    dimensions.append(_score_polish(full_analysis, weights['professional_polish']))

    # 7. Competitive differentiation (5%)
    dimensions.append(_score_differentiation(full_analysis, comp_data, weights['competitive_differentiation']))

    # Calculate overall
    overall = sum(d.score * d.weight for d in dimensions)
    grade, grade_desc = _get_grade(overall)

    # Collect all flags by severity
    critical = []
    warnings = []
    tips = []
    for d in dimensions:
        for flag in d.flags:
            if flag.startswith('CRITICAL:'):
                critical.append(flag)
            elif flag.startswith('WARNING:'):
                warnings.append(flag)
            elif flag.startswith('TIP:'):
                tips.append(flag)

    comp_summary = {}
    if comp_data:
        comp_summary = comp_data.get('category_trends', {})

    return ScoreCard(
        dimensions=dimensions,
        overall_score=round(overall, 1),
        grade=grade,
        grade_description=grade_desc,
        critical_flags=critical,
        warning_flags=warnings,
        tip_flags=tips,
        comp_summary=comp_summary,
    )


def _score_thumbnail(thumb, weight):
    """Score thumbnail readability."""
    flags = []
    score = 5.0  # baseline

    if not thumb:
        return DimensionScore('thumbnail_readability', 'Thumbnail Readability',
                              5.0, weight, ['WARNING: Thumbnail analysis unavailable'],
                              'Could not analyze thumbnail')

    title_readable = thumb.get('title_readable', False)
    author_readable = thumb.get('author_readable', False)
    genre_id = thumb.get('genre_identifiable', False)
    grabs = thumb.get('grabs_attention', False)
    impact = thumb.get('thumbnail_impact', 5)
    issues = thumb.get('issues_at_thumbnail', [])

    # Title readability is the most important factor
    if title_readable:
        score += 2.5
    else:
        score -= 3.0
        flags.append('CRITICAL: Title not readable at Amazon thumbnail size — increase font size, weight, or contrast')

    if author_readable:
        score += 0.5

    if genre_id:
        score += 1.0
    else:
        flags.append('WARNING: Genre not identifiable at thumbnail size')

    if grabs:
        score += 1.0
    else:
        flags.append('TIP: Cover doesn\'t grab attention at thumbnail — consider bolder colors or stronger contrast')

    # Factor in Claude's impact rating
    score = (score + impact) / 2

    # Add specific issues as tips
    for issue in issues:
        flags.append(f'TIP: {issue}')

    score = max(0.0, min(10.0, score))
    return DimensionScore('thumbnail_readability', 'Thumbnail Readability',
                          round(score, 1), weight, flags,
                          f'Impact: {impact}/10, Title readable: {title_readable}')


def _score_typography(analysis, genre_profile, weight):
    """Score title typography against genre conventions."""
    flags = []
    score = 5.0

    if not analysis:
        return DimensionScore('title_typography', 'Title Typography',
                              5.0, weight, ['WARNING: Full analysis unavailable'])

    expected = genre_profile['expected_fonts']
    actual_weight = analysis.get('title_font_weight', 'medium')
    actual_case = analysis.get('title_case', 'mixed')
    actual_size = analysis.get('title_size_relative', 'medium')
    actual_contrast = analysis.get('title_contrast', 'medium')

    # Font weight matching
    weight_scores = {'thin': 1, 'light': 2, 'medium': 3, 'bold': 4, 'heavy': 5}
    expected_weight_val = {'medium': 3, 'heavy': 5, 'medium-to-heavy': 4}.get(expected['weight'], 3)
    actual_weight_val = weight_scores.get(actual_weight, 3)

    weight_diff = abs(expected_weight_val - actual_weight_val)
    if weight_diff == 0:
        score += 2.0
    elif weight_diff == 1:
        score += 1.0
    else:
        score -= 1.0
        flags.append(f'WARNING: Font weight "{actual_weight}" — {genre_profile["name"]} covers typically use {expected["weight"]}')

    # Case matching
    if actual_case == expected['case']:
        score += 1.0
    elif expected['case'] == 'upper' and actual_case != 'upper':
        flags.append(f'TIP: Consider uppercase title — standard for {genre_profile["name"]}')

    # Size
    size_scores = {'small': 1, 'medium': 3, 'large': 4, 'dominant': 5}
    if size_scores.get(actual_size, 3) >= 4:
        score += 1.5
    elif actual_size == 'small':
        score -= 2.0
        flags.append('CRITICAL: Title too small — must be large enough to read at thumbnail size')

    # Contrast
    contrast_scores = {'low': 1, 'medium': 3, 'high': 4, 'extreme': 5}
    if contrast_scores.get(actual_contrast, 3) >= 4:
        score += 1.0
    elif actual_contrast == 'low':
        score -= 2.0
        flags.append('CRITICAL: Title contrast too low — text must pop against background')

    score = max(0.0, min(10.0, score))
    return DimensionScore('title_typography', 'Title Typography',
                          round(score, 1), weight, flags,
                          f'Weight: {actual_weight}, Case: {actual_case}, Size: {actual_size}, Contrast: {actual_contrast}')


def _score_colors(analysis, genre_profile, weight):
    """Score color palette against genre conventions."""
    flags = []
    score = 5.0

    if not analysis:
        return DimensionScore('color_palette', 'Color Palette', 5.0, weight)

    genre_match = analysis.get('genre_match', 'moderate')
    match_scores = {'strong': 3.0, 'moderate': 1.0, 'weak': -1.0, 'mismatch': -3.0}
    score += match_scores.get(genre_match, 0)

    # Check for avoided colors
    colors = analysis.get('dominant_colors', [])
    avoided = genre_profile['expected_colors']['avoid']
    for color in colors:
        color_name = color.get('name', '').lower()
        for avoid in avoided:
            if avoid.lower() in color_name:
                score -= 1.0
                flags.append(f'WARNING: "{color_name}" is unusual for {genre_profile["name"]} — consider {", ".join(genre_profile["expected_colors"]["accent"][:2])} instead')
                break

    # Contrast check
    contrast = analysis.get('title_contrast', 'medium')
    if contrast in ('low',):
        score -= 1.5
        flags.append('CRITICAL: Insufficient contrast between text and background colors')

    score = max(0.0, min(10.0, score))
    return DimensionScore('color_palette', 'Color Palette',
                          round(score, 1), weight, flags,
                          f'Genre match: {genre_match}')


def _score_layout(analysis, genre_profile, weight):
    """Score layout and composition."""
    flags = []
    score = 5.0

    if not analysis:
        return DimensionScore('layout_composition', 'Layout & Composition', 5.0, weight)

    layout = analysis.get('layout_style', 'centered')
    hierarchy = analysis.get('visual_hierarchy', 'balanced')
    expected_layouts = genre_profile['expected_layout']['patterns']
    expected_dominance = genre_profile['expected_layout']['title_dominance']

    # Layout match
    if layout in expected_layouts:
        score += 2.0
    else:
        score += 0.5
        flags.append(f'TIP: "{layout}" layout — {genre_profile["name"]} typically uses {", ".join(expected_layouts)}')

    # Visual hierarchy
    if expected_dominance == 'high' and hierarchy == 'title-dominant':
        score += 2.0
    elif expected_dominance == 'high' and hierarchy == 'image-dominant':
        score -= 1.0
        flags.append('WARNING: Image dominates over title — for this genre, title should be the focal point')
    elif expected_dominance == 'balanced' and hierarchy == 'balanced':
        score += 2.0
    else:
        score += 1.0

    score = max(0.0, min(10.0, score))
    return DimensionScore('layout_composition', 'Layout & Composition',
                          round(score, 1), weight, flags,
                          f'Layout: {layout}, Hierarchy: {hierarchy}')


def _score_genre_signal(analysis, genre_profile, weight):
    """Score how clearly the cover signals its genre."""
    flags = []
    score = 5.0

    if not analysis:
        return DimensionScore('genre_signal', 'Genre Signal', 5.0, weight)

    genre_match = analysis.get('genre_match', 'moderate')
    signals = analysis.get('genre_signals', [])

    match_scores = {'strong': 4.0, 'moderate': 1.5, 'weak': -1.5, 'mismatch': -4.0}
    score += match_scores.get(genre_match, 0)

    if genre_match in ('weak', 'mismatch'):
        flags.append(f'CRITICAL: Cover doesn\'t clearly signal "{genre_profile["name"]}" — readers browsing this category may skip it')
        expected_signals = genre_profile['genre_signals'][:3]
        flags.append(f'TIP: Consider adding: {", ".join(expected_signals)}')

    if len(signals) >= 3:
        score += 1.0

    score = max(0.0, min(10.0, score))
    return DimensionScore('genre_signal', 'Genre Signal',
                          round(score, 1), weight, flags,
                          f'Match: {genre_match}, Signals: {len(signals)} detected')


def _score_polish(analysis, weight):
    """Score professional polish."""
    flags = []

    if not analysis:
        return DimensionScore('professional_polish', 'Professional Polish', 5.0, weight)

    quality = analysis.get('professional_quality', 5)
    weaknesses = analysis.get('notable_weaknesses', [])

    score = float(quality)

    for weakness in weaknesses:
        w_lower = weakness.lower()
        if any(term in w_lower for term in ['amateur', 'cheap', 'low quality', 'blurry', 'pixelated']):
            score -= 1.0
            flags.append(f'WARNING: {weakness}')
        elif any(term in w_lower for term in ['misaligned', 'inconsistent', 'cluttered']):
            score -= 0.5
            flags.append(f'TIP: {weakness}')

    score = max(0.0, min(10.0, score))
    return DimensionScore('professional_polish', 'Professional Polish',
                          round(score, 1), weight, flags,
                          f'Quality: {quality}/10')


def _score_differentiation(analysis, comp_data, weight):
    """Score competitive differentiation — standing out from comps."""
    flags = []
    score = 6.0  # Slightly above average baseline

    if not analysis:
        return DimensionScore('competitive_differentiation', 'Differentiation', 6.0, weight)

    strengths = analysis.get('notable_strengths', [])
    if len(strengths) >= 2:
        score += 2.0
    elif len(strengths) >= 1:
        score += 1.0

    if comp_data and comp_data.get('covers'):
        # Compare quality against comps
        comp_qualities = [c.get('professional_quality', 5) for c in comp_data['covers']]
        avg_comp_quality = sum(comp_qualities) / len(comp_qualities) if comp_qualities else 5
        user_quality = analysis.get('professional_quality', 5)

        if user_quality > avg_comp_quality + 1:
            score += 1.5
            flags.append('TIP: Your cover quality exceeds most competitors — strong position')
        elif user_quality < avg_comp_quality - 1:
            score -= 1.5
            flags.append(f'WARNING: Your cover quality ({user_quality}/10) is below comp average ({avg_comp_quality:.1f}/10)')

    score = max(0.0, min(10.0, score))
    return DimensionScore('competitive_differentiation', 'Differentiation',
                          round(score, 1), weight, flags,
                          f'{len(strengths)} standout strengths')


def _get_grade(score):
    """Convert numeric score to letter grade."""
    for threshold, grade, desc in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade, desc
    return 'F', 'Not competitive'
