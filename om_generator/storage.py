"""
storage.py — File I/O abstraction layer for Provenance.

Currently implements local disk only. All reads and writes go through
this module so that swapping to S3 later is a config change, not a rewrite.

Future: set STORAGE_BACKEND=s3 in environment to route through boto3.
"""

import os
import json
from pathlib import Path

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")


def read_file(path: str) -> bytes:
    """Read a file. Returns raw bytes."""
    return Path(path).read_bytes()


def read_text(path: str, encoding: str = "utf-8") -> str:
    """Read a text file. Returns string."""
    return Path(path).read_text(encoding=encoding)


def read_json(path: str) -> dict:
    """Read and parse a JSON file."""
    return json.loads(read_text(path))


def write_file(path: str, data: bytes) -> None:
    """Write bytes to a file. Creates parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    """Write a string to a file. Creates parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)


def write_json(path: str, data: dict, indent: int = 2) -> None:
    """Serialize and write a dict as JSON."""
    write_text(path, json.dumps(data, indent=indent))


def file_exists(path: str) -> bool:
    """Check if a file exists."""
    return Path(path).exists()


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if needed."""
    Path(path).mkdir(parents=True, exist_ok=True)
