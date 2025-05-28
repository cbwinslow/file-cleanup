"""
ML-based File Cleanup Demo

This script demonstrates how to use the ML-based file cleanup functionality.
It shows how to train a model, analyze files, and get cleanup recommendations.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add parent directory to path to allow importing from file_cleanup
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_cleanup.ml import MLFileAnalyzer, train_default_model
from file_cleanup.utils import human_readable_size

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console = Console()

def setup_demo_environment(demo_dir: Path):
    """Set up a demo environment with sample files."""
    console.print("\n[bold]Setting up demo environment...[/bold]")
    
    # Create directories
    (demo_dir / "temp").mkdir(exist_ok=True)
    (demo_dir / "logs").mkdir(exist_ok=True)
    (demo_dir / "cache").mkdir(exist_ok=True)
    (demo_dir / "downloads").mkdir(exist_ok=True)
    
    # Create sample files
    (demo_dir / "temp" / "temp_file.tmp").touch()
    (demo_dir / "cache" / "cache_file.cache").touch()
    
    # Create log files
    (demo_dir / "logs" / "app.log").write_text("This is a log file\n" * 1000)
    
    # Create an old log file
    old_log = demo_dir / "logs" / "old_app.log"
    old_log.touch()
    old_time = datetime.now() - timedelta(days=60)
    os.utime(old_log, (old_log.stat().st_atime, old_time.timestamp()))
    
    # Create a download file
    (demo_dir / "downloads" / "archive.zip").touch()
    
    console.print(f"[green]✓ Demo environment created at: {demo_dir}[/green]")

def train_model(model_path: Path):
    """Train a new ML model."""
    console.print("\n[bold]Training ML model...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Training model...", total=None)
        metrics = train_default_model(model_path)
    
    console.print(f"[green]✓ Model trained with accuracy: {metrics['accuracy']:.2f}[/green]")
    console.print(f"Model saved to: {model_path}")
    return metrics

def analyze_with_ml(directory: Path, model_path: Path = None, min_confidence: float = 0.7):
    """Analyze files using ML and display results."""
    console.print("\n[bold]Analyzing files with ML...[/bold]")
    
    # Create analyzer with or without a model
    if model_path and model_path.exists():
        console.print(f"Using model from: {model_path}")
        analyzer = MLFileAnalyzer(model_path=model_path)
    else:
        console.print("Using default rule-based analyzer (no model)")
        analyzer = MLFileAnalyzer()
    
    # Analyze files
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Analyzing files...", total=None)
        results = analyzer.analyze_directory(
            directory=directory,
            min_confidence=min_confidence
        )
    
    # Display results
    console.print(f"\n[bold]Analysis Results (confidence ≥ {min_confidence}):[/bold]")
    
    if not results:
        console.print("[green]No files recommended for deletion.[/green]")
        return
    
    # Create and display table
    table = Table(title="Files Recommended for Deletion")
    table.add_column("File", style="cyan")
    table.add_column("Confidence", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Reasons", style="white")
    
    total_size = 0
    for result in results:
        size = result.get('size', 0)
        total_size += size
        
        table.add_row(
            str(Path(result['path']).relative_to(directory)),
            f"{result.get('confidence', 0) * 100:.1f}%",
            human_readable_size(size),
            ", ".join(result.get('reasons', []))
        )
    
    # Add summary row
    table.add_section()
    table.add_row(
        "[bold]Total",
        f"{len(results)} files",
        f"[bold]{human_readable_size(total_size)}",
        ""
    )
    
    console.print(table)
    
    # Save results to file
    output_file = directory / "cleanup_recommendations.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'directory': str(directory),
            'model_used': bool(model_path and model_path.exists()),
            'min_confidence': min_confidence,
            'results': [
                {
                    'path': str(Path(r['path']).relative_to(directory)),
                    'size': r.get('size', 0),
                    'confidence': r.get('confidence', 0),
                    'reasons': r.get('reasons', [])
                }
                for r in results
            ]
        }, f, indent=2)
    
    console.print(f"\n[green]✓ Results saved to: {output_file}[/green]")

def main():
    """Main function for the demo script."""
    parser = argparse.ArgumentParser(description="ML-based File Cleanup Demo")
    parser.add_argument(
        "--demo-dir",
        type=Path,
        default=Path("demo_ml_cleanup"),
        help="Directory for the demo environment"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train a new model before analyzing"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (0-1) for recommendations"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up paths
    demo_dir = args.demo_dir.resolve()
    model_path = demo_dir / "models" / "file_cleanup_model"
    
    try:
        # Set up demo environment
        if not demo_dir.exists():
            setup_demo_environment(demo_dir)
        
        # Train model if requested
        if args.train:
            train_model(model_path)
        
        # Analyze files
        analyze_with_ml(demo_dir, model_path if args.train else None, args.min_confidence)
        
        console.print("\n[bold green]✓ Demo completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
