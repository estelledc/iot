from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import generate_layer_catalogs


class LayerCatalogTests(unittest.TestCase):
    def test_catalog_lists_every_paper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            papers = root / "docs" / "network" / "papers"
            papers.mkdir(parents=True)
            (papers / "a.md").write_text("# A\n", encoding="utf-8")
            (papers / "b.md").write_text("# B\n", encoding="utf-8")
            text = generate_layer_catalogs.render_catalog(
                layer_id=3,
                slug="network",
                name="网络协议",
                paper_paths=[papers / "a.md", papers / "b.md"],
            )
            self.assertIn("](papers/a.md)", text)
            self.assertIn("](papers/b.md)", text)
            self.assertIn("自动生成", text)


if __name__ == "__main__":
    unittest.main()
