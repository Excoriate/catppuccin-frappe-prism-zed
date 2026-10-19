#!/usr/bin/env python3
"""Validate the theme package and run its finite regression controls.

Only the Python 3.11+ standard library is needed. This checks package metadata
and the palette contract; native Zed remains the rendering and capture oracle.
"""

import sys

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required: python3 scripts/check.py")

# Checks and imports must not create files in a contributor's working tree.
sys.dont_write_bytecode = True

import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "Catppuccin Frappé Prism"
EXTENSION_ID = "catppuccin-frappe-prism-theme"
REPOSITORY = "https://github.com/Excoriate/catppuccin-frappe-prism-zed"
THEME_PATH = Path("themes/catppuccin-frappe-prism.json")
COLOR = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
MANIFEST_FIELDS = {
    "id", "name", "version", "schema_version", "authors", "description", "repository"
}
# The grant, inclusion condition and disclaimer are independent of mutable files.
# Copyright years/owners may be maintained without changing these MIT terms.
MIT_TERMS = """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
# A conservative sRGB code-value margin, not a perceptual-uniformity standard.
MIN_ROLE_DISTANCE = 20
ROLE_PAIRS = (
    ("variable", "function.call"),
    ("variable.parameter", "variable"),
    ("variable.member", "function.method.call"),
    ("function.definition", "function.call"),
    ("function.method.definition", "function.method.call"),
    ("constructor.definition", "constructor"),
    ("constructor.definition", "type"),
    ("type", "keyword"),
    ("type.builtin", "type"),
    ("type.interface", "type"),
    ("property", "attribute"),
    ("namespace", "attribute"),
    ("type", "label"),
    ("number", "boolean"),
    ("string", "string.escape"),
    ("operator", "punctuation.delimiter"),
    ("config.section", "config.key"),
    ("config.section.array", "config.section"),
    ("config.key", "string"),
    ("config.path", "config.key"),
    ("config.null", "number.integer"),
    ("config.anchor", "config.alias"),
    ("config.alias", "config.tag"),
    ("number.integer", "number.float"),
    ("string.quoted.single", "string.quoted.double"),
    ("string.block.literal", "string.block.folded"),
    ("datetime.date", "datetime.time"),
    ("punctuation.mapping", "punctuation.sequence"),
    ("argument.flag", "constant"),
    ("argument.flag", "function.builtin"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def regular_file(root, relative):
    path = root / relative
    require(path.is_file() and not path.is_symlink(), f"missing regular file: {relative}")
    require(not any(p.is_symlink() for p in path.parents if p != root.parent),
            f"symlink in package path: {relative}")
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def color(value, label, opaque=False):
    require(isinstance(value, str) and COLOR.fullmatch(value) is not None,
            f"{label}: expected #RRGGBB or #RRGGBBAA color")
    require(not opaque or len(value) == 7, f"{label}: expected opaque #RRGGBB")
    return value.lower()


def luminance(value):
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def composite(foreground, background, opacity):
    """Composite opaque sRGB colors before measuring the rendered glyph contrast."""
    channels = [round(int(foreground[i:i + 2], 16) * opacity +
                      int(background[i:i + 2], 16) * (1 - opacity)) for i in (1, 3, 5)]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def green(value, label):
    value = color(value, label, opaque=True)
    red, channel_green, blue = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    require(channel_green > red and channel_green > blue, f"{label}: expected a green background")
    return value


def validate_settings(root, syntax):
    """Check the documented example, not arbitrary user settings or Zed's full schema."""
    path = regular_file(root, "examples/settings.json")
    settings = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    expected = {"theme", "semantic_tokens", "minimum_contrast_for_highlights",
                "selection_highlight", "global_lsp_settings", "lsp"}
    require(isinstance(settings, dict) and set(settings) == expected,
            "optional settings: expected documented profile keys only")
    theme = settings["theme"]
    require(isinstance(theme, dict) and set(theme) == {"mode", "dark", "light"} and
            theme["mode"] == "dark" and theme["dark"] == NAME and
            isinstance(theme["light"], str) and theme["light"].strip(),
            "optional settings: invalid theme selection")
    require(settings["semantic_tokens"] == "combined", "optional settings: semantic_tokens must be combined")
    require(type(settings["minimum_contrast_for_highlights"]) is int and
            settings["minimum_contrast_for_highlights"] == 75,
            "optional settings: expected documented contrast value 75")
    require(settings["selection_highlight"] is False, "optional settings: selection_highlight must be false")
    global_lsp = settings["global_lsp_settings"]
    require(isinstance(global_lsp, dict) and set(global_lsp) == {"semantic_token_rules"},
            "optional settings: expected semantic_token_rules only in global_lsp_settings")
    rules = global_lsp["semantic_token_rules"]
    require(isinstance(rules, list) and rules, "optional settings: semantic_token_rules must be a nonempty list")
    filters = []
    for index, rule in enumerate(rules):
        label = f"semantic rule {index + 1}"
        allowed = {"token_type", "token_modifiers", "style", "font_weight", "font_style"}
        require(isinstance(rule, dict) and set(rule) <= allowed, f"{label}: invalid rule fields")
        token_type = rule.get("token_type")
        require("token_type" not in rule or (isinstance(token_type, str) and token_type.strip()),
                f"{label}: token_type must be a nonempty string")
        modifiers = rule.get("token_modifiers", [])
        require(isinstance(modifiers, list) and
                all(isinstance(m, str) and m.strip() for m in modifiers) and
                len(set(modifiers)) == len(modifiers), f"{label}: invalid token_modifiers")
        styles = rule.get("style")
        require(isinstance(styles, list) and styles and
                all(isinstance(s, str) and s in syntax for s in styles),
                f"{label}: unknown semantic style or invalid style list")
        require("font_weight" not in rule or rule["font_weight"] in ("normal", "bold"),
                f"{label}: expected normal or bold named font_weight in this profile")
        require("font_style" not in rule or rule["font_style"] in ("normal", "italic", "oblique"),
                f"{label}: invalid font_style")
        required = set(modifiers)
        for prior_index, (prior_type, prior_modifiers) in enumerate(filters):
            # Both selectors are conjunctions. A prior wildcard/equal type with
            # fewer required modifiers covers every token the later rule could match.
            subsumed = (prior_type is None or prior_type == token_type) and prior_modifiers <= required
            require(not subsumed,
                    f"{label}: fully shadowed by earlier semantic rule {prior_index + 1}")
        filters.append((token_type, required))
    lsp = settings["lsp"]
    require(isinstance(lsp, dict) and set(lsp) == {"gopls"}, "optional settings: expected only the gopls enablement")
    gopls = lsp["gopls"]
    require(isinstance(gopls, dict) and set(gopls) == {"initialization_options"},
            "optional settings: invalid gopls profile")
    options = gopls["initialization_options"]
    require(isinstance(options, dict) and set(options) == {"semanticTokens"} and options["semanticTokens"] is True,
            "optional settings: gopls semanticTokens must be true")
    return len(rules)


def validate_repository(root):
    """Raise ValueError/OSError for a broken package; return palette statistics."""
    root = Path(root).resolve()
    manifest = tomllib.loads(regular_file(root, "extension.toml").read_text(encoding="utf-8"))
    require(set(manifest) == MANIFEST_FIELDS, "manifest: expected exactly seven standard fields")
    require(manifest["id"] == EXTENSION_ID, "manifest: extension id drift")
    require(manifest["name"] == NAME, "manifest: display name drift")
    require(isinstance(manifest["version"], str) and VERSION.fullmatch(manifest["version"]),
            "manifest: version must be plain major.minor.patch without leading zeros")
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
            "manifest: schema_version must be integer 1")
    authors = manifest["authors"]
    require(isinstance(authors, list) and authors and
            all(isinstance(a, str) and a.strip() for a in authors),
            "manifest: authors must be a nonempty list of names")
    description = manifest["description"]
    require(isinstance(description, str) and len(description.strip()) > len(NAME),
            "manifest: description must be longer than the display name")
    require(manifest["repository"] == REPOSITORY, "manifest: repository URL drift")
    for forbidden in ("Cargo.toml", "Cargo.lock", "languages", "grammars", "extension.wasm"):
        require(not (root / forbidden).exists() and not (root / forbidden).is_symlink(),
                f"theme-only package: unexpected {forbidden}")
    # Documentation and examples are allowed; executable language providers are not.
    for path in root.rglob("*.wasm"):
        if ".git" not in path.relative_to(root).parts:
            raise ValueError(f"theme-only package: unexpected {path.relative_to(root)}")

    notices = []
    for relative in ("LICENSE", "themes/LICENSE.catppuccin"):
        text = regular_file(root, relative).read_text(encoding="utf-8")
        require(text.strip().endswith(MIT_TERMS),
                f"{relative}: retained MIT copyright and permission notice required: complete canonical MIT grant/disclaimer")
        header = text.strip()[:-len(MIT_TERMS)].strip()
        require(header.startswith("MIT License\n") and
                re.search(r"^Copyright \(c\) [0-9]{4}(?:-[0-9]{4})? \S.*$", header, re.MULTILINE),
                f"{relative}: MIT heading and copyright year/owner required")
        require(relative != "themes/LICENSE.catppuccin" or "Copyright (c) 2021 Catppuccin" in header,
                "upstream copyright notice must retain Copyright (c) 2021 Catppuccin")
        notices.append(text.strip())

    theme_path = regular_file(root, THEME_PATH)
    discovered = sorted((root / "themes").glob("*.json"))
    require(discovered == [theme_path], "theme discovery: expected one theme JSON at the documented path")
    family = json.loads(theme_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(family, dict), "theme family must be an object")
    embedded_license = family.get("license")
    require(isinstance(embedded_license, str) and embedded_license.strip() == "\n\n".join(notices),
            "embedded license must retain both complete source MIT notices")
    require(family.get("$schema") == "https://zed.dev/schema/themes/v0.2.0.json", "theme schema drift")
    require(family.get("name") == NAME, "theme family name drift")
    require(isinstance(family.get("author"), str) and family["author"].strip(), "theme author required")
    themes = family.get("themes")
    require(isinstance(themes, list) and len(themes) == 1 and isinstance(themes[0], dict),
            "theme family must contain exactly one theme")
    theme = themes[0]
    require(theme.get("name") == NAME, "theme name drift")
    require(theme.get("appearance") == "dark", "theme appearance must be dark")
    style = theme.get("style")
    require(isinstance(style, dict), "theme style must be an object")
    require("scrollbar_thumb.background" not in style, "deprecated scrollbar_thumb.background")
    for key, value in style.items():
        if key not in ("syntax", "players", "accents", "background.appearance") and value is not None:
            color(value, key)
    require(style.get("background.appearance") in ("opaque", "transparent", "blurred"),
            "background.appearance must be a supported appearance")
    accents = style.get("accents")
    require(isinstance(accents, list) and accents, "accents must be a nonempty color list")
    for value in accents:
        color(value, "accent")
    backgrounds = [luminance(color(style.get(key), key, opaque=True)) for key in
                   ("editor.background", "editor.active_line.background")]
    color(style.get("editor.foreground"), "editor.foreground", opaque=True)
    players = style.get("players")
    require(isinstance(players, list) and players, "players must be a nonempty list")
    for index, player in enumerate(players):
        require(isinstance(player, dict), f"player {index}: expected an object")
        for key in ("cursor", "selection", "background"):
            color(player.get(key), f"player {index} {key}")
    selection = green(players[0]["selection"], "primary selection")
    require(selection == "#9ad99e", "primary selection must remain #9ad99e")
    read = color(style.get("editor.document_highlight.read_background"), "read highlight", opaque=True)
    write = color(style.get("editor.document_highlight.write_background"), "write highlight", opaque=True)
    require(read == write, "read/write highlight backgrounds must match")
    require(read != selection, "document highlights must differ from primary selection")
    for key in ("search.match_background", "search.active_match_background"):
        require(read != color(style.get(key), key)[:7],
                "document highlights must differ from search backgrounds")
    require(read == "#babbf1", "document highlights must use Frappé lavender #babbf1")

    ansi_names = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
    terminal_keys = ["terminal.background", "terminal.ansi.background", "terminal.foreground",
                     "terminal.bright_foreground", "terminal.dim_foreground"]
    terminal_keys.extend(f"terminal.ansi.{prefix}{name}"
                         for prefix in ("", "bright_", "dim_") for name in ansi_names)
    for key in terminal_keys:
        require(key in style, f"terminal palette missing required key: {key}")
    require({key for key in style if key.startswith("terminal.")} == set(terminal_keys),
            "terminal palette contains unsupported color keys")
    terminal = {key: color(style[key], key, opaque=True) for key in terminal_keys}
    background = terminal["terminal.background"]
    require(background == terminal["terminal.ansi.background"], "terminal and ANSI backgrounds must match")
    require(background == "#080c14", "terminal background must remain #080c14")
    for prefix in ("", "bright_", "dim_"):
        require(len({terminal[f"terminal.ansi.{prefix}{name}"] for name in ansi_names}) == len(ansi_names),
                f"terminal {prefix or 'normal'} ANSI colors must remain distinct")
    require(terminal["terminal.ansi.green"] == "#33e890", "terminal ANSI green must remain #33e890")
    terminal_background = luminance(background)
    terminal_ratios = []
    for key, value in terminal.items():
        if key.endswith("background"):
            continue
        is_dim = key == "terminal.dim_foreground" or key.startswith("terminal.ansi.dim_")
        # Zed v1.24.2 multiplies dim glyph alpha by 0.7 after foreground contrast handling.
        foreground = luminance(composite(value, background, 0.7) if is_dim else value)
        ratio = (max(foreground, terminal_background) + 0.05) / (min(foreground, terminal_background) + 0.05)
        terminal_ratios.append(ratio)
        label = "composited dim contrast" if is_dim else "contrast"
        require(ratio >= 4.5, f"{key}: {label} {ratio:.2f}:1 is below 4.5:1")
    require(terminal["terminal.foreground"] == "#39ff88", "terminal foreground must remain neon green #39ff88")
    for name in ansi_names:
        normal = terminal[f"terminal.ansi.{name}"]
        bright = terminal[f"terminal.ansi.bright_{name}"]
        dim = composite(terminal[f"terminal.ansi.dim_{name}"], background, 0.7)
        require(len({normal, bright, dim}) == 3,
                f"terminal ANSI {name}: normal, bright and effective dim must differ")
        require(luminance(dim) < luminance(normal) < luminance(bright),
                f"terminal ANSI {name}: expected effective dim < normal < bright luminance")

    syntax = style.get("syntax")
    require(isinstance(syntax, dict) and syntax, "syntax must be a nonempty object")
    ratios = []
    for scope, token in syntax.items():
        require(isinstance(token, dict), f"{scope}: syntax style must be an object")
        require(set(token) <= {"color", "font_style", "font_weight"}, f"{scope}: unknown syntax style field")
        foreground = luminance(color(token.get("color"), scope, opaque=True))
        require(token.get("font_style") in (None, "normal", "italic", "oblique"),
                f"{scope}: invalid font_style")
        weight = token.get("font_weight")
        require(weight is None or (type(weight) is int and weight in range(100, 901, 100)),
                f"{scope}: invalid font_weight")
        for background in backgrounds:
            ratio = (max(foreground, background) + 0.05) / (min(foreground, background) + 0.05)
            ratios.append(ratio)
            require(ratio >= 4.5, f"{scope}: contrast {ratio:.2f}:1 is below 4.5:1")
    distances = []
    for first, second in ROLE_PAIRS:
        require(first in syntax and second in syntax, f"required role missing: {first} / {second}")
        require(syntax[first]["color"].lower() != syntax[second]["color"].lower(),
                f"indistinguishable color: {first} / {second}")
        a, b = syntax[first]["color"], syntax[second]["color"]
        distance = sum((int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) ** 2 for i in (1, 3, 5)) ** 0.5
        distances.append(distance)
        require(distance >= MIN_ROLE_DISTANCE,
                f"role color distance below {MIN_ROLE_DISTANCE}: {first} / {second} ({distance:.2f})")
    for scope in ("function.definition", "function.method.definition", "constructor.definition", "config.section"):
        require((syntax[scope].get("font_weight") or 400) >= 600, f"{scope}: declaration emphasis missing")
    require(syntax["variable.parameter"].get("font_style") == "italic", "parameter italic distinction missing")
    rule_count = validate_settings(root, syntax)
    return {"scopes": len(syntax), "colors": len({s["color"].lower() for s in syntax.values()}),
            "minimum_contrast": min(ratios), "role_pairs": len(ROLE_PAIRS),
            "minimum_role_distance": min(distances), "semantic_rules": rule_count,
            "terminal_colors": len(terminal), "minimum_terminal_contrast": min(terminal_ratios)}


def main():
    try:
        result = validate_repository(ROOT)
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f"Package check failed: {error}", file=sys.stderr)
        return 1
    print(f"Package: {EXTENSION_ID}; {result['scopes']} scopes, {result['colors']} colors, "
          f"minimum contrast {result['minimum_contrast']:.2f}:1, {result['role_pairs']} role pairs")
    print(f"Protected-pair minimum sRGB distance: {result['minimum_role_distance']:.2f} (floor {MIN_ROLE_DISTANCE}); "
          f"optional profile: {result['semantic_rules']} semantic rules")
    print(f"Terminal: {result['terminal_colors']} colors, minimum normal/bright/rendered-dim contrast "
          f"{result['minimum_terminal_contrast']:.2f}:1; lavender document highlights distinct from green selection")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_check.py")
    require(suite.countTestCases() > 0, "regression controls are missing")
    tests = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    if not tests.wasSuccessful():
        return 1
    print("Native Zed loading, capture coverage, selection rendering and registry acceptance require separate review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
