"""ML analysis command for the file cleanup utility."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from file_cleanup.ml.analyzer import MLFileAnalyzer
from file_cleanup.utils import human_readable_size

logger = logging.getLogger(__name__)
console = Console()

class MLFileCleanupCLI:
    """CLI for ML-based file cleanup analysis."""
    
    def __init__(self, args):
        """Initialize with command line arguments."""
        self.args = args
        self.ml_analyzer = None
    
    def cmd_ml_analyze(self) -> int:
        """Handle the ml-analyze command."""
        from file_cleanup.ml.trainer import train_default_model
        
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Analyzing files in:[/bold] {directory}")
        
        try:
            # Handle model training if requested
            if self.args.train:
                if not self.args.model_path:
                    logger.error("--model-path is required when --train is specified")
                    return 1
                    
                console.print("[yellow]Training new model...[/yellow]")
                try:
                    self.ml_analyzer = MLFileAnalyzer.train_default_model(
                        output_dir=self.args.model_path,
                        model_type='random_forest'
                    )
                    console.print("[green]Model trained successfully![/green]")
                except Exception as e:
                    logger.error(f"Error training model: {e}")
                    return 1
            else:
                # Load existing model or use default rules
                self.ml_analyzer = MLFileAnalyzer(
                    model_path=self.args.model_path,
                    model_type='random_forest'
                )
            
            # Analyze files
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Analyzing files...", total=None)
                
                results = self.ml_analyzer.analyze_directory(
                    directory=directory,
                    include_patterns=getattr(self.args, 'include', None),
                    exclude_patterns=getattr(self.args, 'exclude', None),
                    min_confidence=self.args.min_confidence
                )
            
            # Display results
            self._display_results(results)
            
            # Save results to file
            if self.args.output:
                self._save_results(results, self.args.output)
                
            return 0
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            return 1
    
    def _display_results(self, results: List[Dict]) -> None:
        """Display analysis results in a table."""
        if not results:
            console.print("[green]No files recommended for deletion.[/green]")
            return
        
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
                str(result['path']),
                f"{result.get('confidence', 0) * 100:.1f}%",
                human_readable_size(size),
                ", ".join(result.get('reasons', []))
            )
        
        table.add_section()
        table.add_row(
            "[bold]Total",
            f"{len(results)} files",
            f"[bold]{human_readable_size(total_size)}",
            ""
        )
        
        console.print(table)
    
    def _save_results(self, results: List[Dict], output_path: str) -> None:
        """Save analysis results to a file."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert datetime objects to strings
            serializable_results = []
            for result in results:
                res = result.copy()
                for key in ['modified', 'accessed']:
                    if key in res and hasattr(res[key], 'isoformat'):
                        res[key] = res[key].isoformat()
                serializable_results.append(res)
            
            with open(output_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': serializable_results
                }, f, indent=2)
                
            console.print(f"[green]Results saved to {output_path}[/green]")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def add_ml_analyze_command(subparsers):
    """Add the ml-analyze command to the argument parser."""
    ml_analyze_parser = subparsers.add_parser(
        "ml-analyze",
        help="Analyze files using machine learning to identify files that can be safely deleted"
    )
    ml_analyze_parser.add_argument("directory", help="Directory to analyze")
    
    # Add include/exclude patterns
    ml_analyze_parser.add_argument(
        "--include",
        type=str,
        nargs='+',
        help="File patterns to include (e.g., '*.py' '*.txt')",
    )
    ml_analyze_parser.add_argument(
        "--exclude",
        type=str,
        nargs='+',
        help="File patterns to exclude (e.g., '*.tmp' '*.log')",
    )
    
    ml_analyze_parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.7,
        help="Minimum confidence threshold (0-1) for recommendations (default: 0.7)",
    )
    ml_analyze_parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to a pre-trained model (default: uses built-in rules)",
    )
    ml_analyze_parser.add_argument(
        "--train",
        action="store_true",
        help="Train a new model before analyzing (requires --model-path)",
    )
    ml_analyze_parser.add_argument(
        "--output",
        type=str,
        default="ml_analysis.json",
        help="Output file path (default: ml_analysis.json)",
    )
    
    return ml_analyze_parser
