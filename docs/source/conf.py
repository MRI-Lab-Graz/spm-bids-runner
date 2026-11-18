"""Sphinx configuration for the SPM BIDS Runner documentation (Read the Docs)."""

project = "SPM BIDS Runner"
author = "MRI-Lab-Graz"
copyright = "2026, MRI-Lab-Graz"

extensions = ["myst_parser", "sphinxcontrib.mermaid"]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3

html_theme = "shibuya"
html_theme_options = {
    "accent_color": "green",
    "github_url": "https://github.com/MRI-Lab-Graz/spm-bids-runner",
}
html_title = "SPM BIDS Runner"
