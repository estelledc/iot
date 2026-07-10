from __future__ import annotations

import unittest

from tools import validate_frontmatter


class FrontmatterSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = validate_frontmatter.load_schema()
        cls.fixtures = validate_frontmatter.ROOT / "tests/fixtures/frontmatter"

    def test_fixture_contract(self) -> None:
        self.assertEqual([], validate_frontmatter.validate_fixtures(self.fixtures, self.schema))

    def test_semantic_path_checks_id_and_layer(self) -> None:
        fixture = self.fixtures / "valid-technical-analysis.md"
        payload, parse_issues = validate_frontmatter.parse_frontmatter(fixture)
        self.assertEqual([], parse_issues)
        assert payload is not None
        issues = validate_frontmatter.validate_payload(
            payload,
            validate_frontmatter.ROOT / "docs/network/papers/wrong-filename.md",
            self.schema,
            semantic_paths=True,
        )
        self.assertTrue(any(issue.location == "id" for issue in issues))


if __name__ == "__main__":
    unittest.main()
