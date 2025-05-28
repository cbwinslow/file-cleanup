"""Utility functions for file cleanup."""

import hashlib
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get detailed metadata for a file."""
    file_path = Path(file_path)
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'is_dir': file_path.is_dir(),
            'is_file': file_path.is_file(),
            'is_symlink': file_path.is_symlink(),
            'mode': stat.st_mode,
            'inode': stat.st_ino,
            'device': stat.st_dev,
            'n_links': stat.st_nlink,
            'user_id': stat.st_uid,
            'group_id': stat.st_gid,
        }
    except Exception as e:
        logging.error(f"Error getting metadata for {file_path}: {e}")
        return {}

def calculate_hash(file_path: Union[str, Path], algorithm: str = 'sha256',
                  chunk_size: int = 65536) -> str:
    """Calculate file hash using the specified algorithm."""
    hash_func = getattr(hashlib, algorithm.lower(), hashlib.sha256)
    hash_obj = hash_func()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.error(f"Error calculating hash for {file_path}: {e}")
        return ""

def human_readable_size(size_bytes: int, decimal_places: int = 2) -> str:
    """Convert size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            break
        size_bytes /= 1024.0
    return f"{size_bytes:.{decimal_places}f} {unit}"

def is_binary_file(file_path: Union[str, Path], chunk_size: int = 1024) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            return b'\0' in chunk or not is_text(chunk)
    except Exception:
        return False

def is_text(chunk: bytes) -> bool:
    """Check if bytes chunk appears to be text."""
    try:
        chunk.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def safe_delete(file_path: Union[str, Path], dry_run: bool = True) -> Tuple[bool, str]:
    """Safely delete a file with checks and optional dry run."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
        
    if not file_path.is_file():
        return False, f"Not a regular file: {file_path}"
        
    try:
        if dry_run:
            return True, f"Would delete: {file_path}"
            
        # Move to trash instead of permanent delete
        trash_dir = file_path.parent / '.trash'
        trash_dir.mkdir(exist_ok=True)
        
        # Ensure unique filename in trash
        counter = 1
        trash_path = trash_dir / file_path.name
        while trash_path.exists():
            name_parts = file_path.stem, file_path.suffix
            trash_path = trash_dir / f"{name_parts[0]}_{counter}{name_parts[1]}"
            counter += 1
            
        file_path.rename(trash_path)
        return True, f"Moved to trash: {file_path} -> {trash_path}"
        
    except Exception as e:
        return False, f"Error deleting {file_path}: {str(e)}"

def get_file_type(file_path: Union[str, Path]) -> str:
    """Get file type using python-magic."""
    try:
        import magic
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except ImportError:
        return "application/octet-stream"
    except Exception as e:
        logging.error(f"Error getting file type for {file_path}: {e}")
        return "unknown"

def find_duplicate_files(directory: Union[str, Path],
                       algorithm: str = 'sha256') -> Dict[str, List[str]]:
    """Find duplicate files in a directory."""
    hashes = {}
    duplicates = {}
    
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = Path(root) / filename
            try:
                file_hash = calculate_hash(file_path, algorithm)
                if file_hash in hashes:
                    if file_hash in duplicates:
                        duplicates[file_hash].append(str(file_path))
                    else:
                        duplicates[file_hash] = [hashes[file_hash], str(file_path)]
                else:
                    hashes[file_hash] = str(file_path)
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                continue
                
    return {k: v for k, v in duplicates.items() if len(v) > 1}

def get_directory_size(directory: Union[str, Path]) -> Tuple[int, int]:
    """Get total size and file count of a directory."""
    total_size = 0
    file_count = 0
    
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
                file_count += 1
            except OSError:
                continue
                
    return total_size, file_count
