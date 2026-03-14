"""Shared test fixtures for Cover Comp Analyzer."""

import json
import os
import pytest
from PIL import Image


@pytest.fixture
def sample_cover():
    """Create a simple test cover image (600x900, dark background with white text area)."""
    img = Image.new('RGB', (600, 900), (20, 15, 10))
    # Add some color variation
    pixels = img.load()
    for x in range(600):
        for y in range(100, 200):
            pixels[x, y] = (255, 255, 255)  # White band for title area
        for y in range(700, 750):
            pixels[x, y] = (200, 168, 78)  # Gold band for author area
    return img


@pytest.fixture
def sample_cover_path(sample_cover, tmp_path):
    """Save sample cover to a temp file and return path."""
    path = tmp_path / 'test_cover.png'
    sample_cover.save(str(path), 'PNG')
    return str(path)


@pytest.fixture
def comp_folder(tmp_path):
    """Create a folder with multiple sample comp images."""
    comp_dir = tmp_path / 'comps'
    comp_dir.mkdir()

    colors = [
        (10, 10, 10),   # Dark
        (20, 15, 25),   # Dark blue
        (15, 10, 10),   # Dark red tint
        (25, 20, 15),   # Dark brown
        (5, 10, 25),    # Navy
    ]
    for i, color in enumerate(colors):
        img = Image.new('RGB', (400, 640), color)
        img.save(str(comp_dir / f'comp_{i + 1:02d}.png'), 'PNG')

    return str(comp_dir)


@pytest.fixture
def sample_full_analysis():
    """Pre-built full analysis result for deterministic testing."""
    return {
        '_analysis_type': 'full',
        'title_text': 'THE FIRST KEY',
        'author_text': 'RANDY PELLEGRINI',
        'subtitle_text': None,
        'title_font_weight': 'heavy',
        'title_case': 'upper',
        'title_size_relative': 'dominant',
        'title_contrast': 'high',
        'dominant_colors': [
            {'name': 'black', 'hex': '#0a0a0a', 'area': 'background'},
            {'name': 'white', 'hex': '#ffffff', 'area': 'text'},
            {'name': 'gold', 'hex': '#c8a84e', 'area': 'accent'},
        ],
        'background_type': 'photographic',
        'background_mood': 'ancient mysterious',
        'layout_style': 'centered',
        'visual_hierarchy': 'title-dominant',
        'has_subtitle': False,
        'has_series_line': False,
        'has_decorative_elements': True,
        'genre_signals': ['period architecture', 'aged textures', 'warm earth tones'],
        'genre_match': 'strong',
        'professional_quality': 8,
        'notable_strengths': ['Bold readable title', 'Period-accurate imagery', 'Strong contrast'],
        'notable_weaknesses': ['No subtitle for series context'],
        'overall_impression': 'Professional historical fiction cover with strong genre signals.',
    }


@pytest.fixture
def sample_thumbnail_analysis():
    """Pre-built thumbnail analysis for deterministic testing."""
    return {
        '_analysis_type': 'thumbnail',
        'title_readable': True,
        'title_text_if_readable': 'THE FIRST KEY',
        'author_readable': True,
        'genre_identifiable': True,
        'genre_guess': 'historical fiction',
        'grabs_attention': True,
        'thumbnail_impact': 8,
        'issues_at_thumbnail': [],
    }


@pytest.fixture
def weak_full_analysis():
    """Analysis for a weak cover — used to test low-score paths."""
    return {
        '_analysis_type': 'full',
        'title_text': 'unreadable',
        'author_text': 'unreadable',
        'subtitle_text': None,
        'title_font_weight': 'thin',
        'title_case': 'mixed',
        'title_size_relative': 'small',
        'title_contrast': 'low',
        'dominant_colors': [
            {'name': 'bright pink', 'hex': '#ff69b4', 'area': 'background'},
        ],
        'background_type': 'gradient',
        'background_mood': 'cheerful',
        'layout_style': 'asymmetric',
        'visual_hierarchy': 'image-dominant',
        'has_subtitle': False,
        'has_series_line': False,
        'has_decorative_elements': False,
        'genre_signals': [],
        'genre_match': 'mismatch',
        'professional_quality': 3,
        'notable_strengths': [],
        'notable_weaknesses': ['Amateur design', 'Wrong genre signals', 'Unreadable text'],
        'overall_impression': 'Does not match genre conventions.',
    }


@pytest.fixture
def weak_thumbnail_analysis():
    """Thumbnail analysis for a weak cover."""
    return {
        '_analysis_type': 'thumbnail',
        'title_readable': False,
        'title_text_if_readable': None,
        'author_readable': False,
        'genre_identifiable': False,
        'genre_guess': 'romance',
        'grabs_attention': False,
        'thumbnail_impact': 2,
        'issues_at_thumbnail': ['Title completely illegible', 'Colors wash out'],
    }


@pytest.fixture
def sample_comp_data():
    """Pre-built comp analysis data."""
    return {
        'covers': [
            {
                'index': 1,
                'title_text': 'THE PILLARS OF THE EARTH',
                'title_font_weight': 'heavy',
                'title_case': 'upper',
                'title_size_relative': 'dominant',
                'title_contrast': 'high',
                'dominant_color_mood': 'dark/moody',
                'background_type': 'photographic',
                'layout_style': 'centered',
                'genre_match': 'strong',
                'professional_quality': 9,
                'standout_element': 'Massive bold title with cathedral imagery',
            },
            {
                'index': 2,
                'title_text': 'ALL THE LIGHT WE CANNOT SEE',
                'title_font_weight': 'medium',
                'title_case': 'title',
                'title_size_relative': 'large',
                'title_contrast': 'high',
                'dominant_color_mood': 'muted/elegant',
                'background_type': 'illustrated',
                'layout_style': 'centered',
                'genre_match': 'strong',
                'professional_quality': 8,
                'standout_element': 'Beautiful illustrated scene with elegant typography',
            },
        ],
        'category_trends': {
            'dominant_color_scheme': 'dark earth tones with gold/white text',
            'typical_font_weight': 'heavy',
            'typical_layout': 'centered',
            'typical_background': 'photographic',
            'average_quality': 7.5,
        },
        'comp_count': 2,
    }


@pytest.fixture
def fixtures_dir():
    """Path to the test fixtures directory."""
    return os.path.join(os.path.dirname(__file__), 'fixtures')
