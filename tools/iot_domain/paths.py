"""Canonical path rules and deterministic content enumeration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from .layers import Layer, layer_by_slug


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_GLOB = "docs/*/papers/*.md"


class ContentPathError(ValueError):
    """Path failure that can be promoted to a structured content issue."""

    def __init__(self, code: str, location: str, message: str) -> None:
        self.code = code
        self.location = location
        self.message = message
        super().__init__(message)


def _root(repo_root: Path | None) -> Path:
    candidate = REPO_ROOT if repo_root is None else Path(repo_root)
    return Path(os.path.abspath(candidate))


def _absolute_path(path: Path, root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return Path(os.path.abspath(candidate))


def display_path(path: Path, *, repo_root: Path | None = None) -> str:
    lexical_root = _root(repo_root)
    candidate = _absolute_path(path, lexical_root)
    try:
        return candidate.relative_to(lexical_root).as_posix()
    except ValueError:
        root = lexical_root.resolve()
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, RuntimeError):
            return candidate.as_posix()
        try:
            return resolved.relative_to(root).as_posix()
        except ValueError:
            return candidate.as_posix()


def content_identity(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> tuple[Layer, str]:
    """Return the registered layer and ID encoded by a canonical content path."""

    root = _root(repo_root)
    candidate = _absolute_path(path, root)
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        raise ContentPathError(
            "INVALID_CONTENT_PATH",
            "path",
            "content file must live inside the repository",
        ) from None

    try:
        resolved_root = root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
    except (OSError, RuntimeError):
        raise ContentPathError(
            "INVALID_CONTENT_PATH",
            "path",
            "content file path cannot be resolved safely",
        ) from None
    try:
        resolved_relative = resolved_candidate.relative_to(resolved_root)
    except ValueError:
        raise ContentPathError(
            "INVALID_CONTENT_PATH",
            "path",
            "content file must live inside the repository",
        ) from None
    if resolved_relative != relative:
        raise ContentPathError(
            "INVALID_CONTENT_PATH",
            "path",
            "content file path must not traverse symlinks",
        )

    parts = relative.parts
    if (
        len(parts) != 4
        or parts[0] != "docs"
        or parts[2] != "papers"
        or candidate.suffix != ".md"
        or not candidate.stem
    ):
        raise ContentPathError(
            "INVALID_CONTENT_PATH",
            "path",
            "content file must live under docs/<layer>/papers/<id>.md",
        )

    try:
        layer = layer_by_slug(parts[1])
    except ValueError:
        raise ContentPathError(
            "UNKNOWN_LAYER",
            "path",
            f"unknown layer slug: {parts[1]}",
        ) from None
    return layer, candidate.stem


def iter_content_paths(*, repo_root: Path | None = None) -> Iterator[Path]:
    """Yield every canonical content candidate in repository-relative order."""

    root = _root(repo_root)
    paths = sorted(
        root.glob(CONTENT_GLOB),
        key=lambda item: item.relative_to(root).as_posix(),
    )
    yield from paths
