# Sub-plan: Task 16, documented paths and Behavior 5 smoke tests

Parent: `2026-11-09-three-repo-consolidation-plan.md`, Task 16. Runs in `$W` on `consolidate-three-repos` after Tasks 14b and 15. Uses the shared names `MONOREPO`, `readme_blocks`, `load_palette` (Task 8) and `CLONE_APPS`.

**Files:** create `tests/test_readme_paths.py`, `tests/test_smoke_install.py`, `tests/fixtures/readme_paths/{spaced.md,relative.md,loop.md}`.

## Step 1: copy-source and docs path test (write first)

`tests/test_readme_paths.py` exposes `copy_sources(markdown) -> list[str]` and `resolve(source) -> Path | None`:
- For each fenced `sh`/`bash`/`powershell` block, track `name=value` assignments (values unquoted with `shlex`). Expand `for v in a 'b c'; do … done` bodies once per value.
- Run `shlex.split` on every line starting with `cp ` or `Copy-Item `. Drop option tokens (`-R`, `-Force`, `-Path`, `-Destination`). Every remaining argument except the last is a source. `$var`/`${var}` are expanded from the tracked assignments and the loop value.
- `resolve` maps `$HOME/.config/apollo-theme/<p>` or `~/.config/apollo-theme/<p>` to `ROOT/<p>`. Anything else returns `None`.

Tests:
- `test_fixture_spaced_name`: `cp "$HOME/.config/apollo-theme/xcode/Apollo Light.xccolortheme" dst/` resolves to an existing file.
- `test_fixture_relative_source_fails`: `cp apollo.toml dst` yields `None`. The repo test reports `<slug>: copy source apollo.toml is not under ~/.config/apollo-theme`.
- `test_fixture_loop_and_variables`: the bat block (`clone_dir="$HOME/.config/apollo-theme/bat"`, `for name in 'Apollo.tmTheme' 'Apollo Light.tmTheme'`, `cp "$clone_dir/$name" …`) yields both files, and both exist.
- `test_every_documented_copy_source_exists`: for each of the 17 READMEs, every copy source resolves and exists.
- `test_every_documented_config_path_exists`: every `~/.config/apollo-theme/<p>` in prose, inline code, or fences exists under `ROOT` (trailing `/` stripped).
- `test_vscode_local_packaging_path`: `vscode/README.md` contains `cd ~/.config/apollo-theme/vscode && npm ci && npm run package && code --install-extension dist/apollo-theme.vsix`. `vscode/package-lock.json` exists. `scripts.package` in `vscode/package.json` contains `--out dist/apollo-theme.vsix`. The Install section contains no `releases` link.

Run `python3 -m unittest tests.test_readme_paths -v`. Expected: FAIL on any README that Task 15 left relative. Fix the README, then re-run until PASS.

## Step 2: smoke harness gating and environment

```python
import os, plistlib, re, shutil, subprocess, sys, tempfile, unittest, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
from common import load_palette, readme_blocks
REQUIRED = os.environ.get("APOLLO_SMOKE_REQUIRED") == "1"
TOOLS = {"vim": "vim", "nvim": "nvim", "tmux": "tmux", "rmux": "rmux", "bat": "bat", "eza": "eza", "powershell": "pwsh"}
def gate(tc, slug):
    if os.name == "nt": tc.skipTest("smoke harness is POSIX-only; CI job 'smoke' (macos-15) runs it")
    if os.environ.get("CI") and not REQUIRED: tc.skipTest("smoke runs only in CI job 'smoke' (macos-15)")
    if shutil.which(TOOLS[slug]) is None:
        if REQUIRED: tc.fail(f"{TOOLS[slug]} missing but APOLLO_SMOKE_REQUIRED=1")
        tc.skipTest(f"{TOOLS[slug]} not installed locally; CI job 'smoke' runs it")
def sgr(hexc): return "38;2;" + ";".join(str(int(hexc[i:i + 2], 16)) for i in (1, 3, 5))
class SmokeBase(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="apollo-smoke-")); self.addCleanup(shutil.rmtree, self.home, True)
        self.clone = self.home / ".config" / "apollo-theme"
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"], "TERM": "xterm-256color", "COLORTERM": "truecolor", "LANG": "en_US.UTF-8"}
    def run_(self, argv, extra=None):
        return subprocess.run(argv, env={**self.env, **(extra or {})}, capture_output=True, text=True, timeout=60)
    def clone_once(self):
        if not (self.clone / ".git").exists():
            self.clone.parent.mkdir(parents=True, exist_ok=True)
            r = self.run_(["git", "clone", "--quiet", str(ROOT), str(self.clone)]); self.assertEqual(0, r.returncode, r.stderr)
    def run_doc(self, slug, marker):
        for block in readme_blocks((ROOT / slug / "README.md").read_text(encoding="utf-8"), marker):
            argv = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", block] if slug == "powershell" else ["sh", "-eu", "-c", block]
            r = self.run_(argv); self.assertEqual(0, r.returncode, f"{slug} {marker}: {r.stderr}")
    def mux(self, tool, args, extra=None):
        sock = f"apollo-smoke-{uuid.uuid4().hex}"          # fresh server per assertion
        try: return self.run_([tool, "-L", sock, *args], extra)
        finally: self.run_([tool, "-L", sock, "kill-server"], extra)   # unconditional cleanup
```
Rules:
- Every command is an argument list. Paths reach tools only as separate argv items or through env vars (`APOLLO_DIR`, `APOLLO_VARIANT`, `APOLLO_SPEC`, `APOLLO_PSD1`); Python values are never formatted into shell or Lua text.
- README blocks run verbatim as one argv element.
- The documented clone line is checked textually by Task 14; the harness clones committed `HEAD` with `clone_once()`, so commit before running.

## Step 3: probes

Loader probes `loader(slug, variant) -> bool` load straight from the clone and prove the variant applied.
- **vim:** `["vim", "-Nu", "NONE", "-i", "NONE", "-es", "--cmd", "let &rtp = $APOLLO_DIR . ',' . &rtp", "-c", "colorscheme " + v, "-c", 'if g:colors_name !=# "' + v + '" | cquit | endif', "-c", "qa!"]`, with `APOLLO_DIR=<clone>/vim` and `v` drawn from the constant tuple `("apollo", "apollo-light")`.
- **nvim:** write `spec.lua` = `"return " +` the README `smoke:lazy` block. Run `["nvim", "--headless", "--clean", "-l", probe]`, where `probe.lua` is a test constant: `local s = dofile(os.getenv("APOLLO_SPEC")); s.config({dir = os.getenv("APOLLO_DIR")}); vim.cmd.colorscheme(os.getenv("APOLLO_VARIANT")); if vim.g.colors_name ~= os.getenv("APOLLO_VARIANT") then os.exit(1) end`.
- **tmux:** `mux("tmux", ["-f", "/dev/null", "new-session", "-d", ";", "source-file", str(clone / "tmux" / f), ";", "show-options", "-gv", "status-style"])`. Stdout must equal the exact pair parsed from that variant's artifact `status-style` line (dark `bg=#1d2021,fg=#cfbc97`-style; read from the file, not hard-coded), and a paired negative test asserts the opposite variant's pair is rejected.
- **RMUX:** same as tmux with `rmux/apollo-rmux[-light].conf` and `{"RMUX_DISABLE_TMUX_FALLBACK": "1"}`.
- **bat:** disposable `cfg = home/"bat-loader-cfg"` and `cache = home/"bat-loader-cache"`, separate from the activation cache. Copy `<clone>/bat/*.tmTheme` into `cfg/themes/`. Run `["bat", "cache", "--build"]` with `{"BAT_CONFIG_DIR": cfg, "BAT_CACHE_PATH": cache}`, then `["bat", "--theme", name, "--color=always", "--decorations=never", "--language=json", str(clone / "palette" / "apollo.json")]` with the same env. Output must contain `sgr()` of that tmTheme's global `foreground` (read via `plistlib`).
- **eza:** `["eza", "--color=always", "-d", str(clone / "eza")]` with `EZA_CONFIG_DIR=<clone>/eza[/light]`. Output must contain `sgr()` of that `theme.yml`'s `filekinds.directory.foreground` (regex `directory: \{foreground: "(#[0-9a-f]{6})"`; dark `#83a598` → `38;2;131;165;152`).
- **pwsh:** `["pwsh", "-NoProfile", "-NonInteractive", "-Command", PS_LOADER]` with `APOLLO_PSD1`, `APOLLO_VARIANT`. `PS_LOADER` is a constant: `Import-Module PSReadLine; Import-Module $env:APOLLO_PSD1; Enable-ApolloTheme -Variant $env:APOLLO_VARIANT; $h=(Get-ApolloPSReadLineColors -Variant $env:APOLLO_VARIANT).Command; $e='38;2;'+[Convert]::ToInt32($h.Substring(1,2),16)+';'+[Convert]::ToInt32($h.Substring(3,2),16)+';'+[Convert]::ToInt32($h.Substring(5,2),16); if ((Get-PSReadLineOption).CommandColor -notlike "*$e*") { exit 1 }`.

Activation probes `active(slug) -> bool` read only the user files that `smoke:install` wrote and never re-run README code.
- **vim:** `["vim", "-Nu", str(home / ".vimrc"), "-i", "NONE", "-es", "-c", 'if get(g:, "colors_name", "") !=# "apollo" | cquit | endif', "-c", "qa!"]`.
- **nvim:** `["nvim", "--headless", "-i", "NONE", "+lua if vim.g.colors_name ~= 'apollo' then vim.cmd.cquit() end", "+qa!"]` (no `--clean`, so `~/.config/nvim/init.lua` loads).
- **tmux:** `mux("tmux", ["-f", str(home / ".tmux.conf"), "new-session", "-d", ";", "show-options", "-gv", "status-style"])` equals the dark artifact's exact `status-style` pair and not the light pair.
- **RMUX:** the same with `~/.rmux.conf` and `RMUX_DISABLE_TMUX_FALLBACK=1`.
- **bat:** `["bat", "--list-themes", "--color=never"]` under the scratch HOME's default config/cache lists `Apollo` and `Apollo Light`.
- **eza:** `["sh", "-c", '. "$HOME/.profile" && eza --color=always -d "$HOME"']` contains the dark directory `sgr`.
- **pwsh:** `["pwsh", "-NoProfile", "-NonInteractive", "-Command", ". $PROFILE; (Get-PSReadLineOption).CommandColor"]` contains Dark's `Command` sgr. The test then rewrites `-Variant Dark` → `-Variant Light` in `$PROFILE` and expects Light's.

## Step 4: tests

- `test_<slug>_loader` (7, each: `gate`, `clone_once`, bat runs install first, both variants True).
- `test_<slug>_activation` (7: `gate`, `clone_once`, `run_doc(slug, "install")`, `active` True).
- `test_powershell_creates_profile_dir`: `$PROFILE`'s directory is absent before install and present after.
- `test_uninstall_keeps_clone_and_other_apps`: install every available app and write `LOCAL-NOTE.txt` in the clone. Then, per app in `TOOLS` order, run `run_doc(slug, "uninstall")` and assert:
  - the clone and note exist;
  - `git -C <clone> status --porcelain` == `?? LOCAL-NOTE.txt`;
  - `active(slug)` is False;
  - every not-yet-uninstalled app's `active` is True;
  - every loader probe is still True (bat's loader uses its own cache).

Run `python3 -m unittest tests.test_readme_paths tests.test_smoke_install -v`.
- Locally (no `CI`): PASS, except the pwsh tests SKIP with "pwsh not installed locally; CI job 'smoke' runs it".
- In `validate` (CI set, not required): all smoke tests SKIP with "smoke runs only in CI job 'smoke' (macos-15)".
- In `smoke`: all run, none skip.

Commit: `c "Smoke-test documented installs under a scratch HOME"`.
