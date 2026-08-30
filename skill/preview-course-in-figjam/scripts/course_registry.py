#!/usr/bin/env python3
"""Manage the privacy-minimal course-to-FigJam registry."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata


SCHEMA_VERSION = 1
DEFAULT_REGISTRY = Path.home() / ".codex" / "course-preview" / "registry.json"
WEEK_STATUSES = ("initialized", "in_progress", "complete", "revision_pending", "failed")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).strip().casefold()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^\w:-]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"-+", "-", normalized).strip("-:")
    if not normalized:
        raise ValueError("course key cannot be empty")
    return normalized


def empty_registry() -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "planKey": None, "courses": {}}


def read_registry(path: Path) -> dict:
    if not path.exists():
        return empty_registry()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schemaVersion") != SCHEMA_VERSION or not isinstance(data.get("courses"), dict):
        raise ValueError("unsupported or invalid registry schema")
    return data


def write_registry(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked_registry(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def find_course(data: dict, requested_key: str) -> tuple[str, dict] | tuple[None, None]:
    key = normalize_key(requested_key)
    courses = data["courses"]
    if key in courses:
        return key, courses[key]
    for canonical, course in courses.items():
        aliases = {normalize_key(alias) for alias in course.get("aliases", [])}
        if key in aliases:
            return canonical, course
    return None, None


def emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def command_lookup(args) -> int:
    data = read_registry(args.registry)
    canonical, course = find_course(data, args.course_key)
    emit({"found": course is not None, "canonicalKey": canonical, "course": course, "planKey": data.get("planKey")})
    return 0


def command_upsert(args) -> int:
    key = normalize_key(args.course_key)
    now = utc_now()
    with locked_registry(args.registry):
        data = read_registry(args.registry)
        existing = data["courses"].get(key, {})
        existing_file_key = existing.get("figmaFileKey")
        if existing_file_key and existing_file_key != args.figma_file_key and not args.allow_rebind:
            raise ValueError(
                "course is already bound to a different FigJam; use --allow-rebind only after explicit user approval"
            )
        aliases = sorted({*existing.get("aliases", []), *(args.alias or [])})
        course = {
            "displayName": args.display_name,
            "institution": args.institution,
            "courseCode": args.course_code,
            "figmaFileKey": args.figma_file_key,
            "figmaUrl": args.figma_url,
            "aliases": aliases,
            "createdAt": existing.get("createdAt", now),
            "updatedAt": now,
            "weeks": existing.get("weeks", {}),
        }
        data["courses"][key] = course
        if args.plan_key:
            data["planKey"] = args.plan_key
        write_registry(args.registry, data)
    emit({"ok": True, "canonicalKey": key, "course": course})
    return 0


def command_set_week(args) -> int:
    key = normalize_key(args.course_key)
    week_key = args.week_key.strip().upper()
    if not re.fullmatch(r"W\d{2,3}(?:-R\d+)?", week_key):
        raise ValueError("week key must look like W01 or W01-R2")
    with locked_registry(args.registry):
        data = read_registry(args.registry)
        canonical, course = find_course(data, key)
        if course is None:
            raise ValueError(f"course is not registered: {key}")
        existing = course.setdefault("weeks", {}).get(week_key, {})
        if not re.fullmatch(r"[0-9a-fA-F]{64}", args.fingerprint):
            raise ValueError("fingerprint must be a 64-character SHA-256 hex digest")
        existing_fingerprint = existing.get("fingerprint")
        if existing_fingerprint and existing_fingerprint != args.fingerprint:
            if args.status == "revision_pending":
                record = {
                    **existing,
                    "status": "revision_pending",
                    "pendingFingerprint": args.fingerprint.casefold(),
                    "updatedAt": utc_now(),
                }
                course["weeks"][week_key] = record
                course["updatedAt"] = record["updatedAt"]
                data["courses"][canonical] = course
                write_registry(args.registry, data)
                emit({"ok": True, "canonicalKey": canonical, "weekKey": week_key, "week": record})
                return 0
            if not args.allow_fingerprint_replace:
                raise ValueError(
                    "week fingerprint differs; set revision_pending first, then use a revision key or "
                    "--allow-fingerprint-replace only after explicit user approval"
                )
        record = {
            "term": args.term if args.term is not None else existing.get("term"),
            "fingerprint": args.fingerprint.casefold(),
            "sectionNodeId": args.section_node_id if args.section_node_id is not None else existing.get("sectionNodeId"),
            "pageCount": args.page_count if args.page_count is not None else existing.get("pageCount"),
            "status": args.status,
            "lastBatch": args.last_batch if args.last_batch is not None else existing.get("lastBatch", 0),
            "createdAt": existing.get("createdAt", utc_now()),
            "updatedAt": utc_now(),
        }
        course["weeks"][week_key] = record
        course["updatedAt"] = record["updatedAt"]
        data["courses"][canonical] = course
        write_registry(args.registry, data)
    emit({"ok": True, "canonicalKey": canonical, "weekKey": week_key, "week": record})
    return 0


def parser_for_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup = subparsers.add_parser("lookup")
    lookup.add_argument("--course-key", required=True)
    lookup.set_defaults(handler=command_lookup)

    upsert = subparsers.add_parser("upsert-course")
    upsert.add_argument("--course-key", required=True)
    upsert.add_argument("--display-name", required=True)
    upsert.add_argument("--figma-file-key", required=True)
    upsert.add_argument("--figma-url", required=True)
    upsert.add_argument("--institution")
    upsert.add_argument("--course-code")
    upsert.add_argument("--plan-key")
    upsert.add_argument("--alias", action="append")
    upsert.add_argument("--allow-rebind", action="store_true")
    upsert.set_defaults(handler=command_upsert)

    week = subparsers.add_parser("set-week-status")
    week.add_argument("--course-key", required=True)
    week.add_argument("--week-key", required=True)
    week.add_argument("--fingerprint", required=True)
    week.add_argument("--status", choices=WEEK_STATUSES, required=True)
    week.add_argument("--term")
    week.add_argument("--section-node-id")
    week.add_argument("--page-count", type=int)
    week.add_argument("--last-batch", type=int)
    week.add_argument("--allow-fingerprint-replace", action="store_true")
    week.set_defaults(handler=command_set_week)
    return parser


def main() -> int:
    parser = parser_for_cli()
    args = parser.parse_args()
    args.registry = args.registry.expanduser().resolve()
    try:
        return args.handler(args)
    except Exception as exc:
        print(f"course_registry: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
