from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
            "642 / 642",
            "IN_REVIEW",
            "NOT_TRACKED",
            'class="jx-proof"',
            "Problem / 问题",
            "Jason Xun / 决策与验收",
            "AI / 辅助",
            "Evidence / 证据",
            "Limitations / 局限",
            "642/642 正文完成深审",
            "IN_REVIEW</code> 不等于事实已验证",
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
            "2.1.0",
            (root / "docs/assets/css/jx/VERSION").read_text(encoding="utf-8").strip(),
        )

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
