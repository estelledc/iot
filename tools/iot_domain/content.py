"""Byte-preserving parser for canonical IoT content documents."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

import yaml
from yaml.constructor import ConstructorError
from yaml.resolver import BaseResolver

from .layers import Layer
from .paths import (
    REPO_ROOT,
    ContentPathError,
    content_identity,
    display_path,
    iter_content_paths,
)


H1_RE = re.compile(r"^#(?P<rest>(?:[ \t]+.*|[ \t]*))$")
CLOSING_ATX_RE = re.compile(r"[ \t]+#+[ \t]*$")
FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class ContentIssue:
    code: str
    path: str
    location: str
    message: str

    def render(self) -> str:
        suffix = f"::{self.location}" if self.location else ""
        return f"{self.path}{suffix}: {self.message}"


class ContentError(ValueError):
    """A single structured content parsing or invariant failure."""

    def __init__(self, issue: ContentIssue) -> None:
        self.issue = issue
        # Keep the legacy catalog error text stable while exposing location and
        # code separately through ``issue``.
        super().__init__(f"{issue.path}: {issue.message}")


@dataclass(frozen=True)
class MarkdownParts:
    frontmatter: dict[str, Any]
    raw_frontmatter_bytes: bytes
    body_bytes: bytes
    body_h1: str | None


@dataclass(frozen=True)
class ContentDocument:
    path: Path
    repo_relative_path: str
    layer: Layer
    content_id: str
    frontmatter: dict[str, Any]
    raw_frontmatter_bytes: bytes
    body_bytes: bytes
    body_sha256: str
    frontmatter_title: str | None
    body_h1: str | None


@dataclass(frozen=True)
class _FrontmatterBounds:
    opening_end: int
    closing_start: int
    closing_end: int


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from None
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _error(code: str, path: str, location: str, message: str) -> ContentError:
    return ContentError(ContentIssue(code, path, location, message))


def _validate_utf8(raw: bytes, *, path: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _error(
            "INVALID_UTF8",
            path,
            f"byte {exc.start}",
            "content must be valid UTF-8",
        ) from None


def _is_delimiter(line: bytes) -> bool:
    return line.rstrip(b"\r\n") == b"---"


def _frontmatter_bounds(
    raw: bytes,
    *,
    path: str,
    required: bool,
) -> _FrontmatterBounds | None:
    lines = raw.splitlines(keepends=True)
    if not lines or not _is_delimiter(lines[0]):
        if required:
            raise _error(
                "MISSING_FRONTMATTER_OPEN",
                path,
                "line 1",
                "missing opening YAML frontmatter delimiter",
            )
        return None

    offset = len(lines[0])
    for line in lines[1:]:
        start = offset
        offset += len(line)
        if _is_delimiter(line):
            return _FrontmatterBounds(len(lines[0]), start, offset)
    raise _error(
        "MISSING_FRONTMATTER_CLOSE",
        path,
        "line 1",
        "missing closing YAML frontmatter delimiter",
    )


def _normalize_yaml(value: Any, active: set[int] | None = None) -> Any:
    if active is None:
        active = set()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        identity = id(value)
        if identity in active:
            raise ValueError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            return {key: _normalize_yaml(item, active) for key, item in value.items()}
        finally:
            active.remove(identity)
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            raise ValueError("recursive YAML aliases are not supported")
        active.add(identity)
        try:
            return [_normalize_yaml(item, active) for item in value]
        finally:
            active.remove(identity)
    return value


def _strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    cursor = 0
    inline_ticks: int | None = None
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                return "".join(visible), True
            cursor = end + 3
            in_comment = False
            continue
        if line.startswith("<!--", cursor) and inline_ticks is None:
            cursor += 4
            in_comment = True
            continue
        if line[cursor] == "`":
            end = cursor + 1
            while end < len(line) and line[end] == "`":
                end += 1
            run = end - cursor
            if inline_ticks is None:
                inline_ticks = run
            elif run == inline_ticks:
                inline_ticks = None
            visible.append(line[cursor:end])
            cursor = end
            continue
        visible.append(line[cursor])
        cursor += 1
    return "".join(visible), in_comment


def first_body_h1(body: bytes, *, path: str = "<memory>") -> str | None:
    text = _validate_utf8(body, path=path)
    opened: tuple[str, int] | None = None
    in_comment = False
    for raw_line in text.splitlines():
        if opened is not None:
            fence = FENCE_RE.match(raw_line)
            if fence:
                marker = fence.group("fence")
                info = fence.group("info").strip()
                if marker[0] == opened[0] and len(marker) >= opened[1] and not info:
                    opened = None
            continue
        line, in_comment = _strip_html_comments(raw_line, in_comment)
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group("fence")
            opened = (marker[0], len(marker))
            continue
        match = H1_RE.match(line)
        if match:
            title = CLOSING_ATX_RE.sub("", match.group("rest"))
            return title.strip()
    return None


def canonical_body_bytes(raw: bytes, *, path: str = "<memory>") -> bytes:
    """Remove only the first complete YAML prefix without normalizing bytes."""

    _validate_utf8(raw, path=path)
    bounds = _frontmatter_bounds(raw, path=path, required=False)
    if bounds is None:
        return raw
    return raw[bounds.closing_end :]


def parse_frontmatter_bytes(raw: bytes, *, path: str) -> MarkdownParts:
    """Parse one frontmatter block while retaining its exact byte boundaries."""

    _validate_utf8(raw, path=path)
    bounds = _frontmatter_bounds(raw, path=path, required=True)
    assert bounds is not None
    yaml_bytes = raw[bounds.opening_end : bounds.closing_start]
    try:
        payload = yaml.load(
            yaml_bytes.decode("utf-8"),
            Loader=_UniqueKeySafeLoader,
        )
    except yaml.YAMLError as exc:
        raise _error(
            "INVALID_FRONTMATTER_YAML",
            path,
            "frontmatter",
            f"invalid YAML: {exc}",
        ) from None
    if not isinstance(payload, dict):
        raise _error(
            "FRONTMATTER_NOT_MAPPING",
            path,
            "frontmatter",
            "frontmatter must be a mapping",
        )
    try:
        normalized = _normalize_yaml(payload)
    except ValueError as exc:
        raise _error(
            "INVALID_FRONTMATTER_YAML",
            path,
            "frontmatter",
            f"invalid YAML: {exc}",
        ) from None
    body = raw[bounds.closing_end :]
    return MarkdownParts(
        frontmatter=normalized,
        raw_frontmatter_bytes=raw[: bounds.closing_end],
        body_bytes=body,
        body_h1=first_body_h1(body, path=path),
    )


def content_title(document: ContentDocument) -> str:
    title = document.frontmatter.get("title")
    if not isinstance(title, str) or not title.strip():
        raise _error(
            "MISSING_TITLE",
            document.repo_relative_path,
            "title",
            "frontmatter title must be a non-empty string",
        )
    normalized = title.strip()
    if document.body_h1 is None:
        raise _error(
            "MISSING_BODY_H1",
            document.repo_relative_path,
            "title",
            f"missing body H1 for frontmatter title {normalized!r}",
        )
    if normalized != document.body_h1:
        raise _error(
            "TITLE_H1_MISMATCH",
            document.repo_relative_path,
            "title",
            f"title/H1 mismatch: frontmatter={normalized!r} body_h1={document.body_h1!r}",
        )
    return normalized


def parse_document(
    path: Path,
    *,
    repo_root: Path | None = None,
    validate_identity: bool = True,
) -> ContentDocument:
    """Parse a canonical document without rewriting any source bytes.

    ``validate_identity=False`` exists only for legacy title-projection adapters
    whose historical test fixtures predate the required ``id``/``layer`` keys.
    Canonical enumeration always uses the strict default.
    """

    relative = display_path(path, repo_root=repo_root)
    candidate = Path(path)
    root = (REPO_ROOT if repo_root is None else Path(repo_root)).absolute()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = Path(os.path.abspath(candidate))

    try:
        layer, content_id = content_identity(candidate, repo_root=root)
    except ContentPathError as exc:
        raise _error(exc.code, relative, exc.location, exc.message) from None
    parts = parse_frontmatter_bytes(candidate.read_bytes(), path=relative)

    if validate_identity:
        declared_id = parts.frontmatter.get("id")
        if declared_id != content_id:
            raise _error(
                "CONTENT_ID_MISMATCH",
                relative,
                "id",
                f"expected id {content_id!r} from filename",
            )
        declared_layer = parts.frontmatter.get("layer")
        if declared_layer != layer.id:
            raise _error(
                "CONTENT_LAYER_MISMATCH",
                relative,
                "layer",
                f"expected layer {layer.id} from path, got {declared_layer}",
            )

    title = parts.frontmatter.get("title")
    document = ContentDocument(
        path=candidate,
        repo_relative_path=relative,
        layer=layer,
        content_id=content_id,
        frontmatter=parts.frontmatter,
        raw_frontmatter_bytes=parts.raw_frontmatter_bytes,
        body_bytes=parts.body_bytes,
        body_sha256=hashlib.sha256(parts.body_bytes).hexdigest(),
        frontmatter_title=title if isinstance(title, str) else None,
        body_h1=parts.body_h1,
    )
    content_title(document)
    return document


def iter_content_documents(*, repo_root: Path | None = None) -> Iterator[ContentDocument]:
    for path in iter_content_paths(repo_root=repo_root):
        yield parse_document(path, repo_root=repo_root)
