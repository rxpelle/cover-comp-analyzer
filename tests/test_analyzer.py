"""Tests for the Claude Vision analyzer module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from cover_comp_analyzer.analyzer import (
    analyze_cover, analyze_thumbnail, analyze_comps_batch,
    _call_claude_vision, _merge_trends,
    FULL_ANALYSIS_PROMPT, THUMBNAIL_PROMPT, BATCH_COMP_PROMPT,
)


class TestPrompts:
    def test_full_analysis_prompt_has_genre_placeholder(self):
        assert '{genre}' in FULL_ANALYSIS_PROMPT

    def test_thumbnail_prompt_is_complete(self):
        assert 'thumbnail' in THUMBNAIL_PROMPT.lower()
        assert 'title_readable' in THUMBNAIL_PROMPT

    def test_batch_comp_prompt_has_placeholders(self):
        assert '{count}' in BATCH_COMP_PROMPT
        assert '{genre}' in BATCH_COMP_PROMPT


class TestCallClaudeVision:
    @patch('cover_comp_analyzer.analyzer.Config')
    def test_returns_none_without_api_key(self, mock_config):
        mock_config.has_anthropic_key.return_value = False
        img = Image.new('RGB', (100, 100))
        result = _call_claude_vision([('test', img)], 'test prompt')
        assert result is None

    @patch('cover_comp_analyzer.analyzer.Anthropic')
    @patch('cover_comp_analyzer.analyzer.Config')
    def test_parses_json_response(self, mock_config, mock_anthropic):
        mock_config.has_anthropic_key.return_value = True
        mock_config.ANTHROPIC_API_KEY = 'test-key'
        mock_config.MODEL = 'claude-sonnet-4-20250514'

        expected = {'title_text': 'TEST', 'quality': 8}
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(expected))]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        img = Image.new('RGB', (100, 100))
        result = _call_claude_vision([('test', img)], 'test prompt')
        assert result == expected

    @patch('cover_comp_analyzer.analyzer.Anthropic')
    @patch('cover_comp_analyzer.analyzer.Config')
    def test_strips_markdown_fences(self, mock_config, mock_anthropic):
        mock_config.has_anthropic_key.return_value = True
        mock_config.ANTHROPIC_API_KEY = 'test-key'
        mock_config.MODEL = 'claude-sonnet-4-20250514'

        expected = {'title_text': 'TEST'}
        fenced = f'```json\n{json.dumps(expected)}\n```'
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=fenced)]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        img = Image.new('RGB', (100, 100))
        result = _call_claude_vision([('test', img)], 'test prompt')
        assert result == expected

    @patch('cover_comp_analyzer.analyzer.Anthropic')
    @patch('cover_comp_analyzer.analyzer.Config')
    def test_handles_invalid_json(self, mock_config, mock_anthropic):
        mock_config.has_anthropic_key.return_value = True
        mock_config.ANTHROPIC_API_KEY = 'test-key'
        mock_config.MODEL = 'claude-sonnet-4-20250514'

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='not valid json at all')]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        img = Image.new('RGB', (100, 100))
        result = _call_claude_vision([('test', img)], 'test prompt')
        assert result is None

    @patch('cover_comp_analyzer.analyzer.Anthropic')
    @patch('cover_comp_analyzer.analyzer.Config')
    def test_sends_multiple_images(self, mock_config, mock_anthropic):
        mock_config.has_anthropic_key.return_value = True
        mock_config.ANTHROPIC_API_KEY = 'test-key'
        mock_config.MODEL = 'claude-sonnet-4-20250514'

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"covers": []}')]
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = mock_response

        images = [(f'Cover {i}', Image.new('RGB', (100, 100))) for i in range(3)]
        _call_claude_vision(images, 'test prompt')

        # Verify the message was constructed with all images
        call_args = mock_client.messages.create.call_args
        content = call_args[1]['messages'][0]['content']
        # Should have 3 images + 3 labels + 1 prompt = 7 content blocks
        assert len(content) == 7


class TestAnalyzeCover:
    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_returns_analysis_with_type(self, mock_call):
        mock_call.return_value = {'title_text': 'TEST', 'quality': 8}
        img = Image.new('RGB', (100, 100))
        result = analyze_cover(img, genre='thriller')
        assert result['_analysis_type'] == 'full'
        assert result['title_text'] == 'TEST'

    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_returns_none_on_failure(self, mock_call):
        mock_call.return_value = None
        img = Image.new('RGB', (100, 100))
        result = analyze_cover(img, genre='thriller')
        assert result is None


class TestAnalyzeThumbnail:
    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_returns_thumbnail_analysis(self, mock_call):
        mock_call.return_value = {'title_readable': True, 'thumbnail_impact': 7}
        img = Image.new('RGB', (600, 900))
        result = analyze_thumbnail(img, genre='thriller')
        assert result['_analysis_type'] == 'thumbnail'

    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_thumbnail_is_resized(self, mock_call):
        mock_call.return_value = {'title_readable': True}
        img = Image.new('RGB', (1600, 2560))
        analyze_thumbnail(img, genre='thriller')
        # Verify the image passed to Claude is the thumbnail, not full size
        call_args = mock_call.call_args
        images = call_args[0][0]
        label, thumb_img = images[0]
        assert thumb_img.width == 150  # AMAZON_THUMBNAIL_WIDTH


class TestAnalyzeCompsBatch:
    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_batches_correctly(self, mock_call):
        mock_call.return_value = {
            'covers': [{'index': 1, 'professional_quality': 7}],
            'category_trends': {'average_quality': 7},
        }
        images = [(f'comp_{i}.png', Image.new('RGB', (100, 100))) for i in range(6)]
        result = analyze_comps_batch(images, genre='thriller', batch_size=4)

        # 6 images with batch_size 4 = 2 API calls
        assert mock_call.call_count == 2
        assert 'covers' in result
        assert 'category_trends' in result
        assert 'comp_count' in result

    @patch('cover_comp_analyzer.analyzer._call_claude_vision')
    def test_handles_empty_batch(self, mock_call):
        result = analyze_comps_batch([], genre='thriller')
        assert result['comp_count'] == 0
        assert mock_call.call_count == 0


class TestMergeTrends:
    def test_single_trend(self):
        trends = [{'average_quality': 7.5, 'dominant_color_scheme': 'dark'}]
        result = _merge_trends(trends)
        assert result['average_quality'] == 7.5

    def test_multiple_trends_averaged(self):
        trends = [
            {'average_quality': 7, 'dominant_color_scheme': 'dark',
             'typical_font_weight': 'bold', 'typical_layout': 'centered',
             'typical_background': 'photographic'},
            {'average_quality': 9, 'dominant_color_scheme': 'dark',
             'typical_font_weight': 'heavy', 'typical_layout': 'centered',
             'typical_background': 'illustrated'},
        ]
        result = _merge_trends(trends)
        assert result['average_quality'] == 8.0
