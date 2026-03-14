"""Tests for image processing module."""

import os
import base64
import pytest
from PIL import Image

from cover_comp_analyzer.images import (
    load_image, make_thumbnail, image_to_base64, get_media_type,
    extract_dominant_colors, get_image_stats, load_comp_folder,
    SUPPORTED_EXTENSIONS,
)


class TestLoadImage:
    def test_load_png(self, sample_cover_path):
        img = load_image(sample_cover_path)
        assert isinstance(img, Image.Image)
        assert img.mode == 'RGB'

    def test_load_jpg(self, tmp_path):
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        path = tmp_path / 'test.jpg'
        img.save(str(path), 'JPEG')
        loaded = load_image(str(path))
        assert loaded.mode == 'RGB'

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_image('/nonexistent/path.png')

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / 'test.txt'
        path.write_text('not an image')
        with pytest.raises(ValueError, match='Unsupported'):
            load_image(str(path))

    def test_rgba_converted_to_rgb(self, tmp_path):
        img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
        path = tmp_path / 'rgba.png'
        img.save(str(path), 'PNG')
        loaded = load_image(str(path))
        assert loaded.mode == 'RGB'


class TestMakeThumbnail:
    def test_resize_maintains_ratio(self, sample_cover):
        thumb = make_thumbnail(sample_cover, width=150)
        assert thumb.width == 150
        expected_height = int(sample_cover.height * (150 / sample_cover.width))
        assert thumb.height == expected_height

    def test_various_widths(self, sample_cover):
        for width in [100, 150, 300, 400]:
            thumb = make_thumbnail(sample_cover, width=width)
            assert thumb.width == width

    def test_preserves_content(self, sample_cover):
        thumb = make_thumbnail(sample_cover, width=300)
        assert isinstance(thumb, Image.Image)
        assert thumb.mode == 'RGB'


class TestImageToBase64:
    def test_returns_valid_base64(self, sample_cover):
        b64 = image_to_base64(sample_cover)
        # Should be decodable
        decoded = base64.standard_b64decode(b64)
        assert len(decoded) > 0

    def test_png_format(self, sample_cover):
        b64 = image_to_base64(sample_cover, format='PNG')
        decoded = base64.standard_b64decode(b64)
        # PNG magic bytes
        assert decoded[:4] == b'\x89PNG'

    def test_jpeg_format(self, sample_cover):
        b64 = image_to_base64(sample_cover, format='JPEG')
        decoded = base64.standard_b64decode(b64)
        # JPEG magic bytes
        assert decoded[:2] == b'\xff\xd8'


class TestGetMediaType:
    def test_png(self):
        assert get_media_type('PNG') == 'image/png'

    def test_jpeg(self):
        assert get_media_type('JPEG') == 'image/jpeg'
        assert get_media_type('JPG') == 'image/jpeg'

    def test_webp(self):
        assert get_media_type('WEBP') == 'image/webp'

    def test_default(self):
        assert get_media_type('UNKNOWN') == 'image/png'


class TestExtractDominantColors:
    def test_returns_colors(self, sample_cover):
        colors = extract_dominant_colors(sample_cover, num_colors=5)
        assert len(colors) > 0
        assert len(colors) <= 5

    def test_color_structure(self, sample_cover):
        colors = extract_dominant_colors(sample_cover, num_colors=3)
        for color in colors:
            assert 'rgb' in color
            assert 'hex' in color
            assert 'percentage' in color
            assert len(color['rgb']) == 3
            assert color['hex'].startswith('#')
            assert 0 <= color['percentage'] <= 100

    def test_percentages_sum_roughly_100(self, sample_cover):
        colors = extract_dominant_colors(sample_cover, num_colors=5)
        total = sum(c['percentage'] for c in colors)
        assert 95 <= total <= 105  # Allow small rounding errors

    def test_solid_color_image(self):
        img = Image.new('RGB', (100, 100), (255, 0, 0))
        colors = extract_dominant_colors(img, num_colors=3)
        assert len(colors) >= 1
        # Dominant color should be red-ish
        top = colors[0]
        assert top['rgb'][0] > 200  # Red channel high

    def test_two_color_image(self):
        img = Image.new('RGB', (200, 100), (0, 0, 0))
        pixels = img.load()
        for x in range(100, 200):
            for y in range(100):
                pixels[x, y] = (255, 255, 255)
        colors = extract_dominant_colors(img, num_colors=2)
        assert len(colors) == 2


class TestGetImageStats:
    def test_dimensions(self, sample_cover):
        stats = get_image_stats(sample_cover)
        assert stats['width'] == 600
        assert stats['height'] == 900

    def test_aspect_ratio(self, sample_cover):
        stats = get_image_stats(sample_cover)
        assert abs(stats['aspect_ratio'] - 0.667) < 0.01

    def test_megapixels(self, sample_cover):
        stats = get_image_stats(sample_cover)
        assert stats['megapixels'] == 0.54


class TestLoadCompFolder:
    def test_loads_all_images(self, comp_folder):
        images = load_comp_folder(comp_folder)
        assert len(images) == 5

    def test_returns_tuples(self, comp_folder):
        images = load_comp_folder(comp_folder)
        for name, img in images:
            assert isinstance(name, str)
            assert isinstance(img, Image.Image)

    def test_sorted_by_name(self, comp_folder):
        images = load_comp_folder(comp_folder)
        names = [name for name, _ in images]
        assert names == sorted(names)

    def test_max_images(self, comp_folder):
        images = load_comp_folder(comp_folder, max_images=3)
        assert len(images) == 3

    def test_skips_non_images(self, tmp_path):
        comp_dir = tmp_path / 'mixed'
        comp_dir.mkdir()
        # Image
        Image.new('RGB', (100, 100)).save(str(comp_dir / 'cover.png'))
        # Non-image
        (comp_dir / 'notes.txt').write_text('not an image')
        images = load_comp_folder(str(comp_dir))
        assert len(images) == 1

    def test_skips_hidden_files(self, tmp_path):
        comp_dir = tmp_path / 'hidden'
        comp_dir.mkdir()
        Image.new('RGB', (100, 100)).save(str(comp_dir / '.hidden.png'))
        Image.new('RGB', (100, 100)).save(str(comp_dir / 'visible.png'))
        images = load_comp_folder(str(comp_dir))
        assert len(images) == 1
        assert images[0][0] == 'visible.png'

    def test_not_a_directory(self, tmp_path):
        path = tmp_path / 'file.txt'
        path.write_text('test')
        with pytest.raises(NotADirectoryError):
            load_comp_folder(str(path))

    def test_empty_folder(self, tmp_path):
        comp_dir = tmp_path / 'empty'
        comp_dir.mkdir()
        images = load_comp_folder(str(comp_dir))
        assert len(images) == 0


class TestSupportedExtensions:
    def test_common_formats(self):
        assert '.png' in SUPPORTED_EXTENSIONS
        assert '.jpg' in SUPPORTED_EXTENSIONS
        assert '.jpeg' in SUPPORTED_EXTENSIONS
        assert '.webp' in SUPPORTED_EXTENSIONS
