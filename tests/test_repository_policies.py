import copy
import unittest
from pathlib import Path

from tools import check_duplicates, check_workflow_policy


class DuplicatePolicyTests(unittest.TestCase):
    def test_declared_sources_have_no_drift(self):
        errors, counts = check_duplicates.validate_policy(
            check_duplicates.ROOT / "data/canonical-sources.yml"
        )
        self.assertEqual(errors, [])
        self.assertEqual(counts, {"canonical_css": 2, "legacy_markdown_mirrors": 2})


class WorkflowPolicyTests(unittest.TestCase):
    def test_repository_workflows_follow_policy(self):
        ci = check_workflow_policy.load_workflow(check_workflow_policy.ROOT / ".github/workflows/ci.yml")
        deploy = check_workflow_policy.load_workflow(
            check_workflow_policy.ROOT / ".github/workflows/deploy.yml"
        )
        self.assertEqual(check_workflow_policy.validate_ci(check_workflow_policy.ROOT / ".github/workflows/ci.yml", ci), [])
        self.assertEqual(
            check_workflow_policy.validate_deploy(
                check_workflow_policy.ROOT / ".github/workflows/deploy.yml", deploy
            ),
            [],
        )

    def test_mutable_action_ref_is_rejected(self):
        ci = check_workflow_policy.load_workflow(check_workflow_policy.ROOT / ".github/workflows/ci.yml")
        changed = copy.deepcopy(ci)
        changed["jobs"]["quality"]["steps"][0]["uses"] = "actions/checkout@v4"
        errors = check_workflow_policy.validate_ci(
            check_workflow_policy.ROOT / ".github/workflows/ci.yml", changed
        )
        self.assertTrue(any("mutable" in error for error in errors))


class PublicDiscoveryTests(unittest.TestCase):
    def test_robots_points_to_public_sitemap(self):
        robots = (Path(__file__).resolve().parents[1] / "docs" / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://estelledc.github.io/iot/sitemap.xml", robots)


if __name__ == "__main__":
    unittest.main()
