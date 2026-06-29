"""Backup verification — checksum validation, integrity checks, and restore dry-run."""

import gzip
import json
import logging
import os
import sqlite3
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    path: str
    verified: bool = False
    checksum_match: bool = False
    integrity_ok: bool = False
    size_bytes: int = 0
    format_detected: str = ""
    error: Optional[str] = None
    details: dict = field(default_factory=dict)


def _checksum_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class VerifyService:
    @staticmethod
    def verify_db_dump(path: str, expected_checksum: Optional[str] = None) -> VerificationResult:
        result = VerificationResult(path=path)
        p = Path(path)
        if not p.exists():
            result.error = "File not found"
            return result

        result.size_bytes = p.stat().st_size
        if result.size_bytes == 0:
            result.error = "Empty file"
            return result

        if expected_checksum:
            actual = _checksum_file(p)
            result.checksum_match = actual == expected_checksum

        try:
            if path.endswith(".gz"):
                with gzip.open(p, "rb") as f:
                    header = f.read(1024)
                    result.format_detected = "gzip"
                    result.integrity_ok = len(header) > 0
            else:
                with open(p, "rb") as f:
                    header = f.read(1024)
                    result.format_detected = "raw"
                    result.integrity_ok = len(header) > 0

            result.details["header_size"] = len(header)
            result.verified = result.integrity_ok
        except Exception as e:
            result.error = str(e)

        return result

    @staticmethod
    def verify_tar_archive(path: str, expected_checksum: Optional[str] = None) -> VerificationResult:
        result = VerificationResult(path=path)
        p = Path(path)
        if not p.exists():
            result.error = "File not found"
            return result

        result.size_bytes = p.stat().st_size
        if expected_checksum:
            result.checksum_match = _checksum_file(p) == expected_checksum

        try:
            with tarfile.open(p, "r:*") as tar:
                members = tar.getmembers()
                result.format_detected = f"tar ({p.suffix})"
                result.integrity_ok = len(members) > 0
                result.details["member_count"] = len(members)
                result.details["members"] = [m.name for m in members[:50]]

                corrupt = [m for m in members if m.issize() and m.size < 0]
                if corrupt:
                    result.error = f"{len(corrupt)} corrupt entries found"
                    result.integrity_ok = False
                else:
                    result.verified = True

                for m in members:
                    if m.name == "config.yaml":
                        f = tar.extractfile(m)
                        if f:
                            try:
                                yaml.safe_load(f)
                                result.details["config_valid"] = True
                            except Exception:
                                result.details["config_valid"] = False
        except Exception as e:
            result.error = str(e)

        return result

    @staticmethod
    def verify_config_backup(path: str) -> VerificationResult:
        result = VerifyService.verify_tar_archive(path)
        if result.verified:
            result.details["type"] = "config_backup"
        return result

    @staticmethod
    def verify_storage_backup(path: str) -> VerificationResult:
        result = VerifyService.verify_tar_archive(path)
        if result.verified:
            with tarfile.open(path, "r:*") as tar:
                has_content = any(m.name.startswith("content/") for m in tar.getmembers())
                result.details["has_content_dir"] = has_content
                if not has_content:
                    result.error = "Backup missing content/ directory"
                    result.verified = False
        return result

    @staticmethod
    def dry_run_restore(path: str) -> VerificationResult:
        """Test that the archive can be extracted without actually writing files."""
        result = VerifyService.verify_tar_archive(path)
        if not result.verified:
            return result

        try:
            with tempfile.TemporaryDirectory() as tmp:
                with tarfile.open(path, "r:*") as tar:
                    tar.extractall(tmp)
                extracted = list(Path(tmp).rglob("*"))
                result.details["dry_run_extracted_count"] = len(extracted)
                result.details["dry_run_success"] = True
        except Exception as e:
            result.error = f"Dry-run restore failed: {e}"
            result.verified = False

        return result
