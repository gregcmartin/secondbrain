"""Command-line interface for Second Brain."""

import asyncio
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import structlog
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .database import Database
from .pipeline import ProcessingPipeline

# Load environment variables
load_dotenv()

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging_level=20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

console = Console()
logger = structlog.get_logger()


def get_pid_file() -> Path:
    """Get path to PID file."""
    return Path.home() / "Library" / "Application Support" / "second-brain" / "second-brain.pid"


def is_running() -> bool:
    """Check if service is running."""
    pid_file = get_pid_file()
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # Process doesn't exist or PID file is invalid
        pid_file.unlink(missing_ok=True)
        return False


def save_pid():
    """Save current process PID."""
    pid_file = get_pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    """Remove PID file."""
    pid_file = get_pid_file()
    pid_file.unlink(missing_ok=True)


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Second Brain - Local-first visual memory capture and search."""
    pass


@main.command()
@click.option("--fps", type=float, help="Frames per second to capture")
@click.option("--daemon", is_flag=True, help="Run as daemon (background process)")
def start(fps: Optional[float], daemon: bool):
    """Start the capture service."""
    if is_running():
        console.print("[yellow]Service is already running[/yellow]")
        return
    
    console.print("[green]Starting Second Brain capture service...[/green]")
    
    # Load config
    config = Config()
    
    # Override FPS if provided
    if fps:
        config.set("capture.fps", fps)
    
    # Save PID
    save_pid()
    
    # Create pipeline
    pipeline = ProcessingPipeline(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        console.print("\n[yellow]Stopping service...[/yellow]")
        asyncio.create_task(pipeline.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start pipeline
    async def run():
        try:
            await pipeline.start()
            
            console.print(f"[green]✓[/green] Service started (PID: {os.getpid()})")
            console.print(f"[green]✓[/green] Capturing at {config.get('capture.fps')} FPS")
            console.print(f"[green]✓[/green] Press Ctrl+C to stop")
            
            # Keep running
            while pipeline.running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping service...[/yellow]")
        finally:
            await pipeline.stop()
            remove_pid()
            console.print("[green]Service stopped[/green]")
    
    try:
        asyncio.run(run())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        remove_pid()
        sys.exit(1)


@main.command()
def stop():
    """Stop the capture service."""
    if not is_running():
        console.print("[yellow]Service is not running[/yellow]")
        return
    
    pid_file = get_pid_file()
    with open(pid_file, "r") as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, signal.SIGTERM)
        console.print(f"[green]✓[/green] Sent stop signal to process {pid}")
        
        # Wait for process to stop
        import time
        for _ in range(10):
            if not is_running():
                console.print("[green]Service stopped[/green]")
                return
            time.sleep(0.5)
        
        console.print("[yellow]Service may still be stopping...[/yellow]")
        
    except OSError as e:
        console.print(f"[red]Error stopping service: {e}[/red]")
        remove_pid()


@main.command()
def status():
    """Show service status."""
    if not is_running():
        console.print("[yellow]Service is not running[/yellow]")
        return
    
    console.print("[green]Service is running[/green]")
    
    # Get stats from database
    try:
        db = Database()
        stats = db.get_database_stats()
        
        table = Table(title="Second Brain Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Status", "Running")
        table.add_row("Total Frames", str(stats["frame_count"]))
        table.add_row("Text Blocks", str(stats["text_block_count"]))
        table.add_row("Apps Tracked", str(stats["window_count"]))
        
        if stats["database_size_bytes"]:
            size_mb = stats["database_size_bytes"] / (1024 * 1024)
            table.add_row("Database Size", f"{size_mb:.2f} MB")
        
        if stats["oldest_frame_timestamp"]:
            oldest = datetime.fromtimestamp(stats["oldest_frame_timestamp"])
            table.add_row("Oldest Frame", oldest.strftime("%Y-%m-%d %H:%M:%S"))
        
        if stats["newest_frame_timestamp"]:
            newest = datetime.fromtimestamp(stats["newest_frame_timestamp"])
            table.add_row("Newest Frame", newest.strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(table)
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")


@main.command()
@click.argument("query")
@click.option("--app", help="Filter by application name")
@click.option("--from", "from_date", help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", help="End date (YYYY-MM-DD)")
@click.option("--limit", default=10, help="Maximum number of results")
def query(query: str, app: Optional[str], from_date: Optional[str], to_date: Optional[str], limit: int):
    """Search captured memory."""
    console.print(f"[cyan]Searching for:[/cyan] {query}")
    
    # Parse dates
    start_timestamp = None
    end_timestamp = None
    
    if from_date:
        try:
            dt = datetime.strptime(from_date, "%Y-%m-%d")
            start_timestamp = int(dt.timestamp())
        except ValueError:
            console.print(f"[red]Invalid from date format. Use YYYY-MM-DD[/red]")
            return
    
    if to_date:
        try:
            dt = datetime.strptime(to_date, "%Y-%m-%d")
            end_timestamp = int(dt.timestamp())
        except ValueError:
            console.print(f"[red]Invalid to date format. Use YYYY-MM-DD[/red]")
            return
    
    # Search database
    try:
        db = Database()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Searching...", total=None)
            
            results = db.search_text(
                query=query,
                app_filter=app,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                limit=limit,
            )
        
        if not results:
            console.print("[yellow]No results found[/yellow]")
            return
        
        console.print(f"\n[green]Found {len(results)} results:[/green]\n")
        
        for i, result in enumerate(results, 1):
            timestamp = datetime.fromtimestamp(result["timestamp"])
            
            panel = Panel(
                f"[bold]{result['window_title']}[/bold]\n"
                f"[dim]{result['app_name']} • {timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n\n"
                f"{result['text'][:200]}{'...' if len(result['text']) > 200 else ''}",
                title=f"Result {i}",
                border_style="cyan",
            )
            console.print(panel)
        
        db.close()
        
    except Exception as e:
        console.print(f"[red]Error searching: {e}[/red]")
        import traceback
        traceback.print_exc()


@main.command()
def health():
    """Check system health."""
    console.print("[cyan]Checking system health...[/cyan]\n")
    
    checks = []
    
    # Check if service is running
    if is_running():
        checks.append(("Service Status", "✓ Running", "green"))
    else:
        checks.append(("Service Status", "✗ Not running", "yellow"))
    
    # Check OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        checks.append(("OpenAI API Key", "✓ Configured", "green"))
    else:
        checks.append(("OpenAI API Key", "✗ Not found", "red"))
    
    # Check database
    try:
        db = Database()
        db.close()
        checks.append(("Database", "✓ Accessible", "green"))
    except Exception as e:
        checks.append(("Database", f"✗ Error: {e}", "red"))
    
    # Check disk space
    import psutil
    config = Config()
    frames_dir = config.get_frames_dir()
    disk = psutil.disk_usage(str(frames_dir))
    free_gb = disk.free / (1024 ** 3)
    
    if free_gb > config.get("capture.min_free_space_gb", 10):
        checks.append(("Disk Space", f"✓ {free_gb:.1f} GB free", "green"))
    else:
        checks.append(("Disk Space", f"✗ Only {free_gb:.1f} GB free", "red"))
    
    # Display results
    table = Table(title="Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status")
    
    for component, status, color in checks:
        table.add_row(component, f"[{color}]{status}[/{color}]")
    
    console.print(table)


if __name__ == "__main__":
    main()
