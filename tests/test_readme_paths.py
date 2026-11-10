import json
import re
import shlex
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import SLUGS  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "readme_paths"


SHELL_FENCES = {"sh", "bash", "powershell", "pwsh"}
COPY_COMMANDS = {"cp", "Copy-Item"}
COPY_OPTIONS = {"-R", "-r", "-f", "-p", "-Force", "-Recurse", "-Path", "-LiteralPath", "-Destination"}
CONTROL_TOKENS = {"&&", "||", ";", "|"}
CLONE_PREFIXES = ("$HOME/.config/apollo-theme/", "${HOME}/.config/apollo-theme/", "~/.config/apollo-theme/")
# Documented paths that a documented build step creates inside the clone; never committed.
BUILD_OUTPUTS = ("vscode/dist/apollo-theme.vsix",)
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*([\w-]*)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.MULTILINE | re.DOTALL)
ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
LOOP = re.compile(r"^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.*?);?\s*do\s*(.*)$")
VARIABLE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")
CONFIG_PATH = re.compile(r"(?:~|\$HOME|\$\{HOME\})/\.config/apollo-theme/")


def shell_blocks(markdown: str) -> list[str]:
    return [match.group(3) for match in FENCE.finditer(markdown) if match.group(2).lower() in SHELL_FENCES]


def expand(word: str, variables: dict[str, str]) -> str:
    """Expand tracked variables; untracked ones (HOME, env:...) stay literal."""
    def substitute(match: re.Match) -> str:
        name = match.group(1) or match.group(2)
        return variables.get(name, match.group(0))
    return VARIABLE.sub(substitute, word)


def split(line: str) -> list[str] | None:
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return None


def loop_end(lines: list[str], start: int) -> int:
    """Index of the ``done`` line closing the loop opened at ``start``."""
    depth = 1
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if re.match(r"^(for|while|until)\b.*\bdo\b", stripped):
            depth += 1
        if stripped == "done" or stripped.startswith("done ") or stripped.startswith("done;"):
            depth -= 1
            if depth == 0:
                return index
    return len(lines)


def walk(lines: list[str], variables: dict[str, str], sources: list[str]) -> None:
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        loop = LOOP.match(line)
        if loop:
            name, words, inline = loop.groups()
            end = loop_end(lines, index + 1)
            body = ([inline] if inline else []) + lines[index + 1 : end]
            for value in split(words) or []:
                walk(body, {**variables, name: expand(value, variables)}, sources)
            index = end + 1
            continue
        tokens = split(line)
        if tokens:
            assignment = ASSIGNMENT.match(tokens[0]) if len(tokens) == 1 else None
            if assignment:
                variables[assignment.group(1)] = expand(assignment.group(2), variables)
            elif tokens[0] in COPY_COMMANDS:
                arguments = []
                for token in tokens[1:]:
                    if token in CONTROL_TOKENS:
                        break
                    if token not in COPY_OPTIONS:
                        arguments.append(expand(token, variables))
                sources.extend(arguments[:-1])
        index += 1


def copy_sources(markdown: str) -> list[str]:
    sources: list[str] = []
    for block in shell_blocks(markdown):
        walk(block.splitlines(), {}, sources)
    return sources


def resolve(source: str) -> Path | None:
    for prefix in CLONE_PREFIXES:
        if source.startswith(prefix):
            relative = source[len(prefix):].rstrip("/")
            parts = Path(relative).parts
            if not parts or ".." in parts:
                return None
            return ROOT.joinpath(*parts)
    return None


def copy_problems(slug: str, markdown: str) -> list[str]:
    problems = []
    for source in copy_sources(markdown):
        path = resolve(source)
        if path is None:
            problems.append(f"{slug}: copy source {source} is not under ~/.config/apollo-theme")
        elif not path.exists():
            problems.append(f"{slug}: copy source {source} does not exist at {path.relative_to(ROOT)}")
    return problems


def config_paths(text: str) -> list[str]:
    """Every ``~/.config/apollo-theme/<p>`` mention, as ``<p>`` relative to the clone root.

    A path opened by a quote or backtick runs to the matching closer, so names with
    spaces stay whole; an unquoted path ends at whitespace or markup.
    """
    paths = []
    for match in CONFIG_PATH.finditer(text):
        opener = text[match.start() - 1] if match.start() else ""
        rest = text[match.end():]
        if opener in "`\"'":
            relative = rest.split(opener, 1)[0].split("\n", 1)[0]
        else:
            relative = re.match(r"[^\s`\"'<>()\[\]]*", rest).group(0)
        relative = relative.rstrip("\\").rstrip("/").rstrip(".,;:")
        if relative:
            paths.append(relative)
    return paths


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FixtureTests(unittest.TestCase):
    def test_fixture_spaced_name(self):
        sources = copy_sources(fixture("spaced.md"))
        self.assertEqual(["$HOME/.config/apollo-theme/xcode/Apollo Light.xccolortheme"], sources)
        path = resolve(sources[0])
        self.assertEqual(ROOT / "xcode" / "Apollo Light.xccolortheme", path)
        self.assertTrue(path.is_file())

    def test_fixture_relative_source_fails(self):
        self.assertEqual(["apollo.toml"], copy_sources(fixture("relative.md")))
        self.assertIsNone(resolve("apollo.toml"))
        self.assertEqual(
            ["demo: copy source apollo.toml is not under ~/.config/apollo-theme"],
            copy_problems("demo", fixture("relative.md")),
        )

    def test_fixture_loop_and_variables(self):
        sources = copy_sources(fixture("loop.md"))
        self.assertEqual(
            [
                "$HOME/.config/apollo-theme/bat/Apollo.tmTheme",
                "$HOME/.config/apollo-theme/bat/Apollo Light.tmTheme",
            ],
            sources,
        )
        for source in sources:
            path = resolve(source)
            self.assertIsNotNone(path, source)
            self.assertTrue(path.is_file(), path)

    def test_tilde_and_braced_home_resolve(self):
        self.assertEqual(ROOT / "tmux" / "apollo.tmux", resolve("~/.config/apollo-theme/tmux/apollo.tmux"))
        self.assertEqual(ROOT / "tmux" / "apollo.tmux", resolve("${HOME}/.config/apollo-theme/tmux/apollo.tmux"))
        self.assertIsNone(resolve("$HOME/.config/apollo-theme-old/tmux/apollo.tmux"))
        self.assertIsNone(resolve("$HOME/.config/apollo-theme/../etc/passwd"))

    def test_powershell_copy_item_drops_options(self):
        markdown = '```powershell\nCopy-Item -Force -Path "$HOME/.config/apollo-theme/tmux/apollo.tmux" -Destination $env:TEMP\n```\n'
        self.assertEqual(["$HOME/.config/apollo-theme/tmux/apollo.tmux"], copy_sources(markdown))

    def test_config_path_ends_at_closing_delimiter(self):
        text = 'at `~/.config/apollo-theme/iterm2/Apollo Light.itermcolors` and "$HOME/.config/apollo-theme/tmux/apollo.tmux\\" end'
        self.assertEqual(
            ["iterm2/Apollo Light.itermcolors", "tmux/apollo.tmux"],
            config_paths(text),
        )


class RepositoryReadmeTests(unittest.TestCase):
    def test_every_documented_copy_source_exists(self):
        problems = []
        for slug in SLUGS:
            problems += copy_problems(slug, (ROOT / slug / "README.md").read_text(encoding="utf-8"))
        self.assertEqual([], problems)

    def test_every_documented_config_path_exists(self):
        missing = []
        for slug in SLUGS:
            for relative in config_paths((ROOT / slug / "README.md").read_text(encoding="utf-8")):
                if relative in BUILD_OUTPUTS:
                    continue
                if not (ROOT / relative).exists():
                    missing.append(f"{slug}: ~/.config/apollo-theme/{relative} does not exist")
        self.assertEqual([], missing)

    def test_build_outputs_are_produced_by_their_package_script(self):
        package = json.loads((ROOT / "vscode" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual({"vscode/dist/apollo-theme.vsix"}, set(BUILD_OUTPUTS))
        self.assertIn("--out dist/apollo-theme.vsix", package["scripts"]["package"])

    def test_vscode_local_packaging_path(self):
        readme = (ROOT / "vscode" / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "cd ~/.config/apollo-theme/vscode && npm ci && npm run package && code --install-extension dist/apollo-theme.vsix",
            readme,
        )
        self.assertTrue((ROOT / "vscode" / "package-lock.json").is_file())
        package = json.loads((ROOT / "vscode" / "package.json").read_text(encoding="utf-8"))
        self.assertIn("--out dist/apollo-theme.vsix", package["scripts"]["package"])
        install = re.search(r"^## Install\n(.*?)(?=^## )", readme, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(install)
        self.assertNotIn("releases", install.group(1))


if __name__ == "__main__":
    unittest.main()
