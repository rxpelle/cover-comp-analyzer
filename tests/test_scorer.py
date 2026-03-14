"""Tests for the scoring engine."""

import pytest
from cover_comp_analyzer.scorer import (
    score_cover, ScoreCard, DimensionScore, GRADE_THRESHOLDS,
    _score_thumbnail, _score_typography, _score_colors,
    _score_layout, _score_genre_signal, _score_polish,
    _score_differentiation, _get_grade,
)
from cover_comp_analyzer.config import Config


class TestScoreCover:
    def test_returns_scorecard(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        assert isinstance(result, ScoreCard)

    def test_scorecard_has_all_dimensions(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        assert len(result.dimensions) == 7
        dim_names = {d.name for d in result.dimensions}
        assert dim_names == set(Config.SCORING_WEIGHTS.keys())

    def test_overall_score_range(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        assert 0 <= result.overall_score <= 10

    def test_has_grade(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        assert result.grade in [g for _, g, _ in GRADE_THRESHOLDS]

    def test_strong_cover_scores_high(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        assert result.overall_score >= 6.0

    def test_weak_cover_scores_low(self, weak_full_analysis, weak_thumbnail_analysis):
        result = score_cover(weak_full_analysis, weak_thumbnail_analysis, genre='thriller')
        assert result.overall_score < 5.0

    def test_weak_cover_has_critical_flags(self, weak_full_analysis, weak_thumbnail_analysis):
        result = score_cover(weak_full_analysis, weak_thumbnail_analysis, genre='thriller')
        assert len(result.critical_flags) > 0

    def test_with_comp_data(self, sample_full_analysis, sample_thumbnail_analysis, sample_comp_data):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis,
                             genre='historical', comp_data=sample_comp_data)
        assert result.comp_summary

    def test_unknown_genre_falls_back(self, sample_full_analysis, sample_thumbnail_analysis):
        result = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='nonexistent')
        assert isinstance(result, ScoreCard)


class TestScoreThumbnail:
    def test_readable_title_scores_higher(self, sample_thumbnail_analysis):
        weight = 0.25
        good = _score_thumbnail(sample_thumbnail_analysis, weight)
        bad_thumb = {**sample_thumbnail_analysis, 'title_readable': False, 'thumbnail_impact': 2,
                     'grabs_attention': False, 'genre_identifiable': False}
        bad = _score_thumbnail(bad_thumb, weight)
        assert good.score > bad.score

    def test_none_analysis(self):
        result = _score_thumbnail(None, 0.25)
        assert result.score == 5.0
        assert any('unavailable' in f for f in result.flags)

    def test_issues_become_tips(self):
        thumb = {
            'title_readable': True, 'author_readable': True,
            'genre_identifiable': True, 'grabs_attention': True,
            'thumbnail_impact': 7,
            'issues_at_thumbnail': ['Font slightly thin'],
        }
        result = _score_thumbnail(thumb, 0.25)
        assert any('Font slightly thin' in f for f in result.flags)


class TestScoreTypography:
    def test_matching_weight_scores_higher(self, sample_full_analysis):
        from cover_comp_analyzer.genres import get_genre
        genre = get_genre('historical')
        weight = 0.15
        result = _score_typography(sample_full_analysis, genre, weight)
        assert result.score >= 5.0

    def test_mismatched_weight_flagged(self):
        from cover_comp_analyzer.genres import get_genre
        genre = get_genre('thriller')  # expects heavy
        analysis = {'title_font_weight': 'thin', 'title_case': 'lower',
                     'title_size_relative': 'small', 'title_contrast': 'low'}
        result = _score_typography(analysis, genre, 0.15)
        assert result.score < 5.0
        assert len(result.flags) > 0

    def test_none_analysis(self):
        from cover_comp_analyzer.genres import get_genre
        result = _score_typography(None, get_genre('thriller'), 0.15)
        assert result.score == 5.0


class TestScoreColors:
    def test_strong_match_scores_high(self, sample_full_analysis):
        from cover_comp_analyzer.genres import get_genre
        result = _score_colors(sample_full_analysis, get_genre('historical'), 0.15)
        assert result.score >= 7.0

    def test_avoided_colors_flagged(self):
        from cover_comp_analyzer.genres import get_genre
        genre = get_genre('thriller')
        analysis = {
            'genre_match': 'weak',
            'title_contrast': 'medium',
            'dominant_colors': [{'name': 'bright pink', 'area': 'background'}],
        }
        result = _score_colors(analysis, genre, 0.15)
        assert any('pink' in f.lower() for f in result.flags)


class TestScoreLayout:
    def test_matching_layout_scores_higher(self, sample_full_analysis):
        from cover_comp_analyzer.genres import get_genre
        result = _score_layout(sample_full_analysis, get_genre('historical'), 0.15)
        assert result.score >= 7.0

    def test_image_dominant_flagged_for_title_first_genre(self):
        from cover_comp_analyzer.genres import get_genre
        genre = get_genre('thriller')  # expects title_dominance: high
        analysis = {'layout_style': 'centered', 'visual_hierarchy': 'image-dominant'}
        result = _score_layout(analysis, genre, 0.15)
        assert any('Image dominates' in f for f in result.flags)


class TestScoreGenreSignal:
    def test_strong_match(self, sample_full_analysis):
        from cover_comp_analyzer.genres import get_genre
        result = _score_genre_signal(sample_full_analysis, get_genre('historical'), 0.15)
        assert result.score >= 7.0

    def test_mismatch_flagged(self, weak_full_analysis):
        from cover_comp_analyzer.genres import get_genre
        result = _score_genre_signal(weak_full_analysis, get_genre('thriller'), 0.15)
        assert result.score < 4.0
        assert any('CRITICAL' in f for f in result.flags)


class TestScorePolish:
    def test_high_quality(self, sample_full_analysis):
        result = _score_polish(sample_full_analysis, 0.10)
        assert result.score >= 7.0

    def test_low_quality_with_weaknesses(self, weak_full_analysis):
        result = _score_polish(weak_full_analysis, 0.10)
        assert result.score < 4.0


class TestScoreDifferentiation:
    def test_without_comps(self, sample_full_analysis):
        result = _score_differentiation(sample_full_analysis, None, 0.05)
        assert result.score >= 5.0

    def test_above_comp_average(self, sample_full_analysis):
        comp_data = {'covers': [{'professional_quality': 5}, {'professional_quality': 4}]}
        result = _score_differentiation(sample_full_analysis, comp_data, 0.05)
        assert any('exceeds' in f.lower() for f in result.flags)

    def test_below_comp_average(self, weak_full_analysis):
        comp_data = {'covers': [{'professional_quality': 8}, {'professional_quality': 9}]}
        result = _score_differentiation(weak_full_analysis, comp_data, 0.05)
        assert any('below' in f.lower() for f in result.flags)


class TestGetGrade:
    def test_grade_thresholds(self):
        assert _get_grade(9.5) == ('A', 'Excellent — competitive with top sellers')
        assert _get_grade(8.5)[0] == 'A-'
        assert _get_grade(7.5)[0] == 'B+'
        assert _get_grade(6.5)[0] == 'B'
        assert _get_grade(5.5)[0] == 'B-'
        assert _get_grade(4.5)[0] == 'C'
        assert _get_grade(3.5)[0] == 'D'
        assert _get_grade(1.0)[0] == 'F'

    def test_boundary_values(self):
        assert _get_grade(9.0)[0] == 'A'
        assert _get_grade(8.0)[0] == 'A-'
        assert _get_grade(0.0)[0] == 'F'
