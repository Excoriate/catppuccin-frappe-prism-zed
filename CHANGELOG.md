# Changelog

## 0.2.0 - 2026-10-19

### Changed

- Give read and write symbol occurrences the same pale lavender background
  (`#babbf1`), distinct from the green selection.
- Restyle the existing integrated terminal palette with deep navy (`#080c14`),
  phosphor green text (`#39ff88`), and 24 normal, bright and dim ANSI colors.
  The colors take inspiration from
  [Neon Blue Split Contrast](https://ghostty-style.vercel.app/config/neon-blue-split-contrast)
  and are adapted for Zed's terminal.
- Pin the installation commands and source download to v0.2.0.

### Known limit

- In Zed 1.24.2, terminal selection shares the editor's green background and keeps
  terminal foreground colors. Selecting bright text can reduce contrast,
  particularly green text on green. Prism retains the strong green editor
  selection; no independent terminal selection foreground theme control has been
  identified for this Zed version.

### Unchanged

- The primary selection remains green (`#9ad99e`). Editor syntax colors, font
  weights and italics remain unchanged.
- Alex Torres Ruiz's author credit and both MIT notices are retained, including
  the Catppuccin notice embedded in the theme JSON.

This GitHub release is a source distribution. Zed catalogue submission and review
are separate; the theme is not yet listed in the catalogue.
