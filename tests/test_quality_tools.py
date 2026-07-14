from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools import (
    check_markdown_fences,
    check_markdown_links,
    check_release_metadata,
    content_inventory,
    validate_site,
)
from overrides.hooks import mathjax


class ContentInventoryTests(unittest.TestCase):
    def test_generated_inventory_is_current_and_deterministic(self) -> None:
        first = content_inventory.content_inventory()
        second = content_inventory.content_inventory()
        self.assertEqual(
            content_inventory._json_bytes(first),
            content_inventory._json_bytes(second),
        )
        self.assertEqual([], content_inventory.check_inventory(first))

    def test_structural_source_audits_are_projected_as_sampled_inventory(self) -> None:
        inventory = content_inventory.content_inventory()
        expected_by_layer = {
            "foundation": 275,
            "connectivity": 217,
            "network": 25,
            "computing": 25,
            "intelligence": 25,
            "security": 25,
            "applications": 25,
            "frontier": 25,
        }
        actual_by_layer = {
            layer["slug"]: layer["structural_source_audit_records"]
            for layer in inventory["layers"]
        }
        self.assertEqual(expected_by_layer, actual_by_layer)
        self.assertEqual(
            {
                "UNVERIFIED": 15,
                "PARTIAL": 0,
                "VERIFIED": 642,
            },
            inventory["totals"]["source_status_counts"],
        )
        self.assertEqual(642, inventory["totals"]["structural_source_audit_records"])
        self.assertEqual(642, inventory["totals"]["structural_source_audited_files"])
        self.assertEqual(642, inventory["totals"]["source_audited_files"])
        self.assertTrue(
            all(layer["source_audit"] == "SAMPLED_STRUCTURAL" for layer in inventory["layers"])
        )

    def test_source_audit_projection_uses_only_current_active_structural_records(self) -> None:
        trust_result = SimpleNamespace(
            projections={
                "active-structural-content": SimpleNamespace(
                    content_path="docs/foundation/papers/active.md",
                    source_status="UNVERIFIED",
                    active_audit_ids=("active-structural", "active-claim"),
                ),
                "inactive-structural-content": SimpleNamespace(
                    content_path="docs/foundation/papers/inactive.md",
                    source_status="UNVERIFIED",
                    active_audit_ids=(),
                ),
                "partial-claim-content": SimpleNamespace(
                    content_path="docs/connectivity/papers/partial.md",
                    source_status="PARTIAL",
                    active_audit_ids=("active-claim-2",),
                ),
            }
        )
        records_by_id = {
            "active-structural": {"audit_kind": "STRUCTURAL"},
            "inactive-structural": {"audit_kind": "STRUCTURAL"},
            "active-claim": {"audit_kind": "CLAIM_VERIFICATION"},
            "active-claim-2": {"audit_kind": "CLAIM_VERIFICATION"},
        }

        projection = content_inventory._source_audit_projection(
            trust_result,
            records_by_id,
        )

        self.assertEqual(1, projection["by_layer"]["foundation"]["structural_records"])
        self.assertEqual(0, projection["by_layer"]["connectivity"]["structural_records"])
        self.assertEqual(1, projection["totals"]["structural_source_audit_records"])
        self.assertEqual(1, projection["totals"]["source_audited_files"])
        self.assertEqual(
            {
                "UNVERIFIED": 2,
                "PARTIAL": 1,
                "VERIFIED": 0,
            },
            projection["totals"]["source_status_counts"],
        )

    def test_source_audit_files_are_part_of_inventory_fingerprint(self) -> None:
        audit_inputs = {
            path.relative_to(content_inventory.ROOT).as_posix()
            for path in content_inventory._source_audit_paths()
        }
        fingerprint_inputs = {
            path.relative_to(content_inventory.ROOT).as_posix()
            for path in content_inventory._inventory_structural_paths()
        }
        self.assertEqual(1284, len(audit_inputs))
        self.assertLessEqual(audit_inputs, fingerprint_inputs)

        temp_root = content_inventory.ROOT / ".tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            probe = Path(directory) / "audit.yml"
            probe.write_text("audit: before\n", encoding="utf-8")
            before = content_inventory._source_fingerprint([probe])
            probe.write_text("audit: after\n", encoding="utf-8")
            after = content_inventory._source_fingerprint([probe])
        self.assertNotEqual(before, after)

    def test_public_inventory_blocks_show_structural_not_factual_verification(self) -> None:
        inventory = content_inventory.content_inventory()
        for rendered in (
            content_inventory._render_readme(inventory),
            content_inventory._render_roadmap_root(inventory),
            content_inventory._render_docs_progress(inventory),
        ):
            self.assertIn("STRUCTURAL", rendered)
            self.assertIn("事实核验：**642**", rendered)
            self.assertNotIn("状态为 `NOT_TRACKED`", rendered)


class HomepageSourceTruthTests(unittest.TestCase):
    def test_editable_home_content_lives_in_markdown(self) -> None:
        root = content_inventory.ROOT
        template = (root / "overrides/home.html").read_text(encoding="utf-8")
        markdown = (root / "docs/index.md").read_text(encoding="utf-8")
        self.assertIn("{{ page.content }}", template)
        self.assertNotIn("物联网全栈技术学习站", template)
        self.assertIn("物联网全栈技术学习站", markdown)

    def test_public_showcase_states_value_roles_evidence_and_limits(self) -> None:
        root = content_inventory.ROOT
        markdown = (root / "docs/index.md").read_text(encoding="utf-8")
        for expected in (
            "持续维护 · Maintained",
            "Explore the stack as a dependency system",
            'class="iot-stack-map"',
            "642 / 657",
            "HUMAN_APPROVED",
            "NOT_TRACKED",
            'class="jx-proof"',
            "Problem / 问题",
            "Jason Xun / 决策与验收",
            "AI / 辅助",
            "Evidence / 证据",
            "Limitations / 局限",
            "642/657 正文已有",
            "新增卡片必须继续走事实核验和人工审查后才能升级",
        ):
            self.assertIn(expected, markdown)

    def test_public_shell_keeps_stable_portfolio_links(self) -> None:
        root = content_inventory.ROOT
        shell = "\n".join(
            (root / relative).read_text(encoding="utf-8")
            for relative in (
                "overrides/partials/header.html",
                "overrides/partials/footer.html",
            )
        )
        for href in (
            "https://estelledc.github.io/",
            "https://estelledc.github.io/about/",
            "https://estelledc.github.io/resume/",
            "https://github.com/estelledc/iot",
        ):
            self.assertIn(f'href="{href}"', shell)

    def test_public_metadata_uses_shared_identity_and_social_preview(self) -> None:
        root = content_inventory.ROOT
        shell = (root / "overrides/main.html").read_text(encoding="utf-8")
        for marker in (
            "https://estelledc.github.io/#person",
            '"name": "Jason Xun"',
            'property="og:image"',
            'name="twitter:image"',
            '"@type": "CollectionPage" if page.is_homepage else "TechArticle"',
        ):
            self.assertIn(marker, shell)

    def test_mkdocs_loads_jason_design_system_v2(self) -> None:
        root = content_inventory.ROOT
        config = (root / "mkdocs.yml").read_text(encoding="utf-8")
        self.assertIn("assets/css/jx/tokens.css", config)
        self.assertIn("assets/css/jx/components.css", config)
        self.assertEqual(
            "2.2.0",
            (root / "docs/assets/css/jx/VERSION").read_text(encoding="utf-8").strip(),
        )

    def test_home_interactions_are_pointer_safe_and_motion_reduced(self) -> None:
        root = content_inventory.ROOT
        template = (root / "overrides/home.html").read_text(encoding="utf-8")
        override = (root / "docs/assets/css/jx-override.css").read_text(encoding="utf-8")
        for marker in (
            "@media (hover: hover) and (pointer: fine)",
            ".iot-stack-map a:focus-visible",
            ".iot-stack-map a:active",
            ".iot-layer-card:focus-visible",
            ".iot-layer-card:active",
            "@media (prefers-reduced-motion: reduce)",
        ):
            self.assertIn(marker, template)
        self.assertIn(".iot-global-nav .jx-site-nav__menu summary:active", override)
        self.assertNotIn("transition: all", template)
        self.assertNotIn("animation-duration: 0.01ms", override)

    def test_home_keeps_material_mobile_drawer_available(self) -> None:
        root = content_inventory.ROOT
        template = (root / "overrides/home.html").read_text(encoding="utf-8")
        self.assertNotIn(".md-sidebar { display: none !important; }", template)
        self.assertIn(".md-sidebar--secondary { display: none !important; }", template)
        self.assertIn("@media screen and (min-width: 76.25em)", template)
        self.assertIn(".md-sidebar--primary { display: none !important; }", template)
        self.assertIn("@media (max-width: 700px)", template)
        self.assertIn(".iot-stack-map a", template)
        self.assertIn("grid-template-columns: 34px minmax(0, 1fr) auto", template)

    def test_mathjax_is_injected_only_for_formula_pages(self) -> None:
        ordinary = '<html><body><main>No formula</main></body></html>'
        formula = '<html><body><span class="arithmatex">\\(x\\)</span></body></html>'
        self.assertEqual(ordinary, mathjax.on_post_page(ordinary))
        rendered = mathjax.on_post_page(formula)
        self.assertIn("mathjax@3.2.2", rendered)
        self.assertIn("window.MathJax", rendered)


class MarkdownQualityToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.old_link_root = check_markdown_links.ROOT
        self.old_docs_root = check_markdown_links.DOCS_ROOT
        self.old_fence_root = check_markdown_fences.ROOT
        check_markdown_links.ROOT = self.root
        check_markdown_links.DOCS_ROOT = self.root / "docs"
        check_markdown_fences.ROOT = self.root

    def tearDown(self) -> None:
        check_markdown_links.ROOT = self.old_link_root
        check_markdown_links.DOCS_ROOT = self.old_docs_root
        check_markdown_fences.ROOT = self.old_fence_root
        self.tempdir.cleanup()

    def test_missing_relative_link_fails(self) -> None:
        source = self.root / "docs" / "index.md"
        source.parent.mkdir(parents=True)
        source.write_text("[missing](missing.md)\n", encoding="utf-8")
        errors = check_markdown_links.check_file(source, check_anchors=True)
        self.assertEqual(1, len(errors))
        self.assertIn("missing link target", errors[0])

    def test_existing_link_and_anchor_pass(self) -> None:
        source = self.root / "docs" / "index.md"
        target = self.root / "docs" / "guide.md"
        source.parent.mkdir(parents=True)
        source.write_text("[guide](guide.md#开始)\n", encoding="utf-8")
        target.write_text("# 开始\n", encoding="utf-8")
        self.assertEqual([], check_markdown_links.check_file(source, check_anchors=True))

    def test_published_doc_link_outside_docs_dir_fails(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        target = self.root / "data" / "progress.yml"
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text("[progress](../../data/progress.yml)\n", encoding="utf-8")
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])
        self.assertIn("docs/plans/review.md", errors[0])

    def test_published_reference_link_outside_docs_dir_fails(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        target = self.root / "data" / "progress.yml"
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text(
            "[progress][state]\n\n[state]: ../../data/progress.yml\n",
            encoding="utf-8",
        )
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])

    def test_published_shortcut_reference_outside_docs_dir_fails(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        target = self.root / "data" / "progress.yml"
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text(
            "[progress]\n\n[progress]: ../../data/progress.yml\n",
            encoding="utf-8",
        )
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])

    def test_inline_code_is_not_treated_as_shortcut_reference(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        target = self.root / "data" / "progress.yml"
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text(
            "Use `[progress]` as a literal.\n"
            "Use `a multiline literal\n[progress]\nthat stays code`.\n"
            "Python-Markdown also treats ````[progress]` as code.\n\n"
            "[progress]: ../../data/progress.yml\n",
            encoding="utf-8",
        )
        self.assertEqual(
            [],
            check_markdown_links.check_file(
                source,
                check_anchors=True,
                published=True,
            ),
        )

    def test_published_link_outside_repository_reports_boundary(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        source.parent.mkdir(parents=True)
        source.write_text("[outside](../../../outside.md)\n", encoding="utf-8")
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])
        self.assertIn("<outside repository>", errors[0])

    def test_nonclosing_fence_info_cannot_hide_published_link(self) -> None:
        source = self.root / "docs" / "plans" / "review.md"
        guide = self.root / "docs" / "guide.md"
        target = self.root / "data" / "progress.yml"
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        guide.write_text("# Guide\n", encoding="utf-8")
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text(
            "```markdown\n"
            "```not-a-closing-fence\n"
            "[example](../guide.md)\n"
            "```\n"
            "[progress](../../data/progress.yml)\n",
            encoding="utf-8",
        )
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])

    def test_published_symlink_source_cannot_escape_docs_dir(self) -> None:
        source = self.root / "docs" / "linked.md"
        outside_source = self.root / "data" / "source.md"
        target = self.root / "data" / "target.yml"
        source.parent.mkdir(parents=True)
        outside_source.parent.mkdir(parents=True)
        outside_source.write_text("[target](../data/target.yml)\n", encoding="utf-8")
        target.write_text("status: done\n", encoding="utf-8")
        source.symlink_to(outside_source)
        errors = check_markdown_links.check_file(
            source,
            check_anchors=True,
            published=True,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("published link target outside docs_dir", errors[0])

    def test_repository_markdown_can_link_to_repository_data(self) -> None:
        source = self.root / "README.md"
        target = self.root / "data" / "progress.yml"
        target.parent.mkdir(parents=True)
        target.write_text("status: done\n", encoding="utf-8")
        source.write_text("[progress](data/progress.yml)\n", encoding="utf-8")
        self.assertEqual(
            [],
            check_markdown_links.check_file(
                source,
                check_anchors=True,
                published=True,
            ),
        )

    def test_published_iot_absolute_directory_and_anchor_pass(self) -> None:
        source = self.root / "docs" / "index.md"
        guide = self.root / "docs" / "guide" / "index.md"
        source.parent.mkdir(parents=True)
        guide.parent.mkdir(parents=True)
        source.write_text("[guide](/iot/guide/#开始)\n", encoding="utf-8")
        guide.write_text("# 开始\n", encoding="utf-8")
        self.assertEqual(
            [],
            check_markdown_links.check_file(
                source,
                check_anchors=True,
                published=True,
            ),
        )

    def test_heading_swallowed_by_bare_fence_fails(self) -> None:
        source = self.root / "broken.md"
        source.write_text("```\nnot code\n## swallowed\n```\n", encoding="utf-8")
        errors = check_markdown_fences.check_file(source)
        self.assertTrue(any("swallowed" in error for error in errors))


class ReleaseMetadataTests(unittest.TestCase):
    def test_repository_release_metadata_is_consistent(self) -> None:
        self.assertEqual(
            [],
            check_release_metadata.validate(
                check_release_metadata.ROOT / "VERSION",
                check_release_metadata.ROOT / "CHANGELOG.md",
            ),
        )

    def test_mismatched_version_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = root / "VERSION"
            changelog = root / "CHANGELOG.md"
            version.write_text("0.2.0\n", encoding="utf-8")
            changelog.write_text(
                "## [0.1.0] - 2026-07-10\n"
                "IOT-T001\n"
                + "a" * 40
                + "\n"
                + "b" * 64
                + "\n",
                encoding="utf-8",
            )
            errors = check_release_metadata.validate(version, changelog)
            self.assertTrue(any("does not match" in error for error in errors))

    def test_local_user_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            version = root / "VERSION"
            changelog = root / "CHANGELOG.md"
            version.write_text("0.1.0\n", encoding="utf-8")
            local_path = "/" + "Users/example/private.log"
            changelog.write_text(
                "## [0.1.0] - 2026-07-10\n"
                "IOT-T025\n"
                + "a" * 40
                + "\n"
                + "b" * 64
                + "\n"
                + local_path
                + "\n",
                encoding="utf-8",
            )
            errors = check_release_metadata.validate(version, changelog)
            self.assertTrue(any("local absolute user path" in error for error in errors))


class SiteValidationTests(unittest.TestCase):
    def test_duplicate_landmarks_and_unsafe_blank_link_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                "<main><h1>Home</h1></main><main></main>"
                "<footer></footer><footer></footer>"
                '<a href="https://example.com" target="_blank">x</a>',
                encoding="utf-8",
            )
            errors = validate_site.validate_page(
                page,
                single_main=True,
                single_footer=True,
                single_h1=True,
                external_link_rel=True,
            )
            self.assertEqual(3, len(errors))

    def test_expected_structure_text_and_link_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                "<main><h1>物联网全栈技术学习站</h1>"
                '<a href="foundation/">Layer 1</a></main>'
                "<footer></footer>",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                validate_site.validate_page(
                    page,
                    single_main=True,
                    single_footer=True,
                    single_h1=True,
                    expected_text=["物联网全栈技术学习站"],
                    expected_links=["foundation/"],
                ),
            )

    def test_canonical_social_metadata_and_json_ld_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                '<link rel="canonical" href="https://example.com/iot/">'
                '<meta property="og:title" content="IoT">'
                '<meta name="twitter:card" content="summary">'
                '<script type="application/ld+json">'
                '{"@context":"https://schema.org","@type":"WebSite"}'
                "</script><main><h1>IoT</h1></main><footer></footer>",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                validate_site.validate_page(
                    page,
                    expected_canonical="https://example.com/iot/",
                    expected_meta=["og:title", "twitter:card"],
                    expected_json_ld_types=["WebSite"],
                ),
            )

    def test_404_contract_requires_noindex_and_no_json_ld(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "404.html"
            page.write_text(
                '<link rel="canonical" href="https://example.com/iot/404.html">'
                '<meta name="robots" content="noindex,follow">'
                '<main><h1>Not found</h1></main><footer>Exit</footer>',
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                validate_site.validate_page(
                    page,
                    single_main=True,
                    single_footer=True,
                    single_h1=True,
                    expected_canonical="https://example.com/iot/404.html",
                    expected_robots="noindex,follow",
                    forbid_json_ld=True,
                ),
            )
    def test_missing_or_invalid_discovery_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                '<meta property="og:title" content="">'
                '<script type="application/ld+json">{invalid}</script>',
                encoding="utf-8",
            )
            errors = validate_site.validate_page(
                page,
                expected_canonical="https://example.com/iot/",
                expected_meta=["og:title"],
                expected_json_ld_types=["WebSite"],
            )
            self.assertEqual(4, len(errors))


if __name__ == "__main__":
    unittest.main()
