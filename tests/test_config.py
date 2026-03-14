"""Tests for configuration module."""

from cover_comp_analyzer.config import Config


class TestConfig:
    def test_scoring_weights_sum_to_one(self):
        total = sum(Config.SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_all_scoring_dimensions_present(self):
        expected = {
            'thumbnail_readability', 'title_typography', 'color_palette',
            'layout_composition', 'genre_signal', 'professional_polish',
            'competitive_differentiation',
        }
        assert set(Config.SCORING_WEIGHTS.keys()) == expected

    def test_thumbnail_sizes(self):
        assert Config.AMAZON_THUMBNAIL_WIDTH == 150
        assert Config.PREVIEW_THUMBNAIL_WIDTH == 300

    def test_default_max_comps(self):
        assert Config.DEFAULT_MAX_COMPS == 20

    def test_has_anthropic_key_method(self):
        # Should return bool regardless of key presence
        result = Config.has_anthropic_key()
        assert isinstance(result, bool)

    def test_setup_logging(self):
        # Should not raise
        Config.setup_logging()

    def test_model_default(self):
        assert 'claude' in Config.MODEL.lower() or Config.MODEL != ''
