"""Tests for genre profiles and scoring conventions."""

from cover_comp_analyzer.genres import GENRE_PROFILES, get_genre, list_genres


class TestGenreProfiles:
    def test_all_genres_present(self):
        expected = {'thriller', 'historical', 'scifi', 'mystery',
                    'literary', 'romance', 'fantasy', 'horror'}
        assert set(GENRE_PROFILES.keys()) == expected

    def test_genre_has_required_fields(self):
        required = {'name', 'expected_colors', 'expected_fonts',
                    'expected_layout', 'genre_signals', 'thumbnail_priority'}
        for key, profile in GENRE_PROFILES.items():
            for field in required:
                assert field in profile, f"Genre '{key}' missing '{field}'"

    def test_expected_colors_structure(self):
        for key, profile in GENRE_PROFILES.items():
            colors = profile['expected_colors']
            assert 'dominant' in colors, f"Genre '{key}' missing dominant colors"
            assert 'accent' in colors, f"Genre '{key}' missing accent colors"
            assert 'avoid' in colors, f"Genre '{key}' missing avoid colors"
            assert len(colors['dominant']) > 0
            assert len(colors['accent']) > 0
            assert len(colors['avoid']) > 0

    def test_expected_fonts_structure(self):
        for key, profile in GENRE_PROFILES.items():
            fonts = profile['expected_fonts']
            assert 'weight' in fonts
            assert 'case' in fonts
            assert 'style' in fonts
            assert fonts['weight'] in ('medium', 'heavy', 'medium-to-heavy')
            assert fonts['case'] in ('upper', 'title', 'lower')

    def test_expected_layout_structure(self):
        for key, profile in GENRE_PROFILES.items():
            layout = profile['expected_layout']
            assert 'patterns' in layout
            assert 'title_dominance' in layout
            assert 'imagery' in layout
            assert layout['title_dominance'] in ('high', 'balanced')

    def test_genre_signals_nonempty(self):
        for key, profile in GENRE_PROFILES.items():
            assert len(profile['genre_signals']) >= 3, \
                f"Genre '{key}' needs at least 3 genre signals"

    def test_amazon_category_urls_present(self):
        for key, profile in GENRE_PROFILES.items():
            urls = profile.get('amazon_category_urls', [])
            assert len(urls) >= 1, f"Genre '{key}' missing Amazon category URL"
            for url in urls:
                assert url.startswith('https://www.amazon.com/')


class TestGetGenre:
    def test_direct_match(self):
        profile = get_genre('thriller')
        assert profile is not None
        assert profile['name'] == 'Thriller / Suspense'

    def test_case_insensitive(self):
        profile = get_genre('THRILLER')
        assert profile is not None
        assert profile['name'] == 'Thriller / Suspense'

    def test_partial_match(self):
        profile = get_genre('sci')
        assert profile is not None
        assert profile['name'] == 'Science Fiction'

    def test_name_match(self):
        profile = get_genre('suspense')
        assert profile is not None
        assert profile['name'] == 'Thriller / Suspense'

    def test_unknown_genre(self):
        assert get_genre('cooking') is None

    def test_whitespace_handling(self):
        profile = get_genre('  historical  ')
        assert profile is not None


class TestListGenres:
    def test_returns_all_genres(self):
        genres = list_genres()
        assert len(genres) == 8

    def test_returns_tuples(self):
        genres = list_genres()
        for key, name in genres:
            assert isinstance(key, str)
            assert isinstance(name, str)
