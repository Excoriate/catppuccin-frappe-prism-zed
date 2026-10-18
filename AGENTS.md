# Repository guidance

## Package safety

This is a theme-only Zed extension. Do not add language providers, grammars,
language servers, runtime installers, or automatic edits to personal settings
to this package.

## Where things live

- `extension.toml`: extension identity, version, and package metadata.
- `themes/catppuccin-frappe-prism.json`: palette and syntax-role styles.
- `LICENSE` and `themes/LICENSE.catppuccin`: both MIT notices; preserve them.
- `examples/`: preview fixtures and optional `examples/settings.json` preferences.
- `scripts/check.py` and `tests/test_check.py`: package validation and regression
  controls; `.github/workflows/ci.yml` runs the same check.
- `README.md` and `CONTRIBUTING.md`: installation and contribution details.

## Setup and tests

Use Python 3.11 or newer. From the repository root, run:

```sh
python3 scripts/check.py
```

An intentional role or contrast change needs a corresponding contract and
regression-control update. Do not remove a failing assertion merely to pass.

## Preview visual changes

In Zed, run **zed: install dev extension** and select this repository root, which
contains `extension.toml`. Then run **theme selector: toggle** and choose
**Catppuccin Frappé Prism**. Compare the motivating example and an ordinary code
sample with the same font, Zed version, and settings before and after the change.

Static checks do not prove native rendering or that a language provider emits a
styled scope. Distinguish the theme alone from the optional settings profile in
`examples/settings.json`; merge those preferences into existing settings rather
than replacing them. Do not promise bundled language-provider behavior or claim
Zed catalogue acceptance without evidence of the separate registry review.
