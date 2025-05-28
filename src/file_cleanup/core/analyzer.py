"""Core file analysis functionality with advanced algorithms."""

import hashlib
import logging
import magic
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np
from rich.progress import Progress, track
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class FileAnalyzer:
    """Advanced file system analyzer with multiple detection algorithms."""

    def __init__(self, root_path: Union[str, Path]):
        """Initialize the file analyzer with root directory path."""
        self.root_path = Path(root_path).resolve()
        self.files: List[Dict] = []
        self.file_hashes: Dict[str, str] = {}
        self.file_metadata: Dict[str, Dict] = {}
        self.duplicates: Dict[str, List[str]] = defaultdict(list)
        self.orphans: List[Dict] = []
        self.old_files: List[Dict] = []
        self.unused_files: List[Dict] = []
        self.deprecated_files: List[Dict] = []
        self.similar_files: Dict[str, List[Dict]] = defaultdict(list)
        self.mime = magic.Magic(mime=True)

    def scan_directory(self, path: Optional[Path] = None) -> None:
        """Scan directory recursively and collect file information with progress tracking."""
        path = path or self.root_path
        logger.info(f"Starting directory scan: {path}")
        
        # First, count all files for progress tracking
        total_files = sum(1 for _ in path.rglob('*') if _.is_file())
        
        with Progress() as progress:
            task = progress.add_task("Scanning files...", total=total_files)
            
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        self._process_file(file_path)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {str(e)}")
                    progress.advance(task)
        
        logger.info(f"Completed scanning {len(self.files)} files")

    def _process_file(self, file_path: Path) -> None:
        """Process a single file and collect its metadata."""
        try:
            stat = file_path.stat()
            file_hash = self._calculate_hash(file_path)
            
            file_info = {
                'path': str(file_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'hash': file_hash,
                'parent': str(file_path.parent),
                'extension': file_path.suffix.lower(),
                'mime_type': self.mime.from_file(str(file_path)),
                'is_hidden': file_path.name.startswith('.'),
                'is_symlink': file_path.is_symlink(),
            }
            
            self.files.append(file_info)
            self.file_metadata[str(file_path)] = file_info
            
            # Track hashes for duplicate detection
            if file_hash in self.file_hashes:
                self.duplicates[file_hash].append(str(file_path))
                self.duplicates[file_hash].append(self.file_hashes[file_hash])
            else:
                self.file_hashes[file_hash] = str(file_path)
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")

    def _calculate_hash(self, file_path: Path, chunk_size: int = 65536) -> str:
        """Calculate SHA-256 hash of file with progress support."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {str(e)}")
            return ""

    def find_orphans(self, check_parents: bool = True) -> None:
        """Find orphaned files (files without parent directories)."""
        self.orphans = []
        for file in self.files:
            if not os.path.exists(file['parent']):
                self.orphans.append(file)
            elif check_parents:
                # Check if any parent directory is also an orphan
                parent = Path(file['parent'])
                while parent != self.root_path and parent != parent.parent:
                    if not parent.exists():
                        self.orphans.append(file)
                        break
                    parent = parent.parent

    def analyze_age(self, threshold_days: int = 365) -> None:
        """Find old files based on modification date."""
        now = datetime.now()
        self.old_files = [
            file for file in self.files 
            if (now - file['modified']).days > threshold_days
        ]

    def find_similar_files(self, similarity_threshold: float = 0.9) -> None:
        """Find similar files using TF-IDF and cosine similarity."""
        text_files = [f for f in self.files if f['mime_type'].startswith('text/')]
        
        if not text_files:
            return
            
        # Extract file contents
        contents = []
        valid_files = []
        
        for file in text_files:
            try:
                with open(file['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    contents.append(f.read())
                    valid_files.append(file)
            except Exception as e:
                logger.warning(f"Could not read {file['path']} for similarity analysis: {e}")
        
        if not valid_files:
            return
            
        # Vectorize text content
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform(contents)
            
            # Calculate cosine similarity
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # Find similar pairs
            for i in range(len(valid_files)):
                for j in range(i + 1, len(valid_files)):
                    if cosine_sim[i, j] > similarity_threshold:
                        file1 = valid_files[i]['path']
                        file2 = valid_files[j]['path']
                        similarity = cosine_sim[i, j]
                        
                        self.similar_files[file1].append({
                            'path': file2,
                            'similarity': similarity
                        })
                        
        except Exception as e:
            logger.error(f"Error in similarity analysis: {str(e)}")

    def find_unused_files(self, access_threshold_days: int = 90) -> None:
        """Find files that haven't been accessed in a while."""
        now = datetime.now()
        self.unused_files = [
            file for file in self.files
            if (now - file['accessed']).days > access_threshold_days
        ]

    def find_deprecated_files(self, patterns: Optional[List[str]] = None) -> None:
        """Find files that match deprecated patterns."""
        if patterns is None:
            patterns = [
                r'\.(old|bak|swp|swo|tmp|temp|~)$',
                r'(?i)(backup|temp|tmp|old|deprecated)',
                r'~$',
                r'\.bak$',
                r'\.swp$',
                r'\.swo$',
                r'\.tmp$',
                r'\.temp$',
            ]
            
        compiled_patterns = [re.compile(pattern) for pattern in patterns]
        
        for file in self.files:
            file_path = file['path'].lower()
            if any(pattern.search(file_path) for pattern in compiled_patterns):
                self.deprecated_files.append(file)

    def cluster_similar_files(self, threshold: float = 0.8) -> Dict[int, List[Dict]]:
        """Cluster similar files using hierarchical clustering."""
        if not self.file_metadata:
            return {}
            
        # Create feature matrix (using file size and modification time as features)
        features = []
        file_paths = []
        
        for file_path, metadata in self.file_metadata.items():
            features.append([
                float(metadata['size']),
                metadata['modified'].timestamp(),
                len(metadata['extension']),
                len(metadata['path'].split(os.sep))
            ])
            file_paths.append(file_path)
            
        if not features:
            return {}
            
        # Normalize features
        features = np.array(features)
        features = (features - features.mean(axis=0)) / features.std(axis=0)
        
        # Calculate pairwise distances
        distances = pdist(features, 'euclidean')
        
        # Apply hierarchical clustering
        Z = linkage(distances, 'ward')
        clusters = fcluster(Z, t=threshold, criterion='distance')
        
        # Group files by cluster
        clustered_files = defaultdict(list)
        for file_path, cluster_id in zip(file_paths, clusters):
            clustered_files[cluster_id].append(self.file_metadata[file_path])
            
        return clustered_files

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of the analysis."""
        return {
            'total_files': len(self.files),
            'duplicate_files': sum(len(files) for files in self.duplicates.values()),
            'orphan_files': len(self.orphans),
            'old_files': len(self.old_files),
            'unused_files': len(self.unused_files),
            'deprecated_files': len(self.deprecated_files),
            'similar_file_groups': len(self.similar_files),
        }
