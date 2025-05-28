import os
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_cleanup.log'),
        logging.StreamHandler()
    ]
)

console = Console()

class FileAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.files = []
        self.duplicates = {}
        self.orphans = []
        self.old_files = []
        self.unused_files = []
        self.deprecated_files = []
        self.metadata = {}

    def scan_directory(self, path: Path = None) -> None:
        """Scan directory recursively and collect file information."""
        if path is None:
            path = self.root_path

        with Progress() as progress:
            task = progress.add_task("Scanning files...", total=1)
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        self._process_file(file_path)
                    except Exception as e:
                        logging.error(f"Error processing {file_path}: {str(e)}")
                progress.advance(task)

    def _process_file(self, file_path: Path) -> None:
        """Process individual file and collect metadata."""
        try:
            stat = file_path.stat()
            file_info = {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'hash': self._calculate_hash(file_path),
                'parent': str(file_path.parent)
            }
            self.files.append({
                'path': str(file_path),
                'info': file_info
            })
            self.metadata[str(file_path)] = file_info
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logging.error(f"Error hashing {file_path}: {str(e)}")
            return ""

    def find_duplicates(self) -> None:
        """Find duplicate files based on hash."""
        hash_map = {}
        for file in self.files:
            file_hash = file['info']['hash']
            if file_hash in hash_map:
                if file_hash not in self.duplicates:
                    self.duplicates[file_hash] = [hash_map[file_hash]]
                self.duplicates[file_hash].append(file['path'])
            else:
                hash_map[file_hash] = file['path']

    def find_orphans(self) -> None:
        """Find orphan files (files without parent directories)."""
        for file in self.files:
            parent = file['info']['parent']
            if not os.path.exists(parent):
                self.orphans.append(file['path'])

    def analyze_age(self, threshold_days: int = 365) -> None:
        """Find old files based on modification date."""
        now = datetime.now()
        for file in self.files:
            modified = file['info']['modified']
            age = (now - modified).days
            if age > threshold_days:
                self.old_files.append({
                    'path': file['path'],
                    'age_days': age
                })

    def generate_report(self) -> None:
        """Generate a summary report of findings."""
        console.print("\n[bold]File Analysis Report[/bold]", style="cyan")

        # Create table for duplicates
        if self.duplicates:
            duplicates_table = Table(title="Duplicate Files")
            duplicates_table.add_column("Hash", style="cyan")
            duplicates_table.add_column("Files", style="green")
            for hash_val, files in self.duplicates.items():
                duplicates_table.add_row(hash_val[:8], "\n".join(files))
            console.print(duplicates_table)

        # Create table for orphans
        if self.orphans:
            orphans_table = Table(title="Orphan Files")
            orphans_table.add_column("Path", style="red")
            for orphan in self.orphans:
                orphans_table.add_row(orphan)
            console.print(orphans_table)

        # Create table for old files
        if self.old_files:
            old_files_table = Table(title="Old Files")
            old_files_table.add_column("Path", style="yellow")
            old_files_table.add_column("Age (days)", style="cyan")
            for old_file in self.old_files:
                old_files_table.add_row(old_file['path'], str(old_file['age_days']))
            console.print(old_files_table)

    def save_report(self, filename: str = "cleanup_report.json") -> None:
        """Save analysis results to a JSON file."""
        report = {
            'duplicates': self.duplicates,
            'orphans': self.orphans,
            'old_files': self.old_files,
            'metadata': self.metadata
        }
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4, default=str)

    def load_report(self, filename: str = "cleanup_report.json") -> None:
        """Load previous analysis results from a JSON file."""
        try:
            with open(filename, 'r') as f:
                report = json.load(f)
            self.duplicates = report.get('duplicates', {})
            self.orphans = report.get('orphans', [])
            self.old_files = report.get('old_files', [])
            self.metadata = report.get('metadata', {})
        except FileNotFoundError:
            logging.warning(f"Report file {filename} not found")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='File system cleanup utility')
    parser.add_argument('path', help='Path to scan')
    parser.add_argument('--scan', action='store_true', help='Scan directory')
    parser.add_argument('--analyze', action='store_true', help='Analyze files')
    parser.add_argument('--report', action='store_true', help='Generate report')
    args = parser.parse_args()

    analyzer = FileAnalyzer(args.path)

    if args.scan:
        analyzer.scan_directory()
    if args.analyze:
        analyzer.find_duplicates()
        analyzer.find_orphans()
        analyzer.analyze_age()
    if args.report:
        analyzer.generate_report()
        analyzer.save_report()

if __name__ == "__main__":
    main()
