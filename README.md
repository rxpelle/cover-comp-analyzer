# Cover Comp Analyzer

Analyze your book cover against genre competitors using Claude Vision. Scores thumbnail readability, typography, color palette, layout, genre signaling, and professional polish — then tells you exactly what to fix.

## What It Does

- **Claude Vision analyzes your cover** — reads the title, evaluates typography, color, layout, and genre signals
- **Tests thumbnail readability** — simulates Amazon search results (150px wide) to check if your title is readable where the sale actually happens
- **Compares against competitors** — analyzes 10-20 top-selling covers in your category and shows where you stand
- **Scores 7 dimensions** — weighted scorecard with letter grade, specific flags (CRITICAL/WARNING/TIP), and actionable fixes
- **Exports JSON reports** — for programmatic use or feeding back into Cover Generator

## Quick Start

```bash
# Clone and install
git clone https://github.com/rxpelle/cover-comp-analyzer.git
cd cover-comp-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure API key
cp .env.example .env
# Edit .env with your Anthropic API key
```

## Commands

### Quick Check (no comps needed)

```bash
cover-comp-analyzer quick-check my-cover.png --genre historical
```

Analyzes your cover against genre conventions and tests thumbnail readability. Two API calls, instant feedback.

### Full Analysis (with competitor covers)

```bash
# Step 1: Download competitor covers
cover-comp-analyzer comps historical
# Opens Amazon bestseller page — save 10-20 covers to a folder

# Step 2: Analyze
cover-comp-analyzer analyze my-cover.png \
  --comps-dir comps/historical/ \
  --genre historical \
  --format all \
  --verbose
```

### List Genres

```bash
cover-comp-analyzer genres
```

## Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **Thumbnail Readability** | 25% | Can the title be read at Amazon search size (150px)? |
| **Title Typography** | 15% | Font weight, size, case, contrast vs. genre norms |
| **Color Palette** | 15% | Colors match genre conventions, sufficient contrast |
| **Layout & Composition** | 15% | Visual hierarchy, whitespace, element placement |
| **Genre Signal** | 15% | Does a reader know the genre in 2 seconds? |
| **Professional Polish** | 10% | Quality, consistency, no amateur tells |
| **Differentiation** | 5% | Stands out from comps while staying on-genre |

### Grading Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 9-10 | Competitive with top sellers |
| A- | 8-9 | Very strong — minor improvements possible |
| B+ | 7-8 | Good — a few areas need attention |
| B | 6-7 | Solid — several improvements recommended |
| B- | 5-6 | Adequate — meaningful changes needed |
| C | 4-5 | Below average — significant issues |
| D | 3-4 | Weak — major redesign recommended |
| F | 0-3 | Not competitive |

## Output Flags

The tool produces three severity levels:

- **CRITICAL** — Must fix. Title unreadable, genre mismatch, zero contrast.
- **WARNING** — Should fix. Wrong font weight, unusual colors, weak hierarchy.
- **TIP** — Nice to fix. Minor polish, small improvements, optimization.

## Options

| Option | Description |
|--------|-------------|
| `--genre, -g` | `thriller`, `historical`, `scifi`, `mystery`, `literary`, `romance`, `fantasy`, `horror` |
| `--comps-dir, -c` | Folder of competitor cover images |
| `--output, -o` | Output directory for reports |
| `--format, -f` | `terminal`, `json`, or `all` |
| `--max-comps, -m` | Max competitor covers to analyze (default: 20) |
| `--verbose` | Show per-comp analysis details |

## How to Get Competitor Covers

Amazon doesn't have a public API for cover images. The `comps` command opens the bestseller page for your genre — save 10-20 covers manually:

1. Run `cover-comp-analyzer comps <genre>`
2. Right-click each cover → "Save Image As..."
3. Save into a folder (e.g., `comps/historical/`)
4. Run the `analyze` command with `--comps-dir`

Focus on books in your specific subgenre for the most useful comparison.

## Integration with Cover Generator

This tool is designed as a quality gate for [Cover Generator](https://github.com/rxpelle/cover-generator). Generate covers → analyze them → iterate until the score passes your threshold.

```bash
# Generate covers
cover-generator ebook "The First Key" --genre historical --dalle --variants 3

# Analyze the best one
cover-comp-analyzer quick-check output/the-first-key-ebook-v1.png --genre historical

# Full comparison
cover-comp-analyzer analyze output/the-first-key-ebook-v1.png \
  -c comps/historical/ -g historical
```

## Cost

- **Quick check**: ~$0.02-0.05 (2 API calls)
- **Full analysis with 20 comps**: ~$0.30-0.50 (7-8 API calls)

## Configuration

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-...    # Required — Claude Vision analyzes covers
COVER_COMP_OUTPUT_DIR=./output
```

## Development

```bash
# Run tests
pytest tests/ -v

# Tests cover:
# - Genre profile validation
# - Image processing (load, thumbnail, color extraction, base64)
# - Analyzer (prompt construction, JSON parsing, batching)
# - Scoring engine (all 7 dimensions, grade thresholds, flags)
# - Report generation (terminal, JSON)
# - CLI commands
```

## Requirements

- Python 3.9+
- Anthropic API key (Claude with vision capabilities)

## License

MIT
