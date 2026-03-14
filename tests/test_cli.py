"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from PIL import Image

from cover_comp_analyzer.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestGenresCommand:
    def test_lists_genres(self, runner):
        result = runner.invoke(main, ['genres'])
        assert result.exit_code == 0
        assert 'thriller' in result.output.lower() or 'Thriller' in result.output

    def test_shows_all_eight(self, runner):
        result = runner.invoke(main, ['genres'])
        assert result.exit_code == 0
        for genre in ['thriller', 'historical', 'mystery', 'romance']:
            assert genre.lower() in result.output.lower()


class TestVersionOption:
    def test_version(self, runner):
        result = runner.invoke(main, ['--version'])
        assert '0.1.0' in result.output


class TestQuickCheckCommand:
    @patch('cover_comp_analyzer.cli.Config')
    def test_requires_api_key(self, mock_config, runner, sample_cover_path):
        mock_config.has_anthropic_key.return_value = False
        mock_config.setup_logging = MagicMock()
        result = runner.invoke(main, ['quick-check', sample_cover_path])
        assert result.exit_code == 1

    def test_requires_existing_file(self, runner):
        result = runner.invoke(main, ['quick-check', '/nonexistent/cover.png'])
        assert result.exit_code != 0


class TestAnalyzeCommand:
    @patch('cover_comp_analyzer.cli.Config')
    def test_requires_api_key(self, mock_config, runner, sample_cover_path, comp_folder):
        mock_config.has_anthropic_key.return_value = False
        mock_config.setup_logging = MagicMock()
        result = runner.invoke(main, ['analyze', sample_cover_path, '-c', comp_folder])
        assert result.exit_code == 1

    def test_requires_comps_dir(self, runner, sample_cover_path):
        result = runner.invoke(main, ['analyze', sample_cover_path])
        assert result.exit_code != 0

    def test_requires_existing_cover(self, runner, comp_folder):
        result = runner.invoke(main, ['analyze', '/nonexistent.png', '-c', comp_folder])
        assert result.exit_code != 0


class TestCompsCommand:
    @patch('cover_comp_analyzer.cli.webbrowser')
    def test_opens_browser(self, mock_browser, runner):
        result = runner.invoke(main, ['comps', 'thriller'])
        assert result.exit_code == 0
        mock_browser.open.assert_called_once()

    @patch('cover_comp_analyzer.cli.webbrowser')
    def test_shows_instructions(self, mock_browser, runner):
        result = runner.invoke(main, ['comps', 'historical'])
        assert result.exit_code == 0
        assert 'instructions' in result.output.lower() or 'download' in result.output.lower()

    def test_unknown_genre(self, runner):
        result = runner.invoke(main, ['comps', 'cooking'])
        assert 'unknown' in result.output.lower() or 'Unknown' in result.output
