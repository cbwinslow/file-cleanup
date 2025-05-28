"""Command-line interface for file cleanup utility."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from file_cleanup.core.analyzer import FileAnalyzer
from file_cleanup.utils import (
    calculate_hash,
    get_directory_size,
    get_file_metadata,
    get_file_type,
    human_readable_size,
    safe_delete,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("file_cleanup")
console = Console()

class FileCleanupCLI:
    """Command-line interface for file cleanup utility."""

    def __init__(self):
        self.parser = self._create_parser()
        self.args = None
        self.analyzer = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="File Cleanup Utility - Clean and organize your files"
        )
        
        # Global arguments
        parser.add_argument(
            "--debug", 
            action="store_true", 
            help="Enable debug output"
        )
        parser.add_argument(
            "--log-file",
            type=str,
            default="file_cleanup.log",
            help="Log file path (default: file_cleanup.log)",
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Scan command
        scan_parser = subparsers.add_parser("scan", help="Scan directory for files")
        scan_parser.add_argument("directory", help="Directory to scan")
        scan_parser.add_argument(
            "--recursive", 
            action="store_true", 
            help="Scan directories recursively"
        )
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            "analyze", 
            help="Analyze files in directory"
        )
        analyze_parser.add_argument("directory", help="Directory to analyze")
        analyze_parser.add_argument(
            "--age-days", 
            type=int, 
            default=365,
            help="Threshold in days for old files (default: 365)"
        )
        analyze_parser.add_argument(
            "--similarity",
            type=float,
            default=0.9,
            help="Similarity threshold (0-1) for finding similar files (default: 0.9)",
        )
        
        # Clean command
        clean_parser = subparsers.add_parser("clean", help="Clean files")
        clean_parser.add_argument("directory", help="Directory to clean")
        clean_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        clean_parser.add_argument(
            "--confirm",
            action="store_true",
            help="Ask for confirmation before deleting each file",
        )
        clean_parser.add_argument(
            "--age-days",
            type=int,
            default=365,
            help="Delete files older than this many days (default: 365)",
        )
        
        # Duplicates command
        dup_parser = subparsers.add_parser(
            "duplicates", 
            help="Find duplicate files"
        )
        dup_parser.add_argument("directory", help="Directory to search for duplicates")
        dup_parser.add_argument(
            "--algorithm",
            default="sha256",
            choices=["md5", "sha1", "sha256", "sha512"],
            help="Hash algorithm to use (default: sha256)",
        )
        
        # Report command
        report_parser = subparsers.add_parser("report", help="Generate reports")
        report_parser.add_argument("directory", help="Directory to generate report for")
        report_parser.add_argument(
            "--output",
            default="report.json",
            help="Output file path (default: report.json)",
        )
        report_parser.add_argument(
            "--format",
            choices=["json", "csv", "table"],
            default="table",
            help="Output format (default: table)",
        )
        
        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        self.args = self.parser.parse_args(args)
        
        # Set up logging
        log_level = logging.DEBUG if self.args.debug else logging.INFO
        logger.setLevel(log_level)
        
        # Add file handler if log file is specified
        if hasattr(self.args, 'log_file'):
            file_handler = logging.FileHandler(self.args.log_file)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(file_handler)
        
        # Execute command
        if not self.args.command:
            self.parser.print_help()
            return 1
            
        try:
            command_method = getattr(self, f"cmd_{self.args.command}")
            return command_method()
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=self.args.debug)
            return 1

    def cmd_scan(self) -> int:
        """Handle scan command."""
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Scanning directory:[/bold] {directory}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Scanning...", total=None)
            self.analyzer = FileAnalyzer(directory)
            self.analyzer.scan_directory()
        
        total_size, file_count = get_directory_size(directory)
        
        # Display results
        table = Table(title="Scan Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Directory", str(directory))
        table.add_row("Total Files", str(file_count))
        table.add_row("Total Size", human_readable_size(total_size))
        
        console.print(table)
        return 0

    def cmd_analyze(self) -> int:
        """Handle analyze command."""
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Analyzing directory:[/bold] {directory}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Analyzing...", total=None)
            self.analyzer = FileAnalyzer(directory)
            self.analyzer.scan_directory()
            self.analyzer.find_orphans()
            self.analyzer.analyze_age(threshold_days=self.args.age_days)
            self.analyzer.find_similar_files(similarity_threshold=self.args.similarity)
        
        # Display results
        summary = self.analyzer.get_summary()
        
        table = Table(title="Analysis Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in summary.items():
            table.add_row(
                key.replace('_', ' ').title(), 
                str(value) if not isinstance(value, (list, dict)) else f"{len(value)} items"
            )
        
        console.print(table)
        return 0

    def cmd_clean(self) -> int:
        """Handle clean command."""
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Cleaning directory:[/bold] {directory}")
        
        if self.args.dry_run:
            console.print("[yellow]Dry run mode - no files will be deleted[/yellow]")
        
        # Perform analysis first
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Analyzing files...", total=None)
            self.analyzer = FileAnalyzer(directory)
            self.analyzer.scan_directory()
            self.analyzer.find_orphans()
            self.analyzer.analyze_age(threshold_days=self.args.age_days)
            self.analyzer.find_deprecated_files()
        
        # Get files to clean
        files_to_clean = []
        
        # Add old files
        files_to_clean.extend(
            (f, f"File not modified in {self.args.age_days}+ days")
            for f in self.analyzer.old_files
        )
        
        # Add deprecated files
        files_to_clean.extend(
            (f, "File matches deprecated pattern") 
            for f in self.analyzer.deprecated_files
        )
        
        # Add duplicates (keep one copy)
        for file_list in self.analyzer.duplicates.values():
            files_to_clean.extend(
                ({"path": f}, "Duplicate file") 
                for f in file_list[1:]  # Keep the first file
            )
        
        if not files_to_clean:
            console.print("[green]No files to clean![/green]")
            return 0
            
        # Display files to be cleaned
        table = Table(title="Files to Clean")
        table.add_column("File", style="cyan")
        table.add_column("Reason", style="yellow")
        table.add_column("Size", style="green")
        
        total_size = 0
        for file_info, reason in files_to_clean:
            size = file_info.get('size', 0)
            table.add_row(
                file_info['path'],
                reason,
                human_readable_size(size)
            )
            total_size += size
            
        table.add_section()
        table.add_row(
            "[bold]Total", 
            f"{len(files_to_clean)} files", 
            f"[bold]{human_readable_size(total_size)}"
        )
        
        console.print(table)
        
        # Ask for confirmation
        if not self.args.dry_run:
            if not self.args.confirm or console.input(
                "\n[bold red]Are you sure you want to delete these files? (y/N): [/bold red]"
            ).lower() == 'y':
                # Delete files
                with Progress() as progress:
                    task = progress.add_task(
                        "[red]Deleting files...", 
                        total=len(files_to_clean)
                    )
                    
                    for file_info, _ in files_to_clean:
                        success, message = safe_delete(
                            file_info['path'], 
                            dry_run=self.args.dry_run
                        )
                        if not success:
                            logger.warning(message)
                        progress.advance(task)
                
                console.print("[green]\nCleanup completed![/green]")
            else:
                console.print("[yellow]Operation cancelled.[/yellow]")
        
        return 0

    def cmd_duplicates(self) -> int:
        """Handle duplicates command."""
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Finding duplicates in:[/bold] {directory}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Searching for duplicates...", total=None)
            self.analyzer = FileAnalyzer(directory)
            self.analyzer.scan_directory()
            self.analyzer.find_duplicates()
        
        if not self.analyzer.duplicates:
            console.print("[green]No duplicate files found![/green]")
            return 0
            
        # Display duplicates
        table = Table(title="Duplicate Files")
        table.add_column("Hash", style="cyan")
        table.add_column("Files", style="green")
        table.add_column("Size", style="yellow")
        
        total_size_saved = 0
        total_duplicates = 0
        
        for file_hash, file_paths in self.analyzer.duplicates.items():
            if len(file_paths) > 1:
                file_size = Path(file_paths[0]).stat().st_size
                total_size_saved += file_size * (len(file_paths) - 1)
                total_duplicates += len(file_paths) - 1
                
                table.add_row(
                    file_hash[:8],
                    "\n".join(f"{i+1}. {p}" for i, p in enumerate(file_paths)),
                    human_readable_size(file_size)
                )
                table.add_section()
        
        table.add_section()
        table.add_row(
            "[bold]Total",
            f"{total_duplicates} duplicate files",
            f"[bold]{human_readable_size(total_size_saved)} to save"
        )
        
        console.print(table)
        return 0

    def cmd_report(self) -> int:
        """Handle report command."""
        directory = Path(self.args.directory).resolve()
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return 1
            
        console.print(f"[bold]Generating report for:[/bold] {directory}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Generating report...", total=None)
            self.analyzer = FileAnalyzer(directory)
            self.analyzer.scan_directory()
            self.analyzer.find_orphans()
            self.analyzer.analyze_age()
            self.analyzer.find_similar_files()
            self.analyzer.find_deprecated_files()
        
        # Generate report data
        report = {
            "directory": str(directory),
            "scan_time": datetime.now().isoformat(),
            "analysis": self.analyzer.get_summary(),
            "files": [
                {
                    "path": str(file_info["path"]),
                    "size": file_info["size"],
                    "modified": file_info["modified"].isoformat(),
                    "type": file_info.get("mime_type", "unknown"),
                }
                for file_info in self.analyzer.files
            ],
            "duplicates": [
                {"hash": h, "files": files, "size": len(files)}
                for h, files in self.analyzer.duplicates.items()
                if len(files) > 1
            ],
            "orphans": [str(f["path"]) for f in self.analyzer.orphans],
            "old_files": [
                {"path": f["path"], "modified": f["modified"].isoformat()}
                for f in self.analyzer.old_files
            ],
        }
        
        # Save report
        output_path = Path(self.args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.args.format == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif self.args.format == "csv":
            # Simple CSV export of files
            import csv
            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["path", "size", "modified", "type"])
                for file_info in self.analyzer.files:
                    writer.writerow([
                        file_info["path"],
                        file_info["size"],
                        file_info["modified"].isoformat(),
                        file_info.get("mime_type", "unknown"),
                    ])
        else:  # table (default)
            # Display summary table
            table = Table(title="File System Report")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in report["analysis"].items():
                table.add_row(
                    key.replace('_', ' ').title(), 
                    str(value) if not isinstance(value, (list, dict)) else f"{len(value)} items"
                )
            
            console.print(table)
            
            # Save as JSON as well for table format
            json_path = output_path.with_suffix(".json")
            with open(json_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"\n[green]Detailed report saved to: {json_path}[/green]")
            
        if self.args.format != "table":
            console.print(f"\n[green]Report saved to: {output_path}[/green]")
        
        return 0

def main() -> int:
    """Main entry point for the CLI."""
    try:
        cli = FileCleanupCLI()
        return cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if cli and cli.args and cli.args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
