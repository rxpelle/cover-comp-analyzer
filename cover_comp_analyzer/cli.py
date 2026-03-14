"""CLI interface for Cover Comp Analyzer."""

import os
import webbrowser
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import Config
from .genres import list_genres, get_genre
from .images import load_image, load_comp_folder, get_image_stats
from .analyzer import analyze_cover, analyze_thumbnail, analyze_comps_batch
from .scorer import score_cover
from .report import print_scorecard, print_quick_check, save_json_report

console = Console()


@click.group()
@click.version_option(version='0.1.0')
def main():
    """Analyze your book cover against genre competitors using AI vision."""
    Config.setup_logging()


@main.command()
@click.argument('cover', type=click.Path(exists=True))
@click.option('--comps-dir', '-c', type=click.Path(exists=True), required=True,
              help='Folder of competitor cover images')
@click.option('--genre', '-g', default='thriller', help='Genre for conventions')
@click.option('--output', '-o', default='', help='Output directory for reports')
@click.option('--format', '-f', 'fmt', default='terminal',
              type=click.Choice(['terminal', 'json', 'all']),
              help='Output format')
@click.option('--max-comps', '-m', default=20, type=int, help='Max competitor covers to analyze')
@click.option('--verbose', is_flag=True, help='Show detailed per-comp analysis')
def analyze(cover, comps_dir, genre, output, fmt, max_comps, verbose):
    """Analyze your cover against competitor covers.

    COVER is the path to your book cover image (PNG, JPG, etc).
    """
    if not Config.has_anthropic_key():
        console.print("[red]Error: ANTHROPIC_API_KEY not set. Add it to .env or environment.[/red]")
        raise SystemExit(1)

    output_dir = output or Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    genre_profile = get_genre(genre)
    genre_name = genre_profile['name'] if genre_profile else genre

    # Load images
    console.print(Panel.fit(
        f"[bold]Analyzing cover[/bold]\n"
        f"Cover: {cover}\n"
        f"Comps: {comps_dir}\n"
        f"Genre: {genre_name}",
        title="Cover Comp Analyzer",
    ))

    console.print("\n[dim]Loading your cover...[/dim]")
    img = load_image(cover)
    stats = get_image_stats(img)
    console.print(f"[dim]  {stats['width']}x{stats['height']}px ({stats['megapixels']}MP)[/dim]")

    console.print("[dim]Loading competitor covers...[/dim]")
    comps = load_comp_folder(comps_dir, max_images=max_comps)
    console.print(f"[dim]  {len(comps)} covers loaded[/dim]")

    if not comps:
        console.print("[yellow]Warning: No competitor covers found. Running without comps.[/yellow]")

    # Analyze user cover
    console.print("\n[dim]Analyzing your cover (full size)...[/dim]")
    full_analysis = analyze_cover(img, genre=genre)
    if full_analysis:
        console.print("[green]  Full analysis complete[/green]")
    else:
        console.print("[red]  Full analysis failed[/red]")

    console.print("[dim]Analyzing your cover (thumbnail size)...[/dim]")
    thumb_analysis = analyze_thumbnail(img, genre=genre)
    if thumb_analysis:
        console.print("[green]  Thumbnail analysis complete[/green]")
    else:
        console.print("[red]  Thumbnail analysis failed[/red]")

    # Analyze comps
    comp_data = None
    if comps:
        console.print(f"\n[dim]Analyzing {len(comps)} competitor covers...[/dim]")
        comp_data = analyze_comps_batch(comps, genre=genre)
        console.print(f"[green]  {comp_data['comp_count']} comps analyzed[/green]")

        if verbose and comp_data.get('covers'):
            table = Table(title="Competitor Analysis", show_header=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", min_width=20)
            table.add_column("Quality", justify="center", width=8)
            table.add_column("Genre", justify="center", width=8)
            table.add_column("Standout")

            for c in comp_data['covers']:
                table.add_row(
                    str(c.get('index', '?')),
                    c.get('title_text', '?')[:30],
                    str(c.get('professional_quality', '?')),
                    c.get('genre_match', '?'),
                    c.get('standout_element', '')[:40],
                )
            console.print()
            console.print(table)

    # Score
    scorecard = score_cover(full_analysis, thumb_analysis, genre=genre, comp_data=comp_data)

    # Output
    if fmt in ('terminal', 'all'):
        print_scorecard(scorecard, cover_path=cover, genre=genre_name)

    if fmt in ('json', 'all'):
        slug = os.path.splitext(os.path.basename(cover))[0]
        json_path = os.path.join(output_dir, f'{slug}-analysis.json')
        save_json_report(scorecard, full_analysis, thumb_analysis, json_path,
                         cover_path=cover, genre=genre, comp_data=comp_data)
        console.print(f"[green]JSON report saved:[/green] {json_path}")


@main.command('quick-check')
@click.argument('cover', type=click.Path(exists=True))
@click.option('--genre', '-g', default='thriller', help='Genre for conventions')
@click.option('--output', '-o', default='', help='Output directory for JSON report')
def quick_check(cover, genre, output):
    """Quick single-cover check — no comps needed.

    Analyzes your cover against genre conventions and tests thumbnail readability.
    One cover, two API calls, instant feedback.
    """
    if not Config.has_anthropic_key():
        console.print("[red]Error: ANTHROPIC_API_KEY not set. Add it to .env or environment.[/red]")
        raise SystemExit(1)

    genre_profile = get_genre(genre)
    genre_name = genre_profile['name'] if genre_profile else genre

    console.print(f"\n[dim]Loading {cover}...[/dim]")
    img = load_image(cover)

    console.print("[dim]Analyzing cover...[/dim]")
    full_analysis = analyze_cover(img, genre=genre)

    console.print("[dim]Testing thumbnail readability...[/dim]")
    thumb_analysis = analyze_thumbnail(img, genre=genre)

    print_quick_check(full_analysis, thumb_analysis, genre=genre_name)

    # Optionally save JSON
    if output:
        os.makedirs(output, exist_ok=True)
        scorecard = score_cover(full_analysis, thumb_analysis, genre=genre)
        slug = os.path.splitext(os.path.basename(cover))[0]
        json_path = os.path.join(output, f'{slug}-quick-check.json')
        save_json_report(scorecard, full_analysis, thumb_analysis, json_path,
                         cover_path=cover, genre=genre)
        console.print(f"[green]JSON report saved:[/green] {json_path}")


@main.command()
@click.argument('genre', default='thriller')
def comps(genre):
    """Open Amazon bestseller page for a genre to download comp covers.

    Downloads 10-20 top covers from the bestseller page into a folder,
    then use that folder with the 'analyze' command.
    """
    genre_profile = get_genre(genre)
    if not genre_profile:
        console.print(f"[red]Unknown genre: {genre}[/red]")
        console.print("Run 'cover-comp-analyzer genres' to see available genres.")
        return

    urls = genre_profile.get('amazon_category_urls', [])
    genre_name = genre_profile['name']

    console.print(Panel(
        f"[bold]Download Competitor Covers[/bold]\n\n"
        f"Genre: {genre_name}\n\n"
        f"[bold]Instructions:[/bold]\n"
        f"1. The Amazon bestseller page will open in your browser\n"
        f"2. Right-click each cover image → 'Save Image As...'\n"
        f"3. Save 10-20 covers into a folder (e.g., comps/{genre}/)\n"
        f"4. Run: cover-comp-analyzer analyze your-cover.png -c comps/{genre}/ -g {genre}\n\n"
        f"[dim]Tip: Focus on books in your specific subgenre for the most useful comparison.[/dim]",
        title="Cover Comp Analyzer",
        border_style="cyan",
    ))

    if urls:
        console.print(f"\n[dim]Opening {urls[0]}...[/dim]")
        webbrowser.open(urls[0])

        if len(urls) > 1:
            console.print("\n[bold]Additional category URLs:[/bold]")
            for url in urls[1:]:
                console.print(f"  {url}")
    else:
        console.print(f"\n[yellow]No Amazon URL configured for {genre_name}.[/yellow]")
        console.print("Search Amazon for bestsellers in your category manually.")


@main.command('genres')
def show_genres():
    """List available genre profiles and their conventions."""
    table = Table(title="Available Genre Profiles")
    table.add_column("Key", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Font Style")
    table.add_column("Expected Colors")
    table.add_column("Thumbnail Priority")

    for key, name in list_genres():
        profile = get_genre(key)
        font_style = f"{profile['expected_fonts']['weight']} / {profile['expected_fonts']['case']}"
        colors = ', '.join(profile['expected_colors']['accent'][:3])
        thumb = profile.get('thumbnail_priority', 'title_first')
        table.add_row(key, name, font_style, colors, thumb)

    console.print(table)


if __name__ == '__main__':
    main()
