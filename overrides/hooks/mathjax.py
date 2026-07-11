"""Inject MathJax only into rendered pages that actually contain formulas."""

from __future__ import annotations


MATHJAX = r"""
<script>
  window.MathJax = {
    tex: {inlineMath: [["\\(", "\\)"], ["$", "$"]]},
    options: {ignoreHtmlClass: "\\bno-mathjax\\b", processHtmlClass: "\\barithmatex\\b"}
  };
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"></script>
""".strip()


def on_post_page(output: str, **_: object) -> str:
    """Keep ordinary reading pages free of the MathJax runtime."""
    if 'class="arithmatex"' not in output:
        return output
    return output.replace("</body>", f"{MATHJAX}\n</body>", 1)
