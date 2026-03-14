"""Configuration management for Cover Comp Analyzer."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv


_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / '.env')


class Config:
    """Central configuration for Cover Comp Analyzer."""

    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    MODEL = os.getenv('COVER_COMP_MODEL', 'claude-sonnet-4-20250514')

    # Output
    OUTPUT_DIR = os.getenv('COVER_COMP_OUTPUT_DIR', str(_project_root / 'output'))

    # Scoring weights (must sum to 1.0)
    SCORING_WEIGHTS = {
        'thumbnail_readability': 0.25,
        'title_typography': 0.15,
        'color_palette': 0.15,
        'layout_composition': 0.15,
        'genre_signal': 0.15,
        'professional_polish': 0.10,
        'competitive_differentiation': 0.05,
    }

    # Thumbnail sizes
    AMAZON_THUMBNAIL_WIDTH = 150  # What shoppers see in search
    PREVIEW_THUMBNAIL_WIDTH = 300  # Medium preview

    # Max comps to analyze (cost control)
    DEFAULT_MAX_COMPS = 20

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def has_anthropic_key(cls):
        return bool(cls.ANTHROPIC_API_KEY)

    @classmethod
    def setup_logging(cls):
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO),
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
