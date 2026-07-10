from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools import migrate_frontmatter


class MigrateFrontmatterTests(unittest.TestCase):
    def test_extracts_difficulty_and_reading_time_from_blockquote(self) -> None:
        text = (
            "# 传感器节点占空比策略与寿命估算\n\n"
            "> **难度**：🟡 中级 | **领域**：IoT功耗优化 | **阅读时间**：约 18 分钟\n\n"
            "正文第一段。\n"
        )
        meta = migrate_frontmatter.extract_meta(
            path=Path("docs/foundation/papers/duty-cycling-sensor-node.md"),
            text=text,
        )
        self.assertEqual(meta["id"], "duty-cycling-sensor-node")
        self.assertEqual(meta["layer"], 1)
        self.assertEqual(meta["title"], "传感器节点占空比策略与寿命估算")
        self.assertEqual(meta["difficulty"], "intermediate")
        self.assertEqual(meta["reading_time"], 18)
        self.assertEqual(meta["source_status"], "UNVERIFIED")
        self.assertEqual(meta["review_status"], "UNREVIEWED")
        self.assertEqual(meta["content_type"], "UNKNOWN")
        self.assertEqual(meta["prerequisites"], "UNKNOWN")
        self.assertNotIn(meta["source_status"], {"VERIFIED"})
        self.assertNotIn(meta["review_status"], {"HUMAN_APPROVED"})

    def test_insert_preserves_body_sha256(self) -> None:
        original = (
            "# 标题\n\n"
            "> **难度**：🟢 入门 | **领域**：测试 | **阅读时间**：约 10 分钟\n\n"
            "保持不变的正文。\n"
        )
        body_before = migrate_frontmatter.body_bytes(original)
        updated = migrate_frontmatter.insert_frontmatter(
            path=Path("docs/network/papers/demo-topic.md"),
            text=original,
        )
        self.assertTrue(updated.startswith("---\n"))
        self.assertEqual(migrate_frontmatter.body_bytes(updated), body_before)
        self.assertEqual(
            hashlib.sha256(body_before).hexdigest(),
            hashlib.sha256(migrate_frontmatter.body_bytes(updated)).hexdigest(),
        )

    def test_idempotent_second_run_unchanged(self) -> None:
        original = "# 标题\n\n正文。\n"
        once = migrate_frontmatter.insert_frontmatter(
            path=Path("docs/security/papers/demo.md"),
            text=original,
        )
        twice = migrate_frontmatter.insert_frontmatter(
            path=Path("docs/security/papers/demo.md"),
            text=once,
        )
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
