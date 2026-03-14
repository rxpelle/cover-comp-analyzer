"""Report generation for cover analysis results.

Produces Rich terminal output, JSON export, and optional HTML reports.
"""

import json
import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


def print_scorecard(scorecard, cover_path='', genre=''):
    """Print a full scorecard to the terminal using Rich."""

    # Header
    console.print()
    header = f"[bold]Cover Analysis Report[/bold]"
    if cover_path:
        header += f"\n[dim]{cover_path}[/dim]"
    if genre:
        header += f"\n[dim]Genre: {genre}[/dim]"
    header += f"\n[dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]"
    console.print(Panel(header, title="Cover Comp Analyzer", border_style="cyan"))

    # Overall grade
    grade_color = _grade_color(scorecard.grade)
    console.print()
    console.print(Panel(
        f"[{grade_color} bold]{scorecard.grade}[/{grade_color} bold]  "
        f"[bold]{scorecard.overall_score}/10[/bold]\n"
        f"[dim]{scorecard.grade_description}[/dim]",
        title="Overall Score",
        border_style=grade_color,
    ))

    # Dimensional scores table
    table = Table(title="Dimensional Scores", show_header=True, header_style="bold")
    table.add_column("Dimension", style="cyan", min_width=24)
    table.add_column("Score", justify="center", min_width=8)
    table.add_column("Weight", justify="center", style="dim", min_width=8)
    table.add_column("Details", style="dim")

    for dim in scorecard.dimensions:
        bar = _score_bar(dim.score)
        score_text = f"{bar} {dim.score}"
        table.add_row(dim.display_name, score_text, f"{dim.weight:.0%}", dim.details)

    console.print()
    console.print(table)

    # Flags
    if scorecard.critical_flags:
        console.print()
        console.print(Panel(
            '\n'.join(f'[red bold]{f}[/red bold]' for f in scorecard.critical_flags),
            title="[red]Critical Issues[/red]",
            border_style="red",
        ))

    if scorecard.warning_flags:
        console.print()
        console.print(Panel(
            '\n'.join(f'[yellow]{f}[/yellow]' for f in scorecard.warning_flags),
            title="[yellow]Warnings[/yellow]",
            border_style="yellow",
        ))

    if scorecard.tip_flags:
        console.print()
        console.print(Panel(
            '\n'.join(f'[blue]{f}[/blue]' for f in scorecard.tip_flags),
            title="[blue]Tips[/blue]",
            border_style="blue",
        ))

    # Comp summary
    if scorecard.comp_summary:
        console.print()
        summary = scorecard.comp_summary
        comp_text = (
            f"Color scheme: {summary.get('dominant_color_scheme', 'N/A')}\n"
            f"Font weight: {summary.get('typical_font_weight', 'N/A')}\n"
            f"Layout: {summary.get('typical_layout', 'N/A')}\n"
            f"Background: {summary.get('typical_background', 'N/A')}\n"
            f"Average quality: {summary.get('average_quality', 'N/A')}/10"
        )
        console.print(Panel(comp_text, title="Category Trends (from comps)", border_style="green"))

    console.print()


def print_quick_check(full_analysis, thumbnail_analysis, genre=''):
    """Print a quick-check report (no comps, lighter output)."""
    console.print()
    console.print(Panel(
        f"[bold]Quick Cover Check[/bold]\n[dim]Genre: {genre}[/dim]",
        title="Cover Comp Analyzer",
        border_style="cyan",
    ))

    if full_analysis:
        title = full_analysis.get('title_text', 'unreadable')
        author = full_analysis.get('author_text', 'unreadable')
        quality = full_analysis.get('professional_quality', '?')
        genre_match = full_analysis.get('genre_match', '?')
        impression = full_analysis.get('overall_impression', '')

        console.print(f"\n[bold]Title:[/bold] {title}")
        console.print(f"[bold]Author:[/bold] {author}")
        console.print(f"[bold]Quality:[/bold] {quality}/10")
        console.print(f"[bold]Genre match:[/bold] {genre_match}")
        if impression:
            console.print(f"[bold]Impression:[/bold] {impression}")

        strengths = full_analysis.get('notable_strengths', [])
        if strengths:
            console.print("\n[green bold]Strengths:[/green bold]")
            for s in strengths:
                console.print(f"  [green]+[/green] {s}")

        weaknesses = full_analysis.get('notable_weaknesses', [])
        if weaknesses:
            console.print("\n[red bold]Weaknesses:[/red bold]")
            for w in weaknesses:
                console.print(f"  [red]-[/red] {w}")

    if thumbnail_analysis:
        console.print("\n[bold]Thumbnail Test (150px — Amazon search size):[/bold]")
        readable = thumbnail_analysis.get('title_readable', False)
        impact = thumbnail_analysis.get('thumbnail_impact', '?')
        genre_guess = thumbnail_analysis.get('genre_guess', '?')

        status = "[green]PASS[/green]" if readable else "[red]FAIL[/red]"
        console.print(f"  Title readable: {status}")
        console.print(f"  Thumbnail impact: {impact}/10")
        console.print(f"  Genre guess: {genre_guess}")

        issues = thumbnail_analysis.get('issues_at_thumbnail', [])
        if issues:
            for issue in issues:
                console.print(f"  [yellow]! {issue}[/yellow]")

    console.print()


def save_json_report(scorecard, full_analysis, thumbnail_analysis, output_path,
                     cover_path='', genre='', comp_data=None):
    """Save complete analysis as JSON for programmatic use."""
    report = {
        'generated_at': datetime.now().isoformat(),
        'cover_path': str(cover_path),
        'genre': genre,
        'overall_score': scorecard.overall_score,
        'grade': scorecard.grade,
        'grade_description': scorecard.grade_description,
        'dimensions': [
            {
                'name': d.name,
                'display_name': d.display_name,
                'score': d.score,
                'weight': d.weight,
                'details': d.details,
                'flags': d.flags,
            }
            for d in scorecard.dimensions
        ],
        'critical_flags': scorecard.critical_flags,
        'warning_flags': scorecard.warning_flags,
        'tip_flags': scorecard.tip_flags,
        'full_analysis': full_analysis,
        'thumbnail_analysis': thumbnail_analysis,
        'comp_summary': scorecard.comp_summary,
    }
    if comp_data:
        report['comp_details'] = comp_data

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return output_path


def _score_bar(score, width=10):
    """Create a visual bar for a score."""
    filled = int(score)
    empty = width - filled
    if score >= 7:
        color = 'green'
    elif score >= 5:
        color = 'yellow'
    else:
        color = 'red'
    return f'[{color}]{"█" * filled}{"░" * empty}[/{color}]'


def _grade_color(grade):
    """Get color for a letter grade."""
    if grade.startswith('A'):
        return 'green'
    elif grade.startswith('B'):
        return 'yellow'
    elif grade.startswith('C'):
        return 'red'
    return 'red'
