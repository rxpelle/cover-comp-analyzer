"""Tests for report generation."""

import json
import os
import pytest

from cover_comp_analyzer.report import (
    print_scorecard, print_quick_check, save_json_report,
    _score_bar, _grade_color,
)
from cover_comp_analyzer.scorer import score_cover


class TestScoreBar:
    def test_high_score_green(self):
        bar = _score_bar(8)
        assert 'green' in bar

    def test_medium_score_yellow(self):
        bar = _score_bar(6)
        assert 'yellow' in bar

    def test_low_score_red(self):
        bar = _score_bar(3)
        assert 'red' in bar

    def test_bar_length(self):
        bar = _score_bar(7, width=10)
        assert '█' * 7 in bar
        assert '░' * 3 in bar


class TestGradeColor:
    def test_a_grade_green(self):
        assert _grade_color('A') == 'green'
        assert _grade_color('A-') == 'green'

    def test_b_grade_yellow(self):
        assert _grade_color('B') == 'yellow'
        assert _grade_color('B+') == 'yellow'
        assert _grade_color('B-') == 'yellow'

    def test_c_grade_red(self):
        assert _grade_color('C') == 'red'

    def test_d_grade_red(self):
        assert _grade_color('D') == 'red'


class TestPrintScorecard:
    def test_does_not_crash(self, sample_full_analysis, sample_thumbnail_analysis):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        # Should not raise
        print_scorecard(scorecard, cover_path='test.png', genre='Historical Fiction')

    def test_with_comp_summary(self, sample_full_analysis, sample_thumbnail_analysis, sample_comp_data):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis,
                                genre='historical', comp_data=sample_comp_data)
        print_scorecard(scorecard, genre='Historical Fiction')

    def test_with_flags(self, weak_full_analysis, weak_thumbnail_analysis):
        scorecard = score_cover(weak_full_analysis, weak_thumbnail_analysis, genre='thriller')
        # Should print flags without crashing
        print_scorecard(scorecard, genre='Thriller')


class TestPrintQuickCheck:
    def test_does_not_crash(self, sample_full_analysis, sample_thumbnail_analysis):
        print_quick_check(sample_full_analysis, sample_thumbnail_analysis, genre='Historical Fiction')

    def test_with_none_analysis(self):
        print_quick_check(None, None, genre='Thriller')

    def test_with_weaknesses(self, weak_full_analysis, weak_thumbnail_analysis):
        print_quick_check(weak_full_analysis, weak_thumbnail_analysis, genre='Thriller')


class TestSaveJsonReport:
    def test_creates_file(self, tmp_path, sample_full_analysis, sample_thumbnail_analysis):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        output_path = str(tmp_path / 'report.json')
        save_json_report(scorecard, sample_full_analysis, sample_thumbnail_analysis,
                         output_path, cover_path='test.png', genre='historical')
        assert os.path.exists(output_path)

    def test_valid_json(self, tmp_path, sample_full_analysis, sample_thumbnail_analysis):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        output_path = str(tmp_path / 'report.json')
        save_json_report(scorecard, sample_full_analysis, sample_thumbnail_analysis,
                         output_path, genre='historical')
        with open(output_path) as f:
            data = json.load(f)
        assert 'overall_score' in data
        assert 'grade' in data
        assert 'dimensions' in data

    def test_json_has_all_fields(self, tmp_path, sample_full_analysis, sample_thumbnail_analysis):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        output_path = str(tmp_path / 'report.json')
        save_json_report(scorecard, sample_full_analysis, sample_thumbnail_analysis,
                         output_path, genre='historical')
        with open(output_path) as f:
            data = json.load(f)
        assert 'generated_at' in data
        assert 'cover_path' in data
        assert 'genre' in data
        assert 'critical_flags' in data
        assert 'warning_flags' in data
        assert 'tip_flags' in data
        assert 'full_analysis' in data
        assert 'thumbnail_analysis' in data

    def test_includes_comp_data(self, tmp_path, sample_full_analysis,
                                sample_thumbnail_analysis, sample_comp_data):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis,
                                genre='historical', comp_data=sample_comp_data)
        output_path = str(tmp_path / 'report.json')
        save_json_report(scorecard, sample_full_analysis, sample_thumbnail_analysis,
                         output_path, genre='historical', comp_data=sample_comp_data)
        with open(output_path) as f:
            data = json.load(f)
        assert 'comp_details' in data

    def test_creates_directories(self, tmp_path, sample_full_analysis, sample_thumbnail_analysis):
        scorecard = score_cover(sample_full_analysis, sample_thumbnail_analysis, genre='historical')
        output_path = str(tmp_path / 'sub' / 'dir' / 'report.json')
        save_json_report(scorecard, sample_full_analysis, sample_thumbnail_analysis,
                         output_path, genre='historical')
        assert os.path.exists(output_path)
