"""Canonical registry for the eight IoT reading-station layers."""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, NamedTuple


class Layer(NamedTuple):
    """One stable content layer.

    ``NamedTuple`` intentionally preserves the tuple-unpacking contract used by
    the repository's legacy generators while giving domain code named fields.
    """

    id: int
    slug: str
    name: str
    plan_file: str


LAYERS: tuple[Layer, ...] = (
    Layer(1, "foundation", "感知与硬件", "layer1-foundation.json"),
    Layer(2, "connectivity", "无线接入", "layer2-connectivity.json"),
    Layer(3, "network", "网络协议", "layer3-network.json"),
    Layer(4, "computing", "计算平台", "layer4-computing.json"),
    Layer(5, "intelligence", "边缘智能", "layer5-intelligence.json"),
    Layer(6, "security", "安全与隐私", "layer6-security.json"),
    Layer(7, "applications", "综合应用", "layer7-applications.json"),
    Layer(8, "frontier", "前沿方向", "layer8-frontier.json"),
)

LAYER_BY_ID: Mapping[int, Layer] = MappingProxyType({layer.id: layer for layer in LAYERS})
LAYER_BY_SLUG: Mapping[str, Layer] = MappingProxyType({layer.slug: layer for layer in LAYERS})
LAYER_BY_NAME: Mapping[str, Layer] = MappingProxyType({layer.name: layer for layer in LAYERS})
LAYER_BY_PLAN_FILE: Mapping[str, Layer] = MappingProxyType(
    {layer.plan_file: layer for layer in LAYERS}
)
LAYER_ID_BY_SLUG: Mapping[str, int] = MappingProxyType(
    {layer.slug: layer.id for layer in LAYERS}
)


def layer_by_id(value: int) -> Layer:
    try:
        return LAYER_BY_ID[value]
    except KeyError:
        raise ValueError(f"unknown layer id: {value}") from None


def layer_by_slug(value: str) -> Layer:
    try:
        return LAYER_BY_SLUG[value]
    except KeyError:
        raise ValueError(f"unknown layer slug: {value}") from None


def layer_by_name(value: str) -> Layer:
    try:
        return LAYER_BY_NAME[value]
    except KeyError:
        raise ValueError(f"unknown layer name: {value}") from None


def layer_by_plan_file(value: str) -> Layer:
    try:
        return LAYER_BY_PLAN_FILE[value]
    except KeyError:
        raise ValueError(f"unknown layer plan file: {value}") from None
