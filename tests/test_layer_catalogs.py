from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import content_inventory, generate_layer_catalogs


class LayerCatalogTests(unittest.TestCase):
    @staticmethod
    def _write_paper(path: Path, *, title: str, h1: str | None = None) -> None:
        path.write_text(
            "---\n"
            "schema_version: '1.0'\n"
            f"id: {path.stem}\n"
            f"title: {title}\n"
            "---\n"
            f"# {h1 or title}\n",
            encoding="utf-8",
        )

    def test_catalog_lists_every_paper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            papers = root / "docs" / "network" / "papers"
            papers.mkdir(parents=True)
            self._write_paper(papers / "a.md", title="A")
            self._write_paper(papers / "b.md", title="B")
            text = generate_layer_catalogs.render_catalog(
                layer_id=3,
                slug="network",
                name="网络协议",
                paper_paths=[papers / "a.md", papers / "b.md"],
            )
            self.assertIn("](papers/a.md)", text)
            self.assertIn("](papers/b.md)", text)
            self.assertIn("自动生成", text)

    def test_title_h1_mismatch_fails_with_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "docs" / "network" / "papers" / "mismatch.md"
            paper.parent.mkdir(parents=True)
            self._write_paper(paper, title="结构化标题", h1="正文标题")
            with mock.patch.object(generate_layer_catalogs, "ROOT", root):
                with self.assertRaisesRegex(
                    ValueError,
                    r"docs/network/papers/mismatch\.md: title/H1 mismatch",
                ):
                    generate_layer_catalogs._title_for(paper)

    def test_fenced_or_commented_h1_does_not_satisfy_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "docs" / "network" / "papers" / "hidden-h1.md"
            paper.parent.mkdir(parents=True)
            paper.write_text(
                "---\n"
                "title: Hidden title\n"
                "---\n"
                "```markdown\n"
                "```not-a-closing-fence\n"
                "# Hidden title\n"
                "```\n"
                "<!--\n"
                "# Hidden title\n"
                "-->\n",
                encoding="utf-8",
            )
            with mock.patch.object(generate_layer_catalogs, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "missing body H1"):
                    generate_layer_catalogs._title_for(paper)

    def test_repository_title_h1_invariant_covers_all_content(self) -> None:
        papers = sorted(generate_layer_catalogs.ROOT.glob("docs/*/papers/*.md"))
        expected = content_inventory.content_inventory()["totals"]["content_files"]
        self.assertEqual(652, expected)
        self.assertEqual(expected, len(papers))
        for paper in papers:
            with self.subTest(path=paper.relative_to(generate_layer_catalogs.ROOT)):
                self.assertTrue(generate_layer_catalogs._title_for(paper))

    def test_check_catalogs_reports_title_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            papers = root / "docs" / "network" / "papers"
            papers.mkdir(parents=True)
            self._write_paper(papers / "a.md", title="A")
            catalog = root / "docs" / "network" / "catalog.md"
            catalog.write_text(
                generate_layer_catalogs.render_catalog(
                    layer_id=3,
                    slug="network",
                    name="网络协议",
                    paper_paths=[papers / "a.md"],
                ).replace("| A |", "| stale A |"),
                encoding="utf-8",
            )
            layers = ((3, "network", "网络协议", "layer3-network.json"),)
            with (
                mock.patch.object(generate_layer_catalogs, "ROOT", root),
                mock.patch.object(generate_layer_catalogs, "LAYERS", layers),
            ):
                errors = generate_layer_catalogs.check_catalogs()
            self.assertEqual(
                ["catalog title/content drift: docs/network/catalog.md"],
                errors,
            )

    def test_check_catalogs_reports_missing_and_unexpected_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            papers = root / "docs" / "network" / "papers"
            papers.mkdir(parents=True)
            self._write_paper(papers / "a.md", title="A")
            self._write_paper(papers / "b.md", title="B")
            catalog = root / "docs" / "network" / "catalog.md"
            catalog.write_text(
                "# stale\n\n"
                "| # | 标题 | 文件 |\n"
                "| --- | --- | --- |\n"
                "| 1 | A | [a](papers/a.md) |\n"
                "| 2 | duplicate | [a again](papers/a.md) |\n"
                "| 3 | extra | [extra](papers/extra.md) |\n",
                encoding="utf-8",
            )
            layers = ((3, "network", "网络协议", "layer3-network.json"),)
            with (
                mock.patch.object(generate_layer_catalogs, "ROOT", root),
                mock.patch.object(generate_layer_catalogs, "LAYERS", layers),
            ):
                errors = generate_layer_catalogs.check_catalogs()
            self.assertIn(
                "catalog missing links: docs/network/catalog.md: papers/b.md",
                errors,
            )
            self.assertIn(
                "catalog unexpected links: docs/network/catalog.md: papers/extra.md",
                errors,
            )
            self.assertIn(
                "catalog duplicate links: docs/network/catalog.md: papers/a.md",
                errors,
            )

    def test_repository_catalogs_are_current(self) -> None:
        self.assertEqual([], generate_layer_catalogs.check_catalogs())


if __name__ == "__main__":
    unittest.main()
