#!/usr/bin/env python3
"""Dataset ingestion utility for project/workstation collections."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v"}
LABEL_EXTENSIONS = {".txt", ".json"}
GENERIC_GROUP_NAMES = {
    "annotation",
    "annotations",
    "image",
    "images",
    "label",
    "labels",
    "video",
    "videos",
}


class IngestError(Exception):
    """Raised when the ingestion config or source data is invalid."""


@dataclass
class ImportStats:
    videos: int = 0
    image_groups: int = 0
    images: int = 0
    annotation_versions: int = 0
    label_groups: int = 0
    label_files: int = 0


@dataclass
class FileCopySpec:
    source_path: Path
    target_name: str


@dataclass
class NamedFileGroup:
    group_name: str
    files: list[FileCopySpec]
    explicit_group: bool = False


@dataclass
class BatchCatalogEntry:
    batch_name: str
    aliases: set[str]


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parent / "collections"
    parser = argparse.ArgumentParser(
        description="Import a single project's dataset into collections/."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the ingestion config JSON file.",
    )
    parser.add_argument(
        "--collections-root",
        default=str(default_root),
        help="Destination collections root. Defaults to server/collections.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print the planned import without copying files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing files in the destination.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise IngestError(f"Config file does not exist: {config_path}")

    collections_root = Path(args.collections_root).resolve()
    config = load_json(config_path)
    summary = ingest_project(
        config=config,
        config_dir=config_path.parent,
        collections_root=collections_root,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestError(f"Invalid JSON in {path}: {exc}") from exc


def ingest_project(
    *,
    config: dict[str, Any],
    config_dir: Path,
    collections_root: Path,
    dry_run: bool,
    overwrite: bool,
) -> dict[str, Any]:
    project_cfg = config.get("info", config.get("project"))
    workstations = config.get("meta", config.get("workstations"))
    if not isinstance(project_cfg, dict):
        raise IngestError("Config must contain an 'info' object.")
    if not isinstance(workstations, list) or not workstations:
        raise IngestError("Config must contain a non-empty 'meta' list.")

    project_name = required_str(project_cfg, "name", alias="project")
    project_root = collections_root / project_name

    dates = [get_nested_str(ws, ["collection_meta", "date"]) for ws in workstations]
    inferred_info = infer_project_info_from_videos(
        workstations=workstations,
        config_dir=config_dir,
    )
    project_info = build_project_info(project_cfg, dates, inferred_info)

    summary: dict[str, Any] = {
        "project": project_name,
        "project_root": str(project_root),
        "dry_run": dry_run,
        "workstations": [],
    }

    if not dry_run:
        project_root.mkdir(parents=True, exist_ok=True)
        write_json(project_root / "info.json", project_info)

    seen_workstations: set[str] = set()
    reserved_versions: dict[str, set[int]] = {}
    for workstation_cfg in workstations:
        workstation_summary = ingest_workstation(
            project_name=project_name,
            project_root=project_root,
            workstation_cfg=workstation_cfg,
            config_dir=config_dir,
            dry_run=dry_run,
            overwrite=overwrite,
            seen_workstations=seen_workstations,
            reserved_versions=reserved_versions,
        )
        summary["workstations"].append(workstation_summary)

    return summary


def ingest_workstation(
    *,
    project_name: str,
    project_root: Path,
    workstation_cfg: dict[str, Any],
    config_dir: Path,
    dry_run: bool,
    overwrite: bool,
    seen_workstations: set[str],
    reserved_versions: dict[str, set[int]],
) -> dict[str, Any]:
    location_name = resolve_location_name(workstation_cfg)
    version = resolve_workstation_version(
        project_root=project_root,
        station=location_name,
        raw_version=workstation_cfg.get("version"),
        reserved_versions=reserved_versions,
    )

    workstation_name = f"{location_name}_{version}"
    if workstation_name in seen_workstations:
        raise IngestError(f"Duplicate workstation target: {workstation_name}")
    seen_workstations.add(workstation_name)

    workstation_root = project_root / workstation_name
    stats = ImportStats()
    sources = workstation_cfg.get("sources", {})
    if not isinstance(sources, dict):
        raise IngestError(f"Workstation '{workstation_name}' has invalid 'sources'.")

    if not dry_run:
        workstation_root.mkdir(parents=True, exist_ok=True)

    collection_meta_cfg = workstation_cfg.get("collection_meta", {})
    if collection_meta_cfg and not isinstance(collection_meta_cfg, dict):
        raise IngestError(f"Workstation '{workstation_name}' has invalid 'collection_meta'.")
    preferred_batch_name = string_or_empty(collection_meta_cfg.get("date"))
    frame_extraction = resolve_frame_extraction_config(
        workstation_name=workstation_name,
        workstation_cfg=workstation_cfg,
        auto_extract=False,
    )

    videos = sources.get("videos", [])
    video_batch_catalog: list[BatchCatalogEntry] = []
    video_groups: list[NamedFileGroup] = []
    if videos:
        video_groups = collect_video_file_groups(
            entries=videos,
            allowed_extensions=VIDEO_EXTENSIONS,
            preferred_batch_name=preferred_batch_name,
            config_dir=config_dir,
        )
        stats.videos = import_video_batches(
            groups=video_groups,
            destination_root=workstation_root / "video",
            dry_run=dry_run,
            overwrite=overwrite,
        )
        video_batch_catalog = build_batch_catalog(video_groups)

    images = sources.get("images", [])
    inferred_resolution = ""
    if images:
        image_groups, image_count = import_grouped_files(
            entries=images,
            allowed_extensions=IMAGE_EXTENSIONS,
            destination_root=workstation_root / "images",
            preferred_batch_name=preferred_batch_name,
            batch_catalog=video_batch_catalog,
            config_dir=config_dir,
            dry_run=dry_run,
            overwrite=overwrite,
        )
        stats.image_groups = image_groups
        stats.images = image_count
        inferred_resolution = infer_image_resolution(
            entries=images,
            config_dir=config_dir,
        )
    elif video_groups:
        frame_extraction = resolve_frame_extraction_config(
            workstation_name=workstation_name,
            workstation_cfg=workstation_cfg,
            auto_extract=True,
        )
        (
            stats.image_groups,
            stats.images,
            inferred_resolution,
        ) = extract_frames_from_videos(
            video_groups=video_groups,
            imported_video_root=workstation_root / "video",
            destination_root=workstation_root / "images",
            fps=float(frame_extraction["fps"]),
            dry_run=dry_run,
            overwrite=overwrite,
        )

    annotation_summaries = []
    annotations = sources.get("annotations", [])
    if annotations:
        if not isinstance(annotations, list):
            raise IngestError(
                f"Workstation '{workstation_name}' has invalid 'sources.annotations'."
            )
        for annotation_cfg in annotations:
            annotation_summary, version_stats = ingest_annotation_version(
                project_name=project_name,
                workstation_root=workstation_root,
                annotation_cfg=annotation_cfg,
                preferred_batch_name=preferred_batch_name,
                video_batch_catalog=video_batch_catalog,
                config_dir=config_dir,
                dry_run=dry_run,
                overwrite=overwrite,
            )
            annotation_summaries.append(annotation_summary)
            stats.annotation_versions += 1
            stats.label_groups += version_stats["label_groups"]
            stats.label_files += version_stats["label_files"]

    collection_meta = build_collection_meta(
        project_name=project_name,
        location_name=location_name,
        workstation_name=workstation_name,
        workstation_cfg=workstation_cfg,
        imported_image_count=stats.images,
        inferred_resolution=inferred_resolution,
        frame_extraction=frame_extraction,
    )

    if not dry_run:
        write_json(workstation_root / "meta.json", collection_meta)

    return {
        "workstation": workstation_name,
        "path": str(workstation_root),
        "videos": stats.videos,
        "image_groups": stats.image_groups,
        "images": stats.images,
        "annotation_versions": annotation_summaries,
        "label_groups": stats.label_groups,
        "label_files": stats.label_files,
    }


def ingest_annotation_version(
    *,
    project_name: str,
    workstation_root: Path,
    annotation_cfg: dict[str, Any],
    preferred_batch_name: str,
    video_batch_catalog: list[BatchCatalogEntry],
    config_dir: Path,
    dry_run: bool,
    overwrite: bool,
) -> tuple[dict[str, Any], dict[str, int]]:
    if not isinstance(annotation_cfg, dict):
        raise IngestError("Each annotation entry must be an object.")

    version_name = required_str(annotation_cfg, "version_name", alias="name")
    annotation_root = workstation_root / "annotations" / version_name
    labels_entries = annotation_cfg.get("labels", [])

    label_groups = 0
    label_files = 0
    if labels_entries:
        label_groups, label_files = import_grouped_files(
            entries=labels_entries,
            allowed_extensions=LABEL_EXTENSIONS,
            destination_root=annotation_root,
            preferred_batch_name=preferred_batch_name,
            batch_catalog=video_batch_catalog,
            config_dir=config_dir,
            dry_run=dry_run,
            overwrite=overwrite,
        )

    meta_cfg = annotation_cfg.get("meta", {})
    if meta_cfg and not isinstance(meta_cfg, dict):
        raise IngestError(f"Annotation '{version_name}' has invalid 'meta'.")

    annotation_meta = build_annotation_meta(
        project_name=project_name,
        version_name=version_name,
        annotation_cfg=annotation_cfg,
        imported_label_count=label_files,
    )
    label_descriptions = annotation_cfg.get("label_descriptions")

    if not dry_run:
        annotation_root.mkdir(parents=True, exist_ok=True)
        write_json(annotation_root / "meta.json", annotation_meta)
        if label_descriptions is not None:
            write_label_descriptions(annotation_root, label_descriptions)

    return (
        {
            "name": version_name,
            "path": str(annotation_root),
            "label_groups": label_groups,
            "label_files": label_files,
            "has_label_descriptions": label_descriptions is not None,
        },
        {"label_groups": label_groups, "label_files": label_files},
    )


def build_project_info(
    project_cfg: dict[str, Any],
    dates: list[str | None],
    inferred_info: dict[str, str],
) -> dict[str, Any]:
    project_name = required_str(project_cfg, "name", alias="project")
    normalized_dates = sorted(date for date in dates if date)
    configured_device = string_or_empty(project_cfg.get("device"))
    configured_start_date = string_or_empty(project_cfg.get("start_date"))
    configured_end_date = string_or_empty(project_cfg.get("end_date"))
    return {
        "project": project_name,
        "type": project_cfg.get("type", ""),
        "device": configured_device or inferred_info.get("device", ""),
        "start_date": configured_start_date
        or inferred_info.get("start_date", "")
        or (normalized_dates[0] if normalized_dates else ""),
        "end_date": configured_end_date
        or inferred_info.get("end_date", "")
        or (normalized_dates[-1] if normalized_dates else ""),
        "status": project_cfg.get("status", "进行中"),
        "notes": project_cfg.get("notes", ""),
        "doc_link": project_cfg.get("doc_link", ""),
    }


def resolve_frame_extraction_config(
    *,
    workstation_name: str,
    workstation_cfg: dict[str, Any],
    auto_extract: bool,
) -> dict[str, Any] | None:
    raw = workstation_cfg.get("video_frame_extraction")
    if raw is None:
        if not auto_extract:
            return None
        raw = {}
    if not isinstance(raw, dict):
        raise IngestError(
            f"Workstation '{workstation_name}' has invalid 'video_frame_extraction'."
        )

    raw_fps = raw.get("fps", 3)
    if isinstance(raw_fps, bool) or not isinstance(raw_fps, (int, float)) or raw_fps <= 0:
        raise IngestError(
            f"Workstation '{workstation_name}' has invalid frame extraction fps: {raw_fps!r}"
        )

    notes = raw.get("notes", "")
    if auto_extract and not notes:
        notes = "未提供图片，已根据视频自动抽帧生成。"

    return {
        "source": raw.get("source", "视频抽帧"),
        "fps": float(raw_fps),
        "deduplicate": bool(raw.get("deduplicate", False)),
        "notes": notes,
    }


def build_collection_meta(
    *,
    project_name: str,
    location_name: str,
    workstation_name: str,
    workstation_cfg: dict[str, Any],
    imported_image_count: int,
    inferred_resolution: str,
    frame_extraction: dict[str, Any] | None,
) -> dict[str, Any]:
    meta_cfg = workstation_cfg.get("collection_meta", {})
    if meta_cfg and not isinstance(meta_cfg, dict):
        raise IngestError(f"Workstation '{workstation_name}' has invalid 'collection_meta'.")

    raw_count = meta_cfg.get("count")
    if isinstance(raw_count, bool) or not isinstance(raw_count, int) or raw_count <= 0:
        count = imported_image_count
    else:
        count = raw_count
    configured_resolution = meta_cfg.get("resolution", "")
    if isinstance(configured_resolution, str):
        configured_resolution = configured_resolution.strip()
    else:
        configured_resolution = ""
    raw_location = (
        string_or_empty(workstation_cfg.get("location"))
        or (string_or_empty(meta_cfg.get("location")) if isinstance(meta_cfg, dict) else "")
        or location_name
    )
    result = {
        "project": project_name,
        "location": normalize_location_name(raw_location),
        "date": meta_cfg.get("date", ""),
        "device": meta_cfg.get("device", ""),
        "resolution": configured_resolution or inferred_resolution,
        "count": count,
        "collector": meta_cfg.get("collector", ""),
        "notes": meta_cfg.get("notes", ""),
    }

    if frame_extraction is not None:
        result["video_frame_extraction"] = frame_extraction

    return result


def build_annotation_meta(
    *,
    project_name: str,
    version_name: str,
    annotation_cfg: dict[str, Any],
    imported_label_count: int,
) -> dict[str, Any]:
    meta_cfg = annotation_cfg.get("meta", {})
    create_time = meta_cfg.get("create_time", now_string())
    update_time = meta_cfg.get("update_time", create_time)

    return {
        "project": project_name,
        "type": meta_cfg.get("type", ""),
        "method": meta_cfg.get("method", ""),
        "used_model": meta_cfg.get("used_model", ""),
        "parent": meta_cfg.get("parent", ""),
        "classes": meta_cfg.get("classes", []),
        "annotated_count": meta_cfg.get("annotated_count", imported_label_count),
        "reviewed": meta_cfg.get("reviewed", False),
        "reviewer": meta_cfg.get("reviewer", ""),
        "difficulty_type": meta_cfg.get("difficulty_type", ""),
        "create_time": create_time,
        "update_time": update_time,
        "notes": meta_cfg.get("notes", ""),
        "version": version_name,
    }


def import_video_batches(
    *,
    groups: list[NamedFileGroup],
    destination_root: Path,
    dry_run: bool,
    overwrite: bool,
) -> int:
    if not dry_run:
        destination_root.mkdir(parents=True, exist_ok=True)

    total = 0
    for group in groups:
        for file_spec in group.files:
            copy_file(
                file_spec.source_path,
                destination_root / file_spec.target_name,
                dry_run=dry_run,
                overwrite=overwrite,
            )
            total += 1

    return total


def import_grouped_files(
    *,
    entries: list[Any],
    allowed_extensions: set[str],
    destination_root: Path,
    preferred_batch_name: str,
    batch_catalog: list[BatchCatalogEntry],
    config_dir: Path,
    dry_run: bool,
    overwrite: bool,
) -> tuple[int, int]:
    groups = collect_named_file_groups(
        entries=entries,
        allowed_extensions=allowed_extensions,
        config_dir=config_dir,
    )
    if not dry_run:
        destination_root.mkdir(parents=True, exist_ok=True)

    destination_groups: set[str] = set()
    file_count = 0
    for group in groups:
        target_group = resolve_target_batch_name(
            group=group,
            preferred_batch_name=preferred_batch_name,
            batch_catalog=batch_catalog,
        )
        target_root = destination_root / target_group if target_group else destination_root
        destination_groups.add(target_group)
        for file_spec in group.files:
            copy_file(
                file_spec.source_path,
                target_root / file_spec.target_name,
                dry_run=dry_run,
                overwrite=overwrite,
            )
            file_count += 1

    return len(destination_groups), file_count


def copy_directory_files(
    *,
    source_dir: Path,
    destination_dir: Path,
    allowed_extensions: set[str],
    recursive: bool,
    dry_run: bool,
    overwrite: bool,
) -> int:
    files = list_files(source_dir, allowed_extensions, recursive=recursive)
    if not files:
        raise IngestError(
            f"Directory '{source_dir}' does not contain supported files: {sorted(allowed_extensions)}"
        )
    for file_path in files:
        target_path = destination_dir / file_path.name
        copy_file(file_path, target_path, dry_run=dry_run, overwrite=overwrite)
    return len(files)


def extract_frames_from_videos(
    *,
    video_groups: list[NamedFileGroup],
    imported_video_root: Path,
    destination_root: Path,
    fps: float,
    dry_run: bool,
    overwrite: bool,
) -> tuple[int, int, str]:
    ensure_ffmpeg_available()

    if dry_run:
        return len(video_groups), 0, ""

    destination_root.mkdir(parents=True, exist_ok=True)
    image_groups = 0
    image_count = 0
    inferred_resolution = ""

    for group in video_groups:
        for file_spec in group.files:
            imported_video_path = imported_video_root / file_spec.target_name
            destination_dir = destination_root / Path(file_spec.target_name).stem
            if destination_dir.exists():
                if not overwrite:
                    raise IngestError(
                        f"Target already exists: {destination_dir}. Re-run with --overwrite to replace it."
                    )
                shutil.rmtree(destination_dir)
            destination_dir.mkdir(parents=True, exist_ok=True)

            group_count = extract_frames_from_video(
                video_path=imported_video_path,
                destination_dir=destination_dir,
                fps=fps,
            )
            if group_count:
                image_groups += 1
                image_count += group_count
                if not inferred_resolution:
                    inferred_resolution = infer_resolution_from_directory(destination_dir)

    return image_groups, image_count, inferred_resolution


def extract_frames_from_video(*, video_path: Path, destination_dir: Path, fps: float) -> int:
    output_pattern = destination_dir / "%06d.png"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
        str(output_pattern),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise IngestError(
            f"ffmpeg frame extraction failed for {video_path}: {completed.stderr.strip() or completed.stdout.strip()}"
        )

    created = sorted(destination_dir.glob("*.png"))
    if not created:
        raise IngestError(f"No frames were generated from video: {video_path}")
    return len(created)


def infer_resolution_from_directory(directory: Path) -> str:
    for image_path in sorted(directory.glob("*.png")):
        size = read_image_size(image_path)
        if size is None:
            continue
        width, height = size
        return f"{width}x{height}"
    return ""


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise IngestError(
            "Frame extraction requires ffmpeg, but it was not found in PATH."
        )


def collect_video_file_groups(
    *,
    entries: list[Any],
    allowed_extensions: set[str],
    preferred_batch_name: str,
    config_dir: Path,
) -> list[NamedFileGroup]:
    if not isinstance(entries, list):
        raise IngestError("Source entries must be a list.")

    groups: list[NamedFileGroup] = []
    used_batch_names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngestError("Each source entry must be an object.")

        source_path = resolve_input_path(entry["path"], config_dir)
        recursive = bool(entry.get("recursive", False))
        explicit_target_group = string_or_empty(entry.get("target_group"))

        if source_path.is_file():
            if source_path.suffix.lower() not in allowed_extensions:
                continue
            batch_name = resolve_video_batch_name(
                source_path=source_path,
                preferred_batch_name=preferred_batch_name,
                explicit_target_group=explicit_target_group,
                used_batch_names=used_batch_names,
            )
            groups.append(
                NamedFileGroup(
                    group_name=batch_name,
                    files=[
                        FileCopySpec(
                            source_path=source_path,
                            target_name=f"{batch_name}{source_path.suffix.lower()}",
                        )
                    ],
                    explicit_group=bool(explicit_target_group),
                )
            )
            continue

        if not source_path.is_dir():
            raise IngestError(f"Source path does not exist: {source_path}")

        files = list_files(source_path, allowed_extensions, recursive=recursive)
        for file_path in files:
            batch_name = resolve_video_batch_name(
                source_path=file_path,
                preferred_batch_name=preferred_batch_name,
                explicit_target_group=explicit_target_group,
                used_batch_names=used_batch_names,
            )
            groups.append(
                NamedFileGroup(
                    group_name=batch_name,
                    files=[
                        FileCopySpec(
                            source_path=file_path,
                            target_name=f"{batch_name}{file_path.suffix.lower()}",
                        )
                    ],
                    explicit_group=bool(explicit_target_group),
                )
            )
    return groups


def collect_named_file_groups(
    *,
    entries: list[Any],
    allowed_extensions: set[str],
    config_dir: Path,
) -> list[NamedFileGroup]:
    if not isinstance(entries, list):
        raise IngestError("Grouped source entries must be a list.")

    groups: list[NamedFileGroup] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngestError("Each grouped source entry must be an object.")

        source_path = resolve_input_path(entry["path"], config_dir)
        recursive = bool(entry.get("recursive", False))
        treat_children_as_groups = bool(entry.get("treat_children_as_groups", False))
        explicit_target_group = string_or_empty(entry.get("target_group"))

        if source_path.is_file():
            if source_path.suffix.lower() not in allowed_extensions:
                continue
            group_name = explicit_target_group or source_path.stem
            groups.append(
                NamedFileGroup(
                    group_name=group_name,
                    files=[
                        FileCopySpec(
                            source_path=source_path,
                            target_name=entry.get("target_name", source_path.name),
                        )
                    ],
                    explicit_group=bool(explicit_target_group),
                )
            )
            continue

        if not source_path.is_dir():
            raise IngestError(f"Source path does not exist: {source_path}")

        if treat_children_as_groups:
            child_dirs = sorted(path for path in source_path.iterdir() if path.is_dir())
            if not child_dirs:
                raise IngestError(
                    f"Directory '{source_path}' has no child directories to import as groups."
                )
            for child_dir in child_dirs:
                files = list_files(child_dir, allowed_extensions, recursive=recursive)
                if not files:
                    raise IngestError(
                        f"Directory '{child_dir}' does not contain supported files: {sorted(allowed_extensions)}"
                    )
                groups.append(
                    NamedFileGroup(
                        group_name=child_dir.name,
                        files=[FileCopySpec(source_path=file_path, target_name=file_path.name) for file_path in files],
                    )
                )
            continue

        files = list_files(source_path, allowed_extensions, recursive=recursive)
        if not files:
            raise IngestError(
                f"Directory '{source_path}' does not contain supported files: {sorted(allowed_extensions)}"
            )
        groups.append(
            NamedFileGroup(
                group_name=explicit_target_group or source_path.name,
                files=[FileCopySpec(source_path=file_path, target_name=file_path.name) for file_path in files],
                explicit_group=bool(explicit_target_group),
            )
        )

    return groups


def build_batch_catalog(groups: list[NamedFileGroup]) -> list[BatchCatalogEntry]:
    catalog: list[BatchCatalogEntry] = []
    for group in groups:
        aliases = {group.group_name}
        aliases.update(build_batch_date_aliases(group.group_name))
        for file_spec in group.files:
            aliases.add(file_spec.source_path.stem)
            parsed_batch = parse_video_batch_name(file_spec.source_path.stem)
            if parsed_batch:
                aliases.add(parsed_batch)
                aliases.update(build_batch_date_aliases(parsed_batch))
        catalog.append(BatchCatalogEntry(batch_name=group.group_name, aliases=aliases))
    return catalog


def resolve_target_batch_name(
    *, group: NamedFileGroup, preferred_batch_name: str, batch_catalog: list[BatchCatalogEntry]
) -> str:
    if group.explicit_group:
        if group.files:
            return build_batch_name_from_hint(preferred_batch_name=group.group_name, source_path=group.files[0].source_path)
        return group.group_name

    if batch_catalog:
        matched = match_batch_catalog(group.group_name, batch_catalog)
        if matched:
            return matched

        for file_spec in group.files:
            for hint in iter_batch_hints(file_spec.source_path):
                matched = match_batch_catalog(hint, batch_catalog)
                if matched:
                    return matched

        if len(batch_catalog) == 1 and normalize_group_name(group.group_name) in GENERIC_GROUP_NAMES:
            return batch_catalog[0].batch_name

    if preferred_batch_name and group.files:
        return build_batch_name_from_hint(
            preferred_batch_name=preferred_batch_name,
            source_path=group.files[0].source_path,
        )

    normalized = normalize_group_name(group.group_name)
    if normalized in GENERIC_GROUP_NAMES:
        return ""

    if group.files:
        parsed_group_batch = parse_video_batch_name(
            group.group_name,
            fallback_time=read_path_timestamp(group.files[0].source_path),
        )
        if parsed_group_batch:
            return parsed_group_batch

    return group.group_name


def match_batch_catalog(
    candidate: str, batch_catalog: list[BatchCatalogEntry]
) -> str | None:
    normalized_candidate = normalize_group_name(candidate)
    if not normalized_candidate:
        return None

    exact_matches = [
        entry.batch_name
        for entry in batch_catalog
        if normalized_candidate in {normalize_group_name(alias) for alias in entry.aliases}
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]

    prefix_matches = []
    for entry in batch_catalog:
        normalized_aliases = {normalize_group_name(alias) for alias in entry.aliases}
        if any(
            alias.startswith(normalized_candidate) or normalized_candidate.startswith(alias)
            for alias in normalized_aliases
            if alias
        ):
            prefix_matches.append(entry.batch_name)
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    return None


def iter_batch_hints(source_path: Path) -> list[str]:
    hints = [source_path.stem]
    parent = source_path.parent
    for _ in range(2):
        if parent == parent.parent:
            break
        hints.append(parent.name)
        parent = parent.parent
    return hints


def derive_video_batch_name(source_path: Path) -> str:
    parsed_batch = parse_video_batch_name(
        source_path.stem,
        fallback_time=read_path_timestamp(source_path),
    )
    if parsed_batch:
        return parsed_batch
    return derive_batch_name_from_file_time(source_path)


def parse_video_batch_name(name: str, fallback_time: datetime | None = None) -> str | None:
    precise_timestamp = parse_precise_timestamp(name)
    if precise_timestamp is not None:
        return precise_timestamp.strftime("%Y%m%d_%H%M%S")

    date_only = parse_date_only(name)
    if date_only is not None:
        if fallback_time is None:
            fallback_time = datetime.now().replace(microsecond=0)
        combined = datetime.combine(date_only.date(), fallback_time.time().replace(microsecond=0))
        return combined.strftime("%Y%m%d_%H%M%S")
    return None


def parse_date_only(raw_date: str) -> datetime | None:
    dashed_match = re.search(r"(?P<date>\d{4}-\d{2}-\d{2})", raw_date)
    if dashed_match:
        raw_date = dashed_match.group("date")
    else:
        compact_match = re.search(r"(?P<date>\d{8})", raw_date)
        if not compact_match:
            return None
        raw_date = compact_match.group("date")

    date_formats = ("%Y-%m-%d", "%Y%m%d")
    for date_format in date_formats:
        try:
            return datetime.strptime(raw_date, date_format)
        except ValueError:
            continue
    return None


def parse_precise_timestamp(raw_value: str) -> datetime | None:
    patterns = [
        r"(?P<year>\d{4})[-_](?P<month>\d{2})[-_](?P<day>\d{2})[-_](?P<hour>\d{2})[-_](?P<minute>\d{2})[-_](?P<second>\d{2})",
        r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})[_-]?(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_value)
        if not match:
            continue
        try:
            return datetime(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
                int(match.group("hour")),
                int(match.group("minute")),
                int(match.group("second")),
            )
        except ValueError:
            continue
    return None


def derive_batch_name_from_file_time(source_path: Path) -> str:
    return read_path_timestamp(source_path).strftime("%Y%m%d_%H%M%S")


def read_path_timestamp(source_path: Path) -> datetime:
    stat_result = source_path.stat()
    timestamp = getattr(stat_result, "st_birthtime", None) or stat_result.st_mtime
    return datetime.fromtimestamp(timestamp).replace(microsecond=0)


def build_batch_date_aliases(batch_name: str) -> set[str]:
    match = re.fullmatch(r"(?P<date>\d{8})_(?P<time>\d{6})", batch_name)
    if not match:
        return set()
    raw_date = match.group("date")
    return {raw_date, f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"}


def normalize_preferred_batch_name(raw_batch_name: str) -> str:
    if not raw_batch_name:
        return ""
    parsed_batch = parse_video_batch_name(raw_batch_name)
    return parsed_batch or raw_batch_name


def resolve_video_batch_name(
    *,
    source_path: Path,
    preferred_batch_name: str,
    explicit_target_group: str,
    used_batch_names: set[str],
) -> str:
    if explicit_target_group:
        base_name = build_batch_name_from_hint(
            preferred_batch_name=explicit_target_group,
            source_path=source_path,
        )
    elif preferred_batch_name:
        base_name = build_batch_name_from_hint(
            preferred_batch_name=preferred_batch_name,
            source_path=source_path,
        )
    else:
        base_name = derive_video_batch_name(source_path)
    unique_name = ensure_unique_batch_name(base_name, used_batch_names)
    used_batch_names.add(unique_name)
    return unique_name


def build_batch_name_from_hint(*, preferred_batch_name: str, source_path: Path) -> str:
    parsed_batch = parse_video_batch_name(
        preferred_batch_name,
        fallback_time=read_path_timestamp(source_path),
    )
    return parsed_batch or preferred_batch_name


def ensure_unique_batch_name(batch_name: str, used_batch_names: set[str]) -> str:
    if batch_name not in used_batch_names:
        return batch_name

    timestamp_match = re.fullmatch(r"(?P<date>\d{8})_(?P<time>\d{6})", batch_name)
    if timestamp_match:
        current = datetime.strptime(batch_name, "%Y%m%d_%H%M%S")
        while True:
            current = current.replace(microsecond=0) + timedelta(seconds=1)
            candidate = current.strftime("%Y%m%d_%H%M%S")
            if candidate not in used_batch_names:
                return candidate

    index = 1
    while True:
        candidate = f"{batch_name}_{index:02d}"
        if candidate not in used_batch_names:
            return candidate
        index += 1


def normalize_location_name(raw_location: str) -> str:
    location = raw_location.strip()
    if location.startswith("工位"):
        suffix = location[2:].strip().replace(" ", "")
        return f"workstation{suffix}" if suffix else "workstation"
    return location


def normalize_group_name(name: str) -> str:
    return name.strip().lower()


def infer_image_resolution(*, entries: list[Any], config_dir: Path) -> str:
    for image_path in iter_grouped_source_files(
        entries=entries,
        allowed_extensions=IMAGE_EXTENSIONS,
        config_dir=config_dir,
    ):
        size = read_image_size(image_path)
        if size is None:
            continue
        width, height = size
        return f"{width}x{height}"
    return ""


def infer_project_info_from_videos(
    *, workstations: list[dict[str, Any]], config_dir: Path
) -> dict[str, str]:
    devices: set[str] = set()
    dates: list[str] = []

    for workstation_cfg in workstations:
        if not isinstance(workstation_cfg, dict):
            raise IngestError("Each meta entry must be an object.")
        sources = workstation_cfg.get("sources", {})
        if not isinstance(sources, dict):
            raise IngestError("Each meta entry must contain an object 'sources'.")
        videos = sources.get("videos", [])
        if not isinstance(videos, list):
            raise IngestError("Each 'sources.videos' entry must be a list.")

        for video_path in iter_flat_source_files(
            entries=videos,
            allowed_extensions=VIDEO_EXTENSIONS,
            config_dir=config_dir,
        ):
            parsed = parse_device_and_date_from_name(video_path.stem)
            if parsed is None:
                continue
            device, date = parsed
            if device:
                devices.add(device)
            if date:
                dates.append(date)

    inferred: dict[str, str] = {}
    if devices:
        inferred["device"] = ",".join(sorted(devices))
    if dates:
        sorted_dates = sorted(dates)
        inferred["start_date"] = sorted_dates[0]
        inferred["end_date"] = sorted_dates[-1]
    return inferred


def parse_device_and_date_from_name(name: str) -> tuple[str, str] | None:
    match = re.search(r"^(?P<device>.+?)[_-](?P<date>\d{4}-\d{2}-\d{2})(?:[_-]|$)", name)
    if not match:
        return None
    return match.group("device"), match.group("date")


def resolve_workstation_version(
    *,
    project_root: Path,
    station: str,
    raw_version: Any,
    reserved_versions: dict[str, set[int]],
) -> int:
    if raw_version is not None and raw_version != "":
        version = normalize_version(raw_version, station)
        reserved_versions.setdefault(station, set()).add(version)
        return version

    used_versions = reserved_versions.setdefault(station, set())
    used_versions.update(discover_existing_versions(project_root, station))

    version = 0
    while version in used_versions:
        version += 1
    used_versions.add(version)
    return version


def normalize_version(raw_version: Any, station: str) -> int:
    if isinstance(raw_version, bool):
        raise IngestError(f"Workstation '{station}' has invalid boolean version.")
    if isinstance(raw_version, int):
        return raw_version
    if isinstance(raw_version, str) and raw_version.strip().isdigit():
        return int(raw_version.strip())
    raise IngestError(f"Workstation '{station}' has invalid version: {raw_version!r}")


def resolve_location_name(workstation_cfg: dict[str, Any]) -> str:
    direct_location = string_or_empty(workstation_cfg.get("location"))
    if direct_location:
        return normalize_location_name(direct_location)

    collection_meta = workstation_cfg.get("collection_meta", {})
    if collection_meta and not isinstance(collection_meta, dict):
        raise IngestError("Each meta entry has invalid 'collection_meta'.")
    nested_location = string_or_empty(collection_meta.get("location")) if isinstance(collection_meta, dict) else ""
    if nested_location:
        return normalize_location_name(nested_location)

    return normalize_location_name(required_str(workstation_cfg, "station", alias="name"))


def discover_existing_versions(project_root: Path, station: str) -> set[int]:
    if not project_root.exists():
        return set()

    prefix = f"{station}_"
    versions: set[int] = set()
    for child in project_root.iterdir():
        if not child.is_dir() or not child.name.startswith(prefix):
            continue
        suffix = child.name[len(prefix) :]
        if suffix.isdigit():
            versions.add(int(suffix))
    return versions


def iter_grouped_source_files(
    *,
    entries: list[Any],
    allowed_extensions: set[str],
    config_dir: Path,
) -> list[Path]:
    collected: list[Path] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngestError("Each grouped source entry must be an object.")

        source_path = resolve_input_path(entry["path"], config_dir)
        recursive = bool(entry.get("recursive", False))
        treat_children_as_groups = bool(entry.get("treat_children_as_groups", False))

        if source_path.is_file():
            if source_path.suffix.lower() in allowed_extensions:
                collected.append(source_path)
            continue

        if not source_path.is_dir():
            raise IngestError(f"Source path does not exist: {source_path}")

        if treat_children_as_groups:
            child_dirs = sorted(path for path in source_path.iterdir() if path.is_dir())
            for child_dir in child_dirs:
                files = list_files(child_dir, allowed_extensions, recursive=recursive)
                collected.extend(files)
            continue

        files = list_files(source_path, allowed_extensions, recursive=recursive)
        collected.extend(files)

    return collected


def iter_flat_source_files(
    *,
    entries: list[Any],
    allowed_extensions: set[str],
    config_dir: Path,
) -> list[Path]:
    collected: list[Path] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise IngestError("Each source entry must be an object.")

        source_path = resolve_input_path(entry["path"], config_dir)
        recursive = bool(entry.get("recursive", False))
        if source_path.is_file():
            if source_path.suffix.lower() in allowed_extensions:
                collected.append(source_path)
            continue
        if not source_path.is_dir():
            raise IngestError(f"Source path does not exist: {source_path}")
        collected.extend(list_files(source_path, allowed_extensions, recursive=recursive))
    return collected


def list_files(source_dir: Path, allowed_extensions: set[str], recursive: bool) -> list[Path]:
    paths = source_dir.rglob("*") if recursive else source_dir.iterdir()
    files = [
        path
        for path in paths
        if path.is_file() and path.suffix.lower() in allowed_extensions
    ]
    return sorted(files)


def copy_file(source_path: Path, target_path: Path, *, dry_run: bool, overwrite: bool) -> None:
    if target_path.exists() and not overwrite:
        raise IngestError(
            f"Target already exists: {target_path}. Re-run with --overwrite to replace it."
        )
    if dry_run:
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


def resolve_input_path(raw_path: str, config_dir: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (config_dir / path).resolve()
    else:
        path = path.resolve()
    if not path.exists():
        raise IngestError(f"Source path does not exist: {path}")
    return path


def read_image_size(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return read_png_size(path)
    if suffix in {".jpg", ".jpeg"}:
        return read_jpeg_size(path)
    if suffix == ".bmp":
        return read_bmp_size(path)
    if suffix == ".webp":
        return read_webp_size(path)
    return None


def read_png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        header = fh.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def read_jpeg_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None

        while True:
            marker_prefix = fh.read(1)
            if not marker_prefix:
                return None
            if marker_prefix != b"\xff":
                continue

            marker_type = fh.read(1)
            while marker_type == b"\xff":
                marker_type = fh.read(1)
            if not marker_type:
                return None

            marker = marker_type[0]
            if marker in {0xD8, 0xD9}:
                continue

            segment_length_bytes = fh.read(2)
            if len(segment_length_bytes) != 2:
                return None
            segment_length = struct.unpack(">H", segment_length_bytes)[0]
            if segment_length < 2:
                return None

            if marker in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                data = fh.read(segment_length - 2)
                if len(data) < 5:
                    return None
                height, width = struct.unpack(">HH", data[1:5])
                return width, height

            fh.seek(segment_length - 2, 1)


def read_bmp_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        header = fh.read(26)
    if len(header) < 26 or header[:2] != b"BM":
        return None
    width = struct.unpack("<I", header[18:22])[0]
    height = struct.unpack("<I", header[22:26])[0]
    return width, height


def read_webp_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        header = fh.read(64)
    if len(header) < 16 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        return None

    chunk = header[12:16]
    if chunk == b"VP8X" and len(header) >= 30:
        width_minus_one = int.from_bytes(header[24:27], "little")
        height_minus_one = int.from_bytes(header[27:30], "little")
        return width_minus_one + 1, height_minus_one + 1
    if chunk == b"VP8 " and len(header) >= 30 and header[20:23] == b"\x9d\x01\x2a":
        width = struct.unpack("<H", header[23:25])[0] & 0x3FFF
        height = struct.unpack("<H", header[25:27])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L" and len(header) >= 25:
        bits = int.from_bytes(header[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None


def required_str(payload: dict[str, Any], key: str, alias: str | None = None) -> str:
    value = payload.get(key)
    if not value and alias:
        value = payload.get(alias)
    if not isinstance(value, str) or not value.strip():
        alias_hint = f" or '{alias}'" if alias else ""
        raise IngestError(f"Missing required string field '{key}'{alias_hint}.")
    return value.strip()


def string_or_empty(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def get_nested_str(payload: dict[str, Any], keys: list[str]) -> str | None:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) and current else None


def now_string() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_label_descriptions(annotation_root: Path, payload: Any) -> None:
    path = annotation_root / "label_descriptions.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IngestError as exc:
        print(f"[ingest-error] {exc}")
        raise SystemExit(1)
