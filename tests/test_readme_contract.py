import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import APPS, CLONE_APPS, MONOREPO  # noqa: E402
import check  # noqa: E402

CLONE_COMMAND = '[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"'
REMOVE_CLONE = 'rm -rf "$HOME/.config/apollo-theme"'
REMOVAL_FORMS = (
    'rm -rf "$HOME/.config/apollo-theme"',
    'rm -fr "$HOME/.config/apollo-theme"',
    'rm -Rf "$HOME/.config/apollo-theme"',
    'rm -r -f "$HOME/.config/apollo-theme"',
    'rm -r "$HOME/.config/apollo-theme"',
    'rm -R $HOME/.config/apollo-theme/',
    'rm --recursive --force "$HOME/.config/apollo-theme"',
    'rm --force --recursive -- "$HOME/.config/apollo-theme/"',
    'rm -rf -- ~/.config/apollo-theme/',
    'rm -rf ${HOME}/.config/apollo-theme',
    'rm -rf "${HOME}/.config/apollo-theme/"',
    'rm -rf $HOME/.config/apollo-theme',
    'command rm -rf "$HOME/.config/apollo-theme" && echo done',
    'rm -rf "$HOME/.cache/x" "$HOME/.config/apollo-theme"',
    'Remove-Item -Recurse -Force "$HOME/.config/apollo-theme"',
    'Remove-Item "$HOME\\.config\\apollo-theme" -Recurse',
    'Remove-Item -LiteralPath $env:HOME/.config/apollo-theme/ -Recurse -Force',
    'remove-item -recurse ~/.config/apollo-theme',
)
NON_REMOVAL_FORMS = (
    'rm -rf "$HOME/.config/apollo-theme/bat/x"',
    'rm -rf ~/.config/apollo-theme/.installed-theme-hashes',
    'rm -rf "$HOME/.config/apollo-theme-old"',
    'rm -f "$HOME/.config/bat/themes/Apollo.tmTheme"',
    'Remove-Item -Recurse "$HOME/.config/apollo-theme/powershell/x"',
    'Remove-Item "$HOME/.config/apollo-theme/x.ps1"',
)
CLONE_NAMES = ", ".join(APPS[slug]["name"] for slug in CLONE_APPS)


def install_heading(slug: str) -> str:
    return APPS[slug]["install_anchor"].replace("-", " ").capitalize()


def valid_readme(slug: str, *, clone: str = CLONE_COMMAND, uninstall: str = "rm -f \"$HOME/.config/bat/themes/Apollo.tmTheme\"", remove_section: str | None = None, markers: tuple[str, ...] = ("install", "uninstall")) -> str:
    app = APPS[slug]
    header = f"""<h1 align="center">{app['name']} Apollo Theme</h1>

<p align="center">
  <a href="{MONOREPO}/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main"></a>
  <a href="{MONOREPO}/releases"><img alt="Release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter={slug}-v*"></a>
  <a href="{MONOREPO}/blob/main/{slug}/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-b8bb26"></a>
  <img alt="Target" src="https://img.shields.io/badge/{app['badge_fragment']}83a598">
  <img alt="Palette" src="https://img.shields.io/badge/palette-canonical-fabd2f">
  <a href="https://apollo-theme.github.io/"><img alt="Preview" src="https://img.shields.io/badge/preview-site-d3869b"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-{slug}"><img alt="Simulated preview of Apollo Dark" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{slug}.svg"></a>
  <a href="https://apollo-theme.github.io/#app-{slug}-light"><img alt="Simulated preview of Apollo Light" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{slug}-light.svg"></a>
</p>

Both Apollo Dark and Apollo Light are included.

## {install_heading(slug)}

"""
    if slug not in CLONE_APPS:
        return header + "Copy the theme files into place.\n"
    install_marker = "<!-- smoke:install -->\n" if "install" in markers else ""
    uninstall_marker = "<!-- smoke:uninstall -->\n" if "uninstall" in markers else ""
    if remove_section is None:
        remove_section = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `{REMOVE_CLONE}`.\n"
    return (
        header
        + f"{install_marker}```sh\n{clone}\nmkdir -p \"$HOME/.config/bat/themes\"\n```\n\n"
        + f"## Uninstall\n\n{uninstall_marker}```sh\n{uninstall}\n```\n\n"
        + remove_section
    )


def run(slug: str, readme: str, claude: str = "", metadata: str = "") -> None:
    check.check_readme_contract(slug, readme, claude=claude, metadata=metadata)


class ReadmeContractTests(unittest.TestCase):
    def test_valid_clone_app_readme_passes(self):
        run("bat", valid_readme("bat"))

    def test_valid_non_clone_app_needs_no_clone_rules(self):
        readme = valid_readme("xcode")
        self.assertNotIn(".config/apollo-theme", readme)
        self.assertNotIn("smoke:", readme)
        run("xcode", readme)

    def test_missing_shared_clone_command_fails(self):
        with self.assertRaisesRegex(ValueError, "shared clone install command"):
            run("bat", valid_readme("bat", clone='git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"'))

    def test_clone_removal_inside_uninstall_fails(self):
        with self.assertRaisesRegex(ValueError, "Uninstall"):
            run("bat", valid_readme("bat", uninstall=f"rm -f x\n{REMOVE_CLONE}"))

    def test_missing_remove_shared_clone_section_fails(self):
        with self.assertRaisesRegex(ValueError, "Remove the shared clone section"):
            run("bat", valid_readme("bat", remove_section=""))

    def test_remove_section_omitting_a_clone_app_fails(self):
        for slug in CLONE_APPS:
            name = APPS[slug]["name"]
            names = ", ".join(APPS[other]["name"] for other in CLONE_APPS if other != slug)
            section = f"## Remove the shared clone\n\n{names} all read from `~/.config/apollo-theme`. Then run `{REMOVE_CLONE}`.\n"
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, rf"'{name}'"):
                run("bat", valid_readme("bat", remove_section=section))

    def test_remove_section_without_removal_command_fails(self):
        section = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`.\n"
        with self.assertRaisesRegex(ValueError, "Remove the shared clone command"):
            run("bat", valid_readme("bat", remove_section=section))

    def test_missing_smoke_markers_fail(self):
        for marker in ("install", "uninstall"):
            kept = tuple(other for other in ("install", "uninstall") if other != marker)
            with self.subTest(marker=marker), self.assertRaisesRegex(ValueError, f"smoke:{marker} block"):
                run("bat", valid_readme("bat", markers=kept))

    def test_old_workflow_and_release_badges_fail(self):
        readme = valid_readme("bat")
        old = readme.replace("status/apollo-theme/apollo-theme/ci.yml", "status/apollo-theme/apollo-theme/check.yml")
        with self.assertRaisesRegex(ValueError, "workflow badge"):
            run("bat", old)
        old = readme.replace("?filter=bat-v", "?filter=xcode-v")
        with self.assertRaisesRegex(ValueError, "release badge"):
            run("bat", old)

    def test_release_badge_filter_must_be_a_glob(self):
        exact = valid_readme("bat").replace("?filter=bat-v*", "?filter=bat-v")
        with self.assertRaisesRegex(ValueError, "release badge"):
            run("bat", exact)

    def test_release_search_links_use_whole_words(self):
        # GitHub's release search matches whole words, so a "-v" suffixed query finds nothing.
        suffixed = "bat" + "-v"
        broken = valid_readme("bat") + f'\n<a href="{MONOREPO}/releases?q={suffixed}">releases</a>\n'
        with self.assertRaisesRegex(ValueError, "release search"):
            run("bat", broken)
        run("bat", valid_readme("bat") + f'\n<a href="{MONOREPO}/releases?q=bat">releases</a>\n')

    def test_license_link_must_be_local_or_monorepo_path(self):
        readme = valid_readme("bat")
        run("bat", readme.replace(f"{MONOREPO}/blob/main/bat/LICENSE", "LICENSE"))
        with self.assertRaisesRegex(ValueError, "license link"):
            run("bat", readme.replace(f"{MONOREPO}/blob/main/bat/LICENSE", f"{MONOREPO}/blob/main/LICENSE"))

    def test_per_app_repository_urls_fail_everywhere(self):
        dead = "https://github.com/apollo-theme/bat-apollo-theme"
        for slug in ("bat", "xcode"):
            readme = valid_readme(slug)
            for source in ("readme", "claude", "metadata"):
                texts = {"readme": readme, "claude": "", "metadata": ""}
                texts[source] += f"\nSee {dead}/releases.\n"
                with self.subTest(slug=slug, source=source), self.assertRaisesRegex(ValueError, "bat-apollo-theme"):
                    run(slug, texts["readme"], claude=texts["claude"], metadata=texts["metadata"])

    def test_monorepo_and_site_urls_are_not_dead(self):
        run("bat", valid_readme("bat"), claude=f"{MONOREPO}/tree/main/bat and https://github.com/apollo-theme/apollo-theme.github.io")

    def test_every_removal_form_is_rejected_outside_remove_section(self):
        for form in REMOVAL_FORMS:
            with self.subTest(form=form), self.assertRaisesRegex(ValueError, "removed outside.*Uninstall"):
                run("bat", valid_readme("bat", uninstall=f"rm -f x\n{form}"))

    def test_every_removal_form_is_allowed_in_remove_section(self):
        for form in REMOVAL_FORMS:
            section = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`.\n\n```sh\n{form}\n```\n"
            with self.subTest(form=form):
                run("bat", valid_readme("bat", remove_section=section))

    def test_subpath_and_sibling_deletions_are_not_clone_removal(self):
        for form in NON_REMOVAL_FORMS:
            with self.subTest(form=form):
                run("bat", valid_readme("bat", uninstall=form))
            section = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`.\n\n```sh\n{form}\n```\n"
            with self.subTest(form=form, where="remove section"), self.assertRaisesRegex(ValueError, "Remove the shared clone command"):
                run("bat", valid_readme("bat", remove_section=section))

    def test_removal_in_first_of_duplicate_uninstall_sections_fails(self):
        readme = valid_readme("bat", uninstall=REMOVE_CLONE).replace(
            "## Remove the shared clone", "## Uninstall\n\nNothing else to remove.\n\n## Remove the shared clone"
        )
        self.assertEqual(2, readme.count("## Uninstall"))
        with self.assertRaisesRegex(ValueError, "removed outside.*Uninstall"):
            run("bat", readme)

    def test_removal_in_preamble_fails(self):
        readme = valid_readme("bat").replace(
            "Both Apollo Dark and Apollo Light are included.",
            f"Both Apollo Dark and Apollo Light are included.\n\n```sh\n{REMOVE_CLONE}\n```",
        )
        with self.assertRaisesRegex(ValueError, "removed outside.*preamble"):
            run("bat", readme)

    def test_two_remove_sections_need_one_complete_and_may_both_remove(self):
        complete = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`. Then run `{REMOVE_CLONE}`.\n"
        removal_only = f"## Remove the shared clone\n\nOr: `rm -fr ~/.config/apollo-theme/`\n"
        names_only = f"## Remove the shared clone\n\n{CLONE_NAMES} all read from `~/.config/apollo-theme`.\n"
        run("bat", valid_readme("bat", remove_section=removal_only + "\n" + complete))
        run("bat", valid_readme("bat", remove_section=complete + "\n" + removal_only))
        with self.assertRaisesRegex(ValueError, "Remove the shared clone"):
            run("bat", valid_readme("bat", remove_section=names_only + "\n" + removal_only))


if __name__ == "__main__":
    unittest.main()
