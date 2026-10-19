"""Wrong-artifact controls for the same validator used by the contributor command."""

import importlib.util
import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("theme_check", ROOT / "scripts/check.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PackageControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="prism-check-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        for relative in ("extension.toml", "LICENSE", "themes/LICENSE.catppuccin", CHECK.THEME_PATH,
                         "examples/settings.json"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def edit_theme(self, edit):
        path = self.root / CHECK.THEME_PATH
        theme = json.loads(path.read_text(encoding="utf-8"))
        edit(theme["themes"][0])
        path.write_text(json.dumps(theme, ensure_ascii=False), encoding="utf-8")

    def reject(self, diagnostic):
        with self.assertRaisesRegex(ValueError, diagnostic):
            CHECK.validate_repository(self.root)

    def test_unmodified_package_and_documentation_are_valid(self):
        (self.root / "examples/notes.json").write_text('{}\n', encoding="utf-8")
        (self.root / "README.md").write_text('Theme documentation.\n', encoding="utf-8")
        self.assertGreaterEqual(CHECK.validate_repository(self.root)["minimum_contrast"], 4.5)

    def test_malformed_json_and_duplicate_keys_are_rejected(self):
        path = self.root / CHECK.THEME_PATH
        path.write_text('{"themes": [', encoding="utf-8")
        self.reject("Expecting")
        path.write_text('{"name": "one", "name": "two"}', encoding="utf-8")
        self.reject("duplicate JSON key")

    def test_invalid_color_is_rejected(self):
        self.edit_theme(lambda t: t["style"]["syntax"]["variable"].update(color="#zzzzzz"))
        self.reject("variable: expected #RRGGBB")

    def test_valid_but_low_contrast_color_is_rejected(self):
        self.edit_theme(lambda t: t["style"]["syntax"]["variable"].update(color=t["style"]["editor.background"]))
        self.reject("variable: contrast 1.00:1")

    def test_valid_colors_cannot_collapse_key_and_string_roles(self):
        self.edit_theme(lambda t: t["style"]["syntax"]["config.key"].update(t["style"]["syntax"]["string"]))
        self.reject("indistinguishable color: config.key / string")

    def test_declaration_emphasis_cannot_disappear(self):
        self.edit_theme(lambda t: t["style"]["syntax"]["function.definition"].update(font_weight=400))
        self.reject("function.definition: declaration emphasis missing")

    def test_null_style_resets_are_valid_but_boolean_weights_are_not(self):
        self.edit_theme(lambda t: t["style"]["syntax"]["variable"].update(font_style=None, font_weight=None))
        CHECK.validate_repository(self.root)
        self.edit_theme(lambda t: t["style"]["syntax"]["variable"].update(font_weight=True))
        self.reject("variable: invalid font_weight")

    def test_manifest_identity_version_and_missing_field_drift(self):
        path = self.root / "extension.toml"
        original = path.read_text(encoding="utf-8")
        version = tomllib.loads(original)["version"]
        for before, after, diagnostic in (
            ('id = "catppuccin-frappe-prism-theme"', 'id = "another-theme"', "extension id drift"),
            (f'version = "{version}"', f'version = "v{version}"', "version must be plain"),
            (f'version = "{version}"', f'version = "0{version}"', "version must be plain"),
            ('schema_version = 1', 'schema_version = true', "schema_version must be integer"),
            ('authors = ["Alex Torres Ruiz"]', '', "exactly seven standard fields"),
            (CHECK.REPOSITORY, 'https://github.com/example/wrong-theme', "repository URL drift"),
        ):
            with self.subTest(diagnostic=diagnostic, replacement=after):
                path.write_text(original.replace(before, after), encoding="utf-8")
                self.reject(diagnostic)

    def test_cargo_languages_grammars_and_wasm_are_not_theme_features(self):
        for relative in ("Cargo.toml", "Cargo.lock", "languages", "grammars", "extension.wasm", "nested/provider.wasm"):
            with self.subTest(path=relative):
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative in ("languages", "grammars"):
                    path.mkdir()
                    self.reject("theme-only package")
                    path.rmdir()
                else:
                    path.write_bytes(b"not a theme")
                    self.reject("theme-only package")
                    path.unlink()

    def test_language_server_manifest_declaration_is_rejected(self):
        path = self.root / "extension.toml"
        path.write_text(path.read_text(encoding="utf-8") + '\n[language_servers.extra]\nlanguages = ["Extra"]\n', encoding="utf-8")
        self.reject("exactly seven standard fields")

    def test_wrong_appearance_and_missing_discoverable_theme_are_rejected(self):
        self.edit_theme(lambda t: t.update(appearance="light"))
        self.reject("appearance must be dark")
        (self.root / CHECK.THEME_PATH).rename(self.root / "theme.json")
        self.reject("missing regular file")

    def test_primary_selection_keeps_its_own_green(self):
        self.edit_theme(lambda t: t["style"]["players"][0].update(selection="#a6d189"))
        self.reject("primary selection must remain #9ad99e")

    def test_read_write_occurrence_backgrounds_must_match(self):
        self.edit_theme(lambda t: t["style"].update({"editor.document_highlight.write_background": "#ca9ee6"}))
        self.reject("read/write highlight backgrounds must match")

    def test_occurrences_keep_opaque_lavender_distinct_from_primary_selection(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for value, diagnostic in (
            ("#9ad99e", "document highlights must differ from primary selection"),
            ("#86c58c", "document highlights must use Frappé lavender #babbf1"),
            ("#85c1dc", "document highlights must use Frappé lavender #babbf1"),
            ("#babbf180", "read highlight: expected opaque #RRGGBB"),
        ):
            with self.subTest(value=value):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].update({
                    "editor.document_highlight.read_background": value,
                    "editor.document_highlight.write_background": value,
                }))
                self.reject(diagnostic)

    def test_occurrences_cannot_merge_with_either_search_background(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for key in ("search.match_background", "search.active_match_background"):
            with self.subTest(key=key):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].update({
                    "editor.document_highlight.read_background": "#babbf1",
                    "editor.document_highlight.write_background": "#babbf1",
                    key: "#babbf14d",
                }))
                self.reject("document highlights must differ from search backgrounds")

    def test_every_supported_terminal_color_is_required(self):
        keys = ["terminal.background", "terminal.ansi.background", "terminal.foreground",
                "terminal.bright_foreground", "terminal.dim_foreground"]
        keys.extend(f"terminal.ansi.{prefix}{name}"
                    for prefix in ("", "bright_", "dim_")
                    for name in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"))
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for key in keys:
            with self.subTest(key=key):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].pop(key))
                self.reject(f"terminal palette missing required key: {key}")

    def test_terminal_colors_are_valid_opaque_hex_and_supported_keys(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for edit, diagnostic in (
            ({"terminal.ansi.green": "#zzzzzz"}, "terminal.ansi.green: expected #RRGGBB"),
            ({"terminal.ansi.green": "#39ff8880"}, "terminal.ansi.green: expected opaque #RRGGBB"),
            ({"terminal.cursor": "#39ff88"}, "terminal palette contains unsupported color keys"),
        ):
            with self.subTest(edit=edit):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].update(edit))
                self.reject(diagnostic)

    def test_terminal_backgrounds_match_the_retro_palette(self):
        self.edit_theme(lambda t: t["style"].update({"terminal.ansi.background": "#090d15"}))
        self.reject("terminal and ANSI backgrounds must match")
        self.edit_theme(lambda t: t["style"].update({
            "terminal.background": "#303446", "terminal.ansi.background": "#303446",
        }))
        self.reject("terminal background must remain #080c14")

    def test_terminal_keeps_neon_green_and_visible_default_and_black_text(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for key, value, diagnostic in (
            ("terminal.ansi.green", "#a6d189", "terminal ANSI green must remain #33e890"),
            ("terminal.foreground", "#a6d189", "terminal foreground must remain neon green #39ff88"),
            ("terminal.foreground", "#080c14", "terminal.foreground: contrast 1.00:1 is below 4.5:1"),
            ("terminal.ansi.black", "#080c14", "terminal.ansi.black: contrast 1.00:1 is below 4.5:1"),
        ):
            with self.subTest(key=key):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].update({key: value}))
                self.reject(diagnostic)

    def test_dim_compositing_uses_the_terminal_background_and_native_opacity(self):
        self.assertEqual(CHECK.composite("#c8c8c8", "#646464", 0.7), "#aaaaaa")
        self.assertEqual(CHECK.composite("#c8c8c8", "#646464", 0), "#646464")
        self.assertEqual(CHECK.composite("#c8c8c8", "#646464", 1), "#c8c8c8")
        for key in ("terminal.dim_foreground", "terminal.ansi.dim_black", "terminal.ansi.dim_red"):
            with self.subTest(key=key):
                self.edit_theme(lambda t: t["style"].update({key: "#70809d"}))
                self.reject(f"{key}: composited dim contrast .* is below 4.5:1")
                shutil.copyfile(ROOT / CHECK.THEME_PATH, self.root / CHECK.THEME_PATH)

    def test_terminal_ansi_palettes_cannot_flatten_or_reverse_brightness(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        for prefix in ("", "bright_", "dim_"):
            with self.subTest(prefix=prefix):
                path.write_text(original, encoding="utf-8")
                self.edit_theme(lambda t: t["style"].update({
                    f"terminal.ansi.{prefix}{name}": "#dce3fa"
                    for name in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
                }))
                self.reject("ANSI colors must remain distinct")
        path.write_text(original, encoding="utf-8")
        self.edit_theme(lambda t: t["style"].update({
            "terminal.ansi.bright_red": t["style"]["terminal.ansi.red"],
        }))
        self.reject("terminal ANSI red: normal, bright and effective dim must differ")
        path.write_text(original, encoding="utf-8")
        self.edit_theme(lambda t: t["style"].update({
            "terminal.ansi.bright_red": "#dd4569",
        }))
        self.reject("terminal ANSI red: expected effective dim < normal < bright luminance")

    def test_upstream_copyright_notice_is_retained(self):
        path = self.root / "themes/LICENSE.catppuccin"
        path.write_text('MIT License\n', encoding="utf-8")
        self.reject("retained MIT copyright and permission notice required")

    def test_embedded_license_retains_complete_notices_with_only_outer_whitespace_normalized(self):
        path = self.root / CHECK.THEME_PATH
        family = json.loads(path.read_text(encoding="utf-8"))
        original = family["license"]
        family["license"] = " \n" + original + "\n "
        family["project_metadata"] = {"note": "Unknown family metadata remains allowed."}
        path.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")
        CHECK.validate_repository(self.root)
        for candidate in (None, [], (self.root / "LICENSE").read_text(encoding="utf-8"),
                          "Copyright (c) 2025 Excoriate\nCopyright (c) 2021 Catppuccin",
                          original.replace("Permission is hereby granted", "Permission granted", 1),
                          original.replace("MIT License\n\n", "MIT License\n", 1)):
            with self.subTest(embedded_license_type=type(candidate).__name__, length=len(str(candidate))):
                family["license"] = candidate
                path.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")
                self.reject("embedded license must retain both complete source MIT notices")

    def test_coordinated_notice_corruption_fails_but_copyright_maintenance_is_allowed(self):
        paths = [self.root / "LICENSE", self.root / "themes/LICENSE.catppuccin"]
        originals = [p.read_text(encoding="utf-8") for p in paths]

        def set_notices(texts):
            for path, text in zip(paths, texts):
                path.write_text(text, encoding="utf-8")
            theme_path = self.root / CHECK.THEME_PATH
            family = json.loads(theme_path.read_text(encoding="utf-8"))
            family["license"] = "\n\n".join(t.strip() for t in texts)
            theme_path.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")

        truncated = [f'MIT License\n\n{t.splitlines()[2]}\n\nPermission is hereby granted, free of charge\n\n'
                     'THE SOFTWARE IS PROVIDED "AS IS"\n' for t in originals]
        for texts in (truncated,
                      [t.replace("to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n", "")
                       for t in originals],
                      [t.replace("FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n", "")
                       for t in originals]):
            with self.subTest(notice_length=len(texts[0])):
                set_notices(texts)
                self.reject("complete canonical MIT grant/disclaimer")
        maintained = [originals[0].replace("2025 Excoriate", "2026 Excoriate and contributors"), originals[1]]
        set_notices(maintained)
        CHECK.validate_repository(self.root)
        set_notices([maintained[0], originals[1].replace("2021 Catppuccin", "2026 Other owner")])
        self.reject("upstream copyright notice must retain")

    def test_role_distance_rejects_one_channel_near_clone_and_interface_collapse(self):
        path = self.root / CHECK.THEME_PATH
        original = path.read_text(encoding="utf-8")
        family = json.loads(original)
        syntax = family["themes"][0]["style"]["syntax"]
        syntax["function.call"] = dict(syntax["variable"], color="#dce3f9")
        path.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")
        self.reject("role color distance below 20: variable / function.call")
        path.write_text(original, encoding="utf-8")
        self.edit_theme(lambda t: t["style"]["syntax"]["type.interface"].update(t["style"]["syntax"]["type"]))
        self.reject("indistinguishable color: type.interface / type")

    def test_optional_settings_json_and_documented_values_are_validated(self):
        path = self.root / "examples/settings.json"
        original = path.read_text(encoding="utf-8")
        path.write_text('{"semantic_tokens": "combined", BROKEN', encoding="utf-8")
        self.reject("Expecting property name")
        for edit, diagnostic in (
            (lambda s: s.update(theme="another-theme"), "invalid theme selection"),
            (lambda s: s.update(semantic_tokens="off"), "semantic_tokens must be combined"),
            (lambda s: s.update(minimum_contrast_for_highlights=True), "contrast value 75"),
            (lambda s: s.update(selection_highlight=0), "selection_highlight must be false"),
            (lambda s: s.update(global_lsp_settings=[]), "expected semantic_token_rules only"),
            (lambda s: s.update(buffer_font_size=100), "documented profile keys only"),
            (lambda s: s["lsp"]["gopls"]["initialization_options"].update(semanticTokens=False),
             "gopls semanticTokens must be true"),
        ):
            with self.subTest(diagnostic=diagnostic):
                settings = json.loads(original)
                edit(settings)
                path.write_text(json.dumps(settings), encoding="utf-8")
                self.reject(diagnostic)

    def test_optional_rule_fields_types_and_theme_style_references_are_validated(self):
        path = self.root / "examples/settings.json"
        original = path.read_text(encoding="utf-8")
        for field, value, diagnostic in (
            ("style", "variable", "unknown semantic style or invalid style list"),
            ("style", ["undefined.scope"], "unknown semantic style or invalid style list"),
            ("token_modifiers", "declaration", "invalid token_modifiers"),
            ("token_type", 42, "token_type must be a nonempty string"),
            ("font_weight", True, "named font_weight"),
            ("font_style", "diagonal", "invalid font_style"),
            ("unknown_rule_key", True, "invalid rule fields"),
        ):
            with self.subTest(field=field, value=value):
                settings = json.loads(original)
                settings["global_lsp_settings"]["semantic_token_rules"][0][field] = value
                path.write_text(json.dumps(settings), encoding="utf-8")
                self.reject(diagnostic)

    def test_first_match_fully_shadowed_rules_fail_but_partial_overlap_and_last_catchall_pass(self):
        path = self.root / "examples/settings.json"
        original = path.read_text(encoding="utf-8")
        for earlier in ({"style": ["variable"]},
                        {"token_type": "function", "style": ["function.call"]},
                        {"token_modifiers": ["constructor"], "style": ["constructor"]}):
            with self.subTest(earlier=earlier):
                settings = json.loads(original)
                settings["global_lsp_settings"]["semantic_token_rules"].insert(0, earlier)
                path.write_text(json.dumps(settings), encoding="utf-8")
                self.reject("fully shadowed by earlier semantic rule")
        settings = json.loads(original)
        settings["global_lsp_settings"]["semantic_token_rules"] = [
            {"token_type": "function", "token_modifiers": ["declaration"], "style": ["function.definition"]},
            {"token_type": "function", "token_modifiers": ["definition"], "style": ["function.definition"]},
            {"token_type": "function", "style": ["function.call"]},
            {"style": ["variable"]},
        ]
        path.write_text(json.dumps(settings), encoding="utf-8")
        CHECK.validate_repository(self.root)


if __name__ == "__main__":
    unittest.main()
