"""Genre-specific scoring conventions for book cover analysis.

Each genre defines what readers expect: color palettes, font weights,
layout patterns, and visual signals. These conventions drive the scoring
engine — a thriller cover that looks like a romance will score poorly
on genre signal regardless of technical quality.
"""


GENRE_PROFILES = {
    'thriller': {
        'name': 'Thriller / Suspense',
        'expected_colors': {
            'dominant': ['black', 'dark blue', 'dark red', 'charcoal'],
            'accent': ['red', 'gold', 'white', 'silver'],
            'avoid': ['pink', 'pastel', 'bright yellow', 'light green'],
        },
        'expected_fonts': {
            'weight': 'heavy',
            'case': 'upper',
            'style': ['bold sans-serif', 'impact', 'condensed bold'],
        },
        'expected_layout': {
            'patterns': ['centered', 'top-heavy'],
            'title_dominance': 'high',  # title should be largest element
            'imagery': ['dark atmospheric', 'silhouette', 'urban', 'isolated figure'],
        },
        'genre_signals': [
            'dark/moody atmosphere', 'high contrast', 'bold typography',
            'suspenseful imagery', 'noir lighting', 'blood red accents',
        ],
        'thumbnail_priority': 'title_first',  # title must dominate at thumbnail
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-thrillers/zgbs/books/10484',
            'https://www.amazon.com/best-sellers-books-suspense/zgbs/books/10483',
        ],
    },
    'historical': {
        'name': 'Historical Fiction',
        'expected_colors': {
            'dominant': ['dark brown', 'sepia', 'black', 'dark gold'],
            'accent': ['gold', 'cream', 'white', 'burgundy', 'bronze'],
            'avoid': ['neon', 'bright pink', 'electric blue'],
        },
        'expected_fonts': {
            'weight': 'medium-to-heavy',
            'case': 'upper',
            'style': ['serif', 'classic serif', 'antiqued'],
        },
        'expected_layout': {
            'patterns': ['centered', 'bottom-heavy'],
            'title_dominance': 'high',
            'imagery': ['period architecture', 'landscapes', 'artifacts', 'atmospheric scenes'],
        },
        'genre_signals': [
            'period-appropriate imagery', 'aged/antiqued feel', 'warm earth tones',
            'architectural elements', 'historical setting visible', 'painterly quality',
        ],
        'thumbnail_priority': 'title_first',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-historical-fiction/zgbs/books/10177',
        ],
    },
    'scifi': {
        'name': 'Science Fiction',
        'expected_colors': {
            'dominant': ['black', 'dark blue', 'deep purple', 'dark teal'],
            'accent': ['cyan', 'electric blue', 'white', 'orange', 'green glow'],
            'avoid': ['warm brown', 'pastel pink', 'earth tones'],
        },
        'expected_fonts': {
            'weight': 'heavy',
            'case': 'upper',
            'style': ['bold sans-serif', 'futuristic', 'clean geometric'],
        },
        'expected_layout': {
            'patterns': ['centered', 'top-heavy'],
            'title_dominance': 'high',
            'imagery': ['space', 'technology', 'cosmic', 'futuristic landscape'],
        },
        'genre_signals': [
            'futuristic elements', 'cosmic/space imagery', 'technology',
            'cool color temperature', 'dramatic lighting', 'sleek design',
        ],
        'thumbnail_priority': 'title_first',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-science-fiction/zgbs/books/16190',
        ],
    },
    'mystery': {
        'name': 'Mystery / Crime',
        'expected_colors': {
            'dominant': ['dark gray', 'black', 'navy', 'dark green'],
            'accent': ['red', 'gold', 'white', 'yellow'],
            'avoid': ['bright pink', 'pastel', 'warm orange'],
        },
        'expected_fonts': {
            'weight': 'heavy',
            'case': 'upper',
            'style': ['bold serif', 'bold sans-serif', 'high contrast'],
        },
        'expected_layout': {
            'patterns': ['centered'],
            'title_dominance': 'high',
            'imagery': ['fog', 'shadows', 'silhouette', 'night scene', 'rain'],
        },
        'genre_signals': [
            'mysterious atmosphere', 'shadows and fog', 'noir aesthetic',
            'hidden elements', 'moody lighting', 'crime scene hints',
        ],
        'thumbnail_priority': 'title_first',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-mystery/zgbs/books/10457',
        ],
    },
    'literary': {
        'name': 'Literary Fiction',
        'expected_colors': {
            'dominant': ['muted tones', 'off-white', 'cream', 'soft gray', 'dusty blue'],
            'accent': ['subtle warm', 'muted red', 'ochre', 'forest green'],
            'avoid': ['neon', 'high saturation', 'garish combinations'],
        },
        'expected_fonts': {
            'weight': 'medium',
            'case': 'title',
            'style': ['elegant serif', 'classic', 'refined'],
        },
        'expected_layout': {
            'patterns': ['centered', 'minimalist'],
            'title_dominance': 'balanced',
            'imagery': ['abstract', 'minimalist', 'artistic', 'symbolic'],
        },
        'genre_signals': [
            'minimalist design', 'elegant typography', 'muted palette',
            'artistic composition', 'restrained aesthetic', 'symbolic imagery',
        ],
        'thumbnail_priority': 'balanced',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-literary-fiction/zgbs/books/10177',
        ],
    },
    'romance': {
        'name': 'Romance',
        'expected_colors': {
            'dominant': ['warm tones', 'dark jewel tones', 'deep pink', 'rich purple'],
            'accent': ['gold', 'pink', 'red', 'warm white'],
            'avoid': ['cold blue', 'gray', 'industrial colors'],
        },
        'expected_fonts': {
            'weight': 'medium',
            'case': 'title',
            'style': ['script', 'elegant serif', 'flowing'],
        },
        'expected_layout': {
            'patterns': ['centered', 'bottom-heavy'],
            'title_dominance': 'balanced',
            'imagery': ['couple', 'intimate', 'warm lighting', 'scenic', 'flowers'],
        },
        'genre_signals': [
            'warm atmosphere', 'intimate mood', 'romantic imagery',
            'soft focus elements', 'warm color temperature', 'emotional tone',
        ],
        'thumbnail_priority': 'balanced',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-romance/zgbs/books/23',
        ],
    },
    'fantasy': {
        'name': 'Fantasy',
        'expected_colors': {
            'dominant': ['deep purple', 'dark green', 'dark blue', 'black'],
            'accent': ['gold', 'silver', 'emerald', 'magical glow'],
            'avoid': ['pastel', 'corporate blue', 'plain gray'],
        },
        'expected_fonts': {
            'weight': 'heavy',
            'case': 'upper',
            'style': ['bold serif', 'ornamental', 'epic'],
        },
        'expected_layout': {
            'patterns': ['centered', 'top-heavy'],
            'title_dominance': 'high',
            'imagery': ['epic landscape', 'magical elements', 'mythical creatures', 'ancient'],
        },
        'genre_signals': [
            'magical atmosphere', 'epic scale', 'mythical elements',
            'rich detail', 'world-building hints', 'ornamental design',
        ],
        'thumbnail_priority': 'title_first',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-fantasy/zgbs/books/16190',
        ],
    },
    'horror': {
        'name': 'Horror',
        'expected_colors': {
            'dominant': ['black', 'very dark red', 'dark gray'],
            'accent': ['blood red', 'white', 'sickly green', 'bone'],
            'avoid': ['bright', 'cheerful', 'warm pastels'],
        },
        'expected_fonts': {
            'weight': 'heavy',
            'case': 'upper',
            'style': ['bold sans-serif', 'distressed', 'stark'],
        },
        'expected_layout': {
            'patterns': ['centered'],
            'title_dominance': 'high',
            'imagery': ['darkness', 'decay', 'isolation', 'dread', 'distortion'],
        },
        'genre_signals': [
            'dread atmosphere', 'deep shadows', 'unsettling elements',
            'isolation', 'decay imagery', 'stark contrast',
        ],
        'thumbnail_priority': 'title_first',
        'amazon_category_urls': [
            'https://www.amazon.com/best-sellers-books-horror/zgbs/books/49',
        ],
    },
}


def get_genre(name):
    """Get genre profile by name (case-insensitive, partial match)."""
    name_lower = name.lower().strip()
    if name_lower in GENRE_PROFILES:
        return GENRE_PROFILES[name_lower]
    for key, profile in GENRE_PROFILES.items():
        if name_lower in key or name_lower in profile['name'].lower():
            return profile
    return None


def list_genres():
    """Return list of available genre names."""
    return [(k, v['name']) for k, v in GENRE_PROFILES.items()]
