# Contributing

Changes that make the theme easier to read are welcome. You can propose a fix in an issue or open a pull request with a small, focused change. Include the language, the role that is difficult to distinguish, your Zed version, and a short example when reporting a rendering problem.

## Check a change locally

You need Python 3.11 or newer and Zed for visual review. The checker uses the Python standard library; there are no packages to install or build tools to configure.

From the repository root, run:

```sh
python3 scripts/check.py
```

This is the same command used by CI. It checks the manifest, discoverable theme, retained licenses, color syntax, syntax contrast against normal and active-line backgrounds, deliberate role distinctions, declaration typography, lavender read/write occurrences, green selection, and terminal colors. It also runs negative controls that must reject malformed or regressed packages. It does not modify your working tree.

The checker intentionally protects reading behavior rather than a frozen palette checksum. If a deliberate design change alters a role contract, update its check and control together, and explain the reading task the new contract improves. Do not remove a failing contract merely to make CI green.

## Preview in Zed

1. Open Zed's command palette and run **zed: install dev extension**.
2. Select this repository's root, which contains `extension.toml`.
3. Run **theme selector: toggle** and choose **Catppuccin Frappé Prism**. Reload Zed if a copied theme or extension change has not appeared.
4. Inspect the affected code at your normal font size, including the active line, selection, and read/write occurrence highlights.
5. In Zed's terminal, run `sh examples/terminal-preview.sh`. Compare plain text, normal, bright and dim ANSI colors, and text on black backgrounds. Check inverse and selected text, too.

For visual changes, include before and after screenshots of the same code, font, Zed version, and settings. Use a short example without secrets. Check at least one ordinary language as well as the language motivating the change, so a stronger distinction does not hide another role.

A theme assigns styles to scopes that Zed or a language provider emits. Some of the enhanced examples described in the README depend on optional providers or semantic-token settings. State which profile you used. A color entry or passing palette check does not prove a language emits that capture, and it does not prove selected-text rendering. Do not describe a provider-dependent role as part of a fresh, theme-only installation.

## Pull requests

- Keep a change focused and explain the concrete before/after behavior.
- Run `python3 scripts/check.py` and include the result plus native preview details when relevant.
- Preserve both MIT notices: `LICENSE` and `themes/LICENSE.catppuccin`, including their embedded text in the theme JSON `license` metadata. Credit the upstream Catppuccin palette without implying official endorsement.
- Keep the package theme-only. Language providers, grammars, compilers and automatic changes to personal settings belong outside this extension.
- Leave the extension version unchanged for ordinary contributions unless the maintainer requests a release update. Registry releases require the repository version and registry entry to agree.

There is no special commit-message format or contributor agreement. The maintainer may ask for a smaller example or a screenshot with the same settings to make a rendering claim reproducible. A green pull request check establishes the local package contracts; Zed catalogue review and publication are separate steps.

## Catalogue submission

Follow Zed's [official publishing guide](https://zed.dev/docs/extensions/publishing/publishing-guide).
This repository is a theme-only extension with ID `catppuccin-frappe-prism-theme`.
Before submitting, publish the intended commit, manually test that exact commit
as a dev extension in Zed, and run the checks above. In a fork of
`zed-industries/extensions`, add this repository as the HTTPS Git submodule
`extensions/catppuccin-frappe-prism-theme` and add its entry to `extensions.toml`:

```toml
[catppuccin-frappe-prism-theme]
submodule = "extensions/catppuccin-frappe-prism-theme"
version = "0.2.0"
```

Keep the registry version equal to this repository's `extension.toml`, pin the
tested submodule commit, and run the registry's `pnpm sort-extensions` command.
Explain Prism's role distinctions and typography when requesting review.
Submission and repository CI do not guarantee acceptance. Update the README's
catalogue status only after listing is observed. Future updates need a new
manifest version and a registry PR advancing the submodule to the tested commit.
