"""Behavior 5 smoke tests: documented clone-app installs, run under a scratch HOME.

Every subprocess gets ``HOME=<scratch>``; the real HOME is never read or written.
Commands are argument lists. Paths reach tools only as separate argv items or
through ``APOLLO_*`` environment variables, never formatted into shell or Lua text.
"""

import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import readme_blocks  # noqa: E402

REQUIRED = os.environ.get("APOLLO_SMOKE_REQUIRED") == "1"
TOOLS = {"vim": "vim", "nvim": "nvim", "tmux": "tmux", "rmux": "rmux", "bat": "bat", "eza": "eza", "powershell": "pwsh"}
# Dark first. Each tuple is a constant; nothing outside it is formatted into tool commands.
VARIANTS = {
    "vim": ("apollo", "apollo-light"),
    "nvim": ("apollo", "apollo-light"),
    "tmux": ("apollo.tmux", "apollo-light.tmux"),
    "rmux": ("apollo-rmux.conf", "apollo-rmux-light.conf"),
    "bat": ("Apollo", "Apollo Light"),
    "eza": ("", "light"),
    "powershell": ("Dark", "Light"),
}
MUX_ENV = {"tmux": {}, "rmux": {"RMUX_DISABLE_TMUX_FALLBACK": "1"}}
NVIM_PROBE = 'local s = dofile(os.getenv("APOLLO_SPEC")); s.config({dir = os.getenv("APOLLO_DIR")}); vim.cmd.colorscheme(os.getenv("APOLLO_VARIANT")); if vim.g.colors_name ~= os.getenv("APOLLO_VARIANT") then os.exit(1) end\n'
PS_LOADER = "Import-Module PSReadLine; Import-Module $env:APOLLO_PSD1; Enable-ApolloTheme -Variant $env:APOLLO_VARIANT; $h=(Get-ApolloPSReadLineColors -Variant $env:APOLLO_VARIANT).Command; $e='38;2;'+[Convert]::ToInt32($h.Substring(1,2),16)+';'+[Convert]::ToInt32($h.Substring(3,2),16)+';'+[Convert]::ToInt32($h.Substring(5,2),16); if ((Get-PSReadLineOption).CommandColor -notlike \"*$e*\") { exit 1 }"
PS_ACTIVE = ". $PROFILE; (Get-PSReadLineOption).CommandColor"


def gate(tc, slug):
    if os.name == "nt":
        tc.skipTest("smoke harness is POSIX-only; CI job 'smoke' (macos-15) runs it")
    if os.environ.get("CI") and not REQUIRED:
        tc.skipTest("smoke runs only in CI job 'smoke' (macos-15)")
    if shutil.which(TOOLS[slug]) is None:
        if REQUIRED:
            tc.fail(f"{TOOLS[slug]} missing but APOLLO_SMOKE_REQUIRED=1")
        tc.skipTest(f"{TOOLS[slug]} not installed locally; CI job 'smoke' runs it")


def sgr(hexc):
    return "38;2;" + ";".join(str(int(hexc[i : i + 2], 16)) for i in (1, 3, 5))


def parse_style(text):
    """``bg=#x,fg=#y`` (any order) -> dict, so attribute order never matters."""
    return dict(item.split("=", 1) for item in text.strip().split(",") if "=" in item)


def status_pair(artifact):
    match = re.search(r'^set-option -g status-style "([^"]+)"$', Path(artifact).read_text(encoding="utf-8"), re.MULTILINE)
    return parse_style(match.group(1))


def eza_directory(theme):
    return re.search(r'directory: \{foreground: "(#[0-9a-f]{6})"', Path(theme).read_text(encoding="utf-8")).group(1)


def tmtheme_foreground(theme):
    plist = plistlib.loads(Path(theme).read_bytes())
    return next(entry["settings"]["foreground"] for entry in plist["settings"] if "scope" not in entry)


def ps_command(psm1, variant):
    text = Path(psm1).read_text(encoding="utf-8")
    table = re.search(rf"^\s*{variant} = @\{{\n(.*?)^\s*\}}", text, re.MULTILINE | re.DOTALL).group(1)
    return re.search(r"^\s*Command = '(#[0-9a-f]{6})'", table, re.MULTILINE).group(1)


class SmokeBase(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="apollo-smoke-"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.clone = self.home / ".config" / "apollo-theme"
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"], "TERM": "xterm-256color", "COLORTERM": "truecolor", "LANG": "en_US.UTF-8"}

    def run_(self, argv, extra=None):
        return subprocess.run(argv, env={**self.env, **(extra or {})}, capture_output=True, text=True, timeout=60)

    def clone_once(self):
        if not (self.clone / ".git").exists():
            self.clone.parent.mkdir(parents=True, exist_ok=True)
            r = self.run_(["git", "clone", "--quiet", str(ROOT), str(self.clone)])
            self.assertEqual(0, r.returncode, r.stderr)

    def run_doc(self, slug, marker):
        blocks = readme_blocks((ROOT / slug / "README.md").read_text(encoding="utf-8"), marker)
        self.assertTrue(blocks, f"{slug}: no smoke:{marker} block")
        for block in blocks:
            argv = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", block] if slug == "powershell" else ["sh", "-eu", "-c", block]
            r = self.run_(argv)
            self.assertEqual(0, r.returncode, f"{slug} {marker}: {r.stderr}")

    def mux(self, tool, args, extra=None):
        sock = f"apollo-smoke-{uuid.uuid4().hex}"  # fresh server per assertion
        # tmux leaves its socket file behind after kill-server, so every server's
        # socket lives in a scratch TMUX_TMPDIR (short, for the AF_UNIX path limit).
        sockets = tempfile.mkdtemp(prefix="apollo-smoke-", dir="/tmp")
        extra = {**(extra or {}), "TMUX_TMPDIR": sockets}
        try:
            return self.run_([tool, "-L", sock, *args], extra)
        finally:
            self.run_([tool, "-L", sock, "kill-server"], extra)  # unconditional cleanup
            shutil.rmtree(sockets, True)

    def mux_status(self, tool, config, from_file=False):
        """``status-style`` of a fresh server that sourced ``config`` (or started with ``-f config``)."""
        if from_file:
            args = ["-f", str(config), "new-session", "-d", ";", "show-options", "-gv", "status-style"]
        else:
            args = ["-f", "/dev/null", "new-session", "-d", ";", "source-file", str(config), ";", "show-options", "-gv", "status-style"]
        r = self.mux(tool, args, MUX_ENV[tool])
        return parse_style(r.stdout) if r.returncode == 0 else None

    def ps_profile(self):
        r = self.run_(["pwsh", "-NoProfile", "-NonInteractive", "-Command", "$PROFILE"])
        self.assertEqual(0, r.returncode, r.stderr)
        profile = Path(r.stdout.strip())
        self.assertTrue(profile.is_relative_to(self.home), f"$PROFILE {profile} escapes the scratch HOME")
        return profile

    def loader(self, slug, variant):
        """Load ``variant`` straight from the clone and prove it applied."""
        assert variant in VARIANTS[slug], (slug, variant)
        if slug == "vim":
            r = self.run_(["vim", "-Nu", "NONE", "-i", "NONE", "-es", "--cmd", "let &rtp = $APOLLO_DIR . ',' . &rtp", "-c", "colorscheme " + variant, "-c", 'if g:colors_name !=# "' + variant + '" | cquit | endif', "-c", "qa!"], {"APOLLO_DIR": str(self.clone / "vim")})
            return r.returncode == 0
        if slug == "nvim":
            spec, probe = self.home / "spec.lua", self.home / "probe.lua"
            spec.write_text("return " + readme_blocks((ROOT / "nvim" / "README.md").read_text(encoding="utf-8"), "lazy")[0], encoding="utf-8")
            probe.write_text(NVIM_PROBE, encoding="utf-8")
            r = self.run_(["nvim", "--headless", "--clean", "-l", str(probe)], {"APOLLO_SPEC": str(spec), "APOLLO_DIR": str(self.clone), "APOLLO_VARIANT": variant})
            return r.returncode == 0
        if slug in MUX_ENV:
            artifact = self.clone / slug / variant
            return self.mux_status(slug, artifact) == status_pair(artifact)
        if slug == "bat":
            cfg, cache = self.home / "bat-loader-cfg", self.home / "bat-loader-cache"
            (cfg / "themes").mkdir(parents=True, exist_ok=True)
            for theme in (self.clone / "bat").glob("*.tmTheme"):
                shutil.copyfile(theme, cfg / "themes" / theme.name)
            env = {"BAT_CONFIG_DIR": str(cfg), "BAT_CACHE_PATH": str(cache)}
            if self.run_(["bat", "cache", "--build"], env).returncode != 0:
                return False
            r = self.run_(["bat", "--theme", variant, "--color=always", "--decorations=never", "--language=json", str(self.clone / "palette" / "apollo.json")], env)
            return r.returncode == 0 and sgr(tmtheme_foreground(self.clone / "bat" / (variant + ".tmTheme"))) in r.stdout
        if slug == "eza":
            config_dir = self.clone / "eza" / variant if variant else self.clone / "eza"
            r = self.run_(["eza", "--color=always", "-d", str(self.clone / "eza")], {"EZA_CONFIG_DIR": str(config_dir)})
            return r.returncode == 0 and sgr(eza_directory(config_dir / "theme.yml")) in r.stdout
        if slug == "powershell":
            r = self.run_(["pwsh", "-NoProfile", "-NonInteractive", "-Command", PS_LOADER], {"APOLLO_PSD1": str(self.clone / "powershell" / "ApolloTheme.psd1"), "APOLLO_VARIANT": variant})
            return r.returncode == 0
        raise ValueError(slug)

    def active(self, slug, variant="Dark"):
        """Read only the user files ``smoke:install`` wrote; never re-run README code."""
        if slug == "vim":
            r = self.run_(["vim", "-Nu", str(self.home / ".vimrc"), "-i", "NONE", "-es", "-c", 'if get(g:, "colors_name", "") !=# "apollo" | cquit | endif', "-c", "qa!"])
            return r.returncode == 0
        if slug == "nvim":
            r = self.run_(["nvim", "--headless", "-i", "NONE", "+lua if vim.g.colors_name ~= 'apollo' then vim.cmd.cquit() end", "+qa!"])
            return r.returncode == 0
        if slug in MUX_ENV:
            config = self.home / (".tmux.conf" if slug == "tmux" else ".rmux.conf")
            dark, light = (status_pair(ROOT / slug / name) for name in VARIANTS[slug])
            status = self.mux_status(slug, config, from_file=True)
            return status == dark and status != light
        if slug == "bat":
            r = self.run_(["bat", "--list-themes", "--color=never"])
            names = set(r.stdout.splitlines())
            return r.returncode == 0 and {"Apollo", "Apollo Light"} <= names
        if slug == "eza":
            r = self.run_(["sh", "-c", '. "$HOME/.profile" && eza --color=always -d "$HOME"'])
            return r.returncode == 0 and sgr(eza_directory(ROOT / "eza" / "theme.yml")) in r.stdout
        if slug == "powershell":
            r = self.run_(["pwsh", "-NoProfile", "-NonInteractive", "-Command", PS_ACTIVE])
            return r.returncode == 0 and sgr(ps_command(ROOT / "powershell" / "ApolloTheme.psm1", variant)) in r.stdout
        raise ValueError(slug)


class HelperTests(unittest.TestCase):
    def test_sgr(self):
        self.assertEqual("38;2;131;165;152", sgr("#83a598"))

    def test_style_pairs_are_read_from_artifacts(self):
        self.assertEqual({"bg": "#141617", "fg": "#cfbc97"}, status_pair(ROOT / "tmux" / "apollo.tmux"))
        self.assertEqual({"bg": "#f9f5d7", "fg": "#3c3836"}, status_pair(ROOT / "rmux" / "apollo-rmux-light.conf"))
        self.assertEqual(parse_style("fg=#cfbc97,bg=#141617\n"), status_pair(ROOT / "tmux" / "apollo.tmux"))

    def test_eza_directory_colors(self):
        self.assertEqual("#83a598", eza_directory(ROOT / "eza" / "theme.yml"))
        self.assertEqual("#076678", eza_directory(ROOT / "eza" / "light" / "theme.yml"))

    def test_tmtheme_foregrounds(self):
        self.assertEqual("#cfbc97", tmtheme_foreground(ROOT / "bat" / "Apollo.tmTheme"))
        self.assertEqual("#3c3836", tmtheme_foreground(ROOT / "bat" / "Apollo Light.tmTheme"))

    def test_powershell_command_colors(self):
        self.assertEqual("#fabd2f", ps_command(ROOT / "powershell" / "ApolloTheme.psm1", "Dark"))
        self.assertEqual("#8a5200", ps_command(ROOT / "powershell" / "ApolloTheme.psm1", "Light"))


class SmokeInstallTests(SmokeBase):
    def check_loader(self, slug):
        gate(self, slug)
        self.clone_once()
        if slug == "bat":
            self.run_doc("bat", "install")
        for variant in VARIANTS[slug]:
            self.assertTrue(self.loader(slug, variant), f"{slug} loader failed for {variant!r}")

    def check_activation(self, slug):
        gate(self, slug)
        self.clone_once()
        self.assertFalse(self.active(slug), f"{slug} looked active before install")
        self.run_doc(slug, "install")
        self.assertTrue(self.active(slug), f"{slug} not active after install")

    def check_mux_rejects_opposite(self, slug):
        gate(self, slug)
        self.clone_once()
        dark, light = (self.clone / slug / name for name in VARIANTS[slug])
        self.assertNotEqual(status_pair(light), self.mux_status(slug, dark))
        self.assertNotEqual(status_pair(dark), self.mux_status(slug, light))

    def test_vim_loader(self):
        self.check_loader("vim")

    def test_nvim_loader(self):
        self.check_loader("nvim")

    def test_tmux_loader(self):
        self.check_loader("tmux")

    def test_rmux_loader(self):
        self.check_loader("rmux")

    def test_bat_loader(self):
        self.check_loader("bat")

    def test_eza_loader(self):
        self.check_loader("eza")

    def test_powershell_loader(self):
        self.check_loader("powershell")

    def check_mux_leaves_no_socket(self, slug):
        gate(self, slug)
        default_dir = Path(os.environ.get("TMUX_TMPDIR", "/tmp")) / f"{slug}-{os.getuid()}"
        before = set(default_dir.glob("apollo-smoke-*"))
        self.assertEqual(0, self.mux(slug, ["-f", "/dev/null", "new-session", "-d"], MUX_ENV[slug]).returncode)
        self.assertEqual(before, set(default_dir.glob("apollo-smoke-*")), f"{slug} left a socket in {default_dir}")

    def test_tmux_leaves_no_socket(self):
        self.check_mux_leaves_no_socket("tmux")

    def test_rmux_leaves_no_socket(self):
        self.check_mux_leaves_no_socket("rmux")

    def test_tmux_loader_rejects_opposite_variant(self):
        self.check_mux_rejects_opposite("tmux")

    def test_rmux_loader_rejects_opposite_variant(self):
        self.check_mux_rejects_opposite("rmux")

    def test_vim_activation(self):
        self.check_activation("vim")

    def test_nvim_activation(self):
        self.check_activation("nvim")

    def test_tmux_activation(self):
        self.check_activation("tmux")

    def test_rmux_activation(self):
        self.check_activation("rmux")

    def test_bat_activation(self):
        self.check_activation("bat")

    def test_eza_activation(self):
        self.check_activation("eza")

    def test_powershell_activation(self):
        self.check_activation("powershell")
        profile = self.ps_profile()
        text = profile.read_text(encoding="utf-8")
        self.assertIn("-Variant Dark", text)
        profile.write_text(text.replace("-Variant Dark", "-Variant Light"), encoding="utf-8")
        self.assertTrue(self.active("powershell", "Light"), "powershell Light not active after switching $PROFILE")

    def test_powershell_creates_profile_dir(self):
        gate(self, "powershell")
        self.clone_once()
        profile_dir = self.ps_profile().parent
        self.assertFalse(profile_dir.exists(), profile_dir)
        self.run_doc("powershell", "install")
        self.assertTrue(profile_dir.is_dir(), profile_dir)

    def test_uninstall_keeps_clone_and_other_apps(self):
        if os.name == "nt":
            self.skipTest("smoke harness is POSIX-only; CI job 'smoke' (macos-15) runs it")
        if os.environ.get("CI") and not REQUIRED:
            self.skipTest("smoke runs only in CI job 'smoke' (macos-15)")
        missing = [tool for tool in TOOLS.values() if shutil.which(tool) is None]
        if missing and REQUIRED:
            self.fail(f"{', '.join(missing)} missing but APOLLO_SMOKE_REQUIRED=1")
        apps = [slug for slug, tool in TOOLS.items() if tool not in missing]
        if not apps:
            self.skipTest("no clone app installed locally; CI job 'smoke' runs it")
        self.clone_once()
        for slug in apps:
            self.run_doc(slug, "install")
        note = self.clone / "LOCAL-NOTE.txt"
        note.write_text("local work that uninstall must keep\n", encoding="utf-8")
        for slug in apps:
            self.assertTrue(self.active(slug), f"{slug} not active after install")

        for index, slug in enumerate(apps):
            self.run_doc(slug, "uninstall")
            self.assertTrue((self.clone / ".git").is_dir(), f"clone removed by {slug} uninstall")
            self.assertTrue(note.is_file(), f"note removed by {slug} uninstall")
            status = self.run_(["git", "-C", str(self.clone), "status", "--porcelain"])
            self.assertEqual("?? LOCAL-NOTE.txt", status.stdout.strip(), f"after {slug} uninstall")
            self.assertFalse(self.active(slug), f"{slug} still active after its uninstall")
            for later in apps[index + 1 :]:
                self.assertTrue(self.active(later), f"{later} deactivated by {slug} uninstall")
            for other in apps:
                for variant in VARIANTS[other]:
                    self.assertTrue(self.loader(other, variant), f"{other} {variant!r} loader broke after {slug} uninstall")


if __name__ == "__main__":
    unittest.main()
