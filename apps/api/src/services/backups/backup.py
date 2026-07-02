"""Backup service — database, configuration, and file storage backups."""

import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import yaml

from config.config import get_learnhouse_config
from src.core.storage import get_storage_backend

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    DATABASE = "database"
    CONFIG = "config"
    STORAGE = "storage"
    FULL = "full"


@dataclass
class BackupResult:
    backup_type: BackupType
    path: str
    size_bytes: int = 0
    checksum: str = ""
    started_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    success: bool = False


BACKUP_ROOT = Path("backups")


def _ensure_backup_dir() -> Path:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    return BACKUP_ROOT


def _checksum_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class BackupService:
    def __init__(self, backup_root: Path = BACKUP_ROOT):
        self.backup_root = backup_root

    async def backup_database(self, db_url: str) -> BackupResult:
        ts = _timestamp()
        filename = f"db_{ts}.sql.gz"
        dest = self.backup_root / filename
        result = BackupResult(backup_type=BackupType.DATABASE, path=str(dest), started_at=ts)

        try:
            _ensure_backup_dir()
            env = os.environ.copy()
            parsed = urlparse(db_url)
            env["PGPASSWORD"] = parsed.password or ""

            cmd = [
                "pg_dump",
                "--no-owner",
                "--no-acl",
                "--compress=9",
                "-f", str(dest),
                db_url,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                result.error = f"pg_dump failed: {proc.stderr[:500]}"
                return result

            result.size_bytes = dest.stat().st_size
            result.checksum = _checksum_file(dest)
            result.completed_at = _timestamp()
            result.success = True
            logger.info("Database backup created: %s (%d bytes)", dest, result.size_bytes)
        except Exception as e:
            result.error = str(e)
            logger.error("Database backup failed: %s", e)

        return result

    async def backup_config(self) -> BackupResult:
        ts = _timestamp()
        filename = f"config_{ts}.tar.gz"
        dest = self.backup_root / filename
        result = BackupResult(backup_type=BackupType.CONFIG, path=str(dest), started_at=ts)

        try:
            _ensure_backup_dir()
            cfg = get_learnhouse_config()

            config_data = {
                "general": {
                    "env": cfg.general_config.env,
                    "development_mode": cfg.general_config.development_mode,
                },
                "hosting_config": {
                    "domain": cfg.hosting_config.domain,
                    "frontend_domain": cfg.hosting_config.frontend_domain,
                    "ssl": cfg.hosting_config.ssl,
                    "content_delivery": {
                        "type": cfg.hosting_config.content_delivery.type,
                        "s3api": {
                            "bucket_name": cfg.hosting_config.content_delivery.s3api.bucket_name,
                            "endpoint_url": cfg.hosting_config.content_delivery.s3api.endpoint_url,
                            "region_name": cfg.hosting_config.content_delivery.s3api.region_name,
                        },
                    },
                },
                "backup_timestamp": ts,
            }

            with tempfile.TemporaryDirectory() as tmp:
                config_path = Path(tmp) / "config.yaml"
                with open(config_path, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)

                env_export = {}
                for key, val in sorted(os.environ.items()):
                    if key.startswith(("LEARNHOUSE_", "AWS_", "OTEL_", "SENTRY_")):
                        env_export[key] = "***REDACTED***" if any(k in key.lower() for k in ("key", "secret", "token", "password")) else val

                env_path = Path(tmp) / "env_export.json"
                with open(env_path, "w") as f:
                    json.dump(env_export, f, indent=2)

                with tarfile.open(dest, "w:gz") as tar:
                    tar.add(config_path, arcname="config.yaml")
                    tar.add(env_path, arcname="env_export.json")

            result.size_bytes = dest.stat().st_size
            result.checksum = _checksum_file(dest)
            result.completed_at = _timestamp()
            result.success = True
            logger.info("Config backup created: %s", dest)
        except Exception as e:
            result.error = str(e)
            logger.error("Config backup failed: %s", e)

        return result

    async def backup_storage(self) -> BackupResult:
        ts = _timestamp()
        filename = f"storage_{ts}.tar.gz"
        dest = self.backup_root / filename
        result = BackupResult(backup_type=BackupType.STORAGE, path=str(dest), started_at=ts)

        try:
            _ensure_backup_dir()
            content_dir = Path("content")
            if not content_dir.exists():
                result.error = "Content directory not found"
                return result

            with tarfile.open(dest, "w:gz") as tar:
                tar.add(str(content_dir), arcname="content")

            result.size_bytes = dest.stat().st_size
            result.checksum = _checksum_file(dest)
            result.completed_at = _timestamp()
            result.success = True
            logger.info("Storage backup created: %s (%d bytes)", dest, result.size_bytes)
        except Exception as e:
            result.error = str(e)
            logger.error("Storage backup failed: %s", e)

        return result

    async def backup_full(self) -> dict[str, BackupResult]:
        cfg = get_learnhouse_config()
        db_url = cfg.database.sql_connection_string or os.environ.get("LEARNHOUSE_SQL_CONNECTION_STRING", "")

        results = {}
        if db_url:
            results["database"] = await self.backup_database(db_url)
        results["config"] = await self.backup_config()
        results["storage"] = await self.backup_storage()

        return results

    async def restore_database(self, backup_path: str, db_url: str) -> bool:
        path = Path(backup_path)
        if not path.exists():
            logger.error("Backup file not found: %s", backup_path)
            return False

        try:
            env = os.environ.copy()
            parsed = urlparse(db_url)
            env["PGPASSWORD"] = parsed.password or ""

            # Detect format: compressed SQL (.sql.gz) → psql,  custom (.dump) → pg_restore
            name = path.name
            if name.endswith(".sql.gz") or name.endswith(".sql"):
                if name.endswith(".gz"):
                    cmd = ["sh", "-c", f"zcat {str(path)} | psql {db_url}"]
                else:
                    cmd = ["psql", "-f", str(path), db_url]
            else:
                cmd = ["pg_restore", "--no-owner", "--no-acl", "--clean", "--if-exists", "-d", db_url, str(path)]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode != 0:
                logger.error("Database restore failed: %s", proc.stderr[:1000])
                return False

            logger.info("Database restored from %s", backup_path)
            return True
        except Exception as e:
            logger.error("Database restore failed: %s", e)
            return False

    def _safe_extract(self, tar: tarfile.TarFile, target_dir: Path) -> None:
        """Extract a tar archive while blocking path traversal."""
        target_dir = target_dir.resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        for member in tar.getmembers():
            # Resolve the member path and ensure it's within target_dir
            member_path = target_dir / member.name
            resolved = member_path.resolve()
            if not str(resolved).startswith(str(target_dir)):
                raise ValueError(
                    f"Path traversal blocked: {member.name} resolves outside {target_dir}"
                )
            tar.extract(member, path=target_dir)

    async def restore_storage(self, backup_path: str) -> bool:
        path = Path(backup_path)
        if not path.exists():
            logger.error("Storage backup not found: %s", backup_path)
            return False

        try:
            content_dir = Path("content")
            if content_dir.exists():
                shutil.rmtree(str(content_dir))

            with tarfile.open(path, "r:gz") as tar:
                self._safe_extract(tar, Path("."))

            logger.info("Storage restored from %s", backup_path)
            return True
        except Exception as e:
            logger.error("Storage restore failed: %s", e)
            return False
