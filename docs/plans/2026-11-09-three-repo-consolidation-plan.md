# Three-Repository Consolidation Implementation Plan

**Goal:** Reduce `github.com/apollo-theme` to `apollo-palette`, `apollo-theme`, `apollo-theme.github.io` without losing history, tags, releases, or install paths.
**Architecture:** `apollo-palette` is the new source of truth, pinned by `palette/SOURCE.json`. `apollo-theme` replaces 15 submodules with 17 history-preserving `git subtree` folders, one root CI, and four migration scripts. The site is a peer repo, no longer a submodule. Deletion is gated by `verify_migration.py`.
**Tech stack:** git 2.56 (`git subtree`), Python 3 stdlib, GitHub Actions, `gh` CLI. Node, vim, nvim, tmux, rmux, bat, eza, and pwsh are needed only by the app jobs.

Paths: `R=/Users/d0n9x1n/Workspace/fun-code/apollo-theme` (current checkout); `W=$R/.build/consolidate` (work clone); `P=/Users/d0n9x1n/Workspace/fun-code/apollo-palette`; `S=$R/.build/site` (site clone); `B=$R/.build/org-backup-2026-11-09`; `X=$R/.build/apollo-light-crlf-audit`.
Shell blocks run in bash; define `APPS13="sonicterm windows-terminal firefox vscode visual-studio vim nvim xcode tmux rmux powershell bat eza"`.
Commit helper, defined in every shell: `c() { git commit -m "$1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; }`.

## Test Strategy

| Requirement | Test (written first) | Kind | Task |
| --- | --- | --- | --- |
| 17 real folders, no gitlinks | `test_layout.LayoutTests.test_every_app_is_a_tracked_folder` (`git ls-files -s` mode ≠ 160000) | unit/repo | 8 |
| SOURCE pin | `test_layout…test_source_pin_matches_palette_bytes` plus a negative pin fixture | unit | 8 |
| Gecko IDs | the existing `check.py` gecko block kept; `test_layout…test_gecko_ids_unchanged` | unit | 8 |
| `sync_palette.py` | `test_sync_palette` against a temp palette repo and a temp root with 2 fake apps; bad ref → exit 2 | fixture | 9 |
| Firefox dry run | `test_firefox_release`: tag parse accept/reject, version mismatch, injected build runner; CI runs a real dry run | unit + CI | 10 |
| One root CI | `test_ci`: one job per slug with `working-directory: <slug>`, no nested workflows, release trigger `firefox-v*` | static | 11 |
| Verify gate (tree/history/tags) | `test_verify_migration` builds source repo → bundle → subtree mono in tmp; allowlisted edit passes, other edit fails, moved tag fails | fixture | 12 |
| Live repos equal backups | `test_verify_migration` live-source fakes (moved ref, edited release) | fixture | 0, 12, 21 |
| tmux/RMUX/eza/bat checks use shared paths | each app's `tests/test_theme.py` updated first | unit | 14b |
| Releases restore + verify | `test_restore_releases`: plan from temp backup; `check_releases` with an injected fake API/downloader | unit | 13 |
| README contract (shared clone) | `test_readme_contract` with injected README strings: missing idempotent clone, `rm -rf` of the clone under Uninstall, missing "Remove the shared clone" | unit | 14 |
| Documented paths exist | `test_readme_paths`: every `cp`/`Copy-Item` source (relative fails; variables/loops expanded; spaced names) and every `~/.config/apollo-theme/<p>` in 17 READMEs → `ROOT/<p>` exists | static | 16 |
| Behavior 5 smoke | `test_smoke_install` (sub-plan `2026-11-09-three-repo-consolidation-smoke-subplan.md`): loader probes (both variants) plus activation probes after README-extracted `smoke:install`/`smoke:uninstall` blocks under a scratch HOME; skips per absent tool unless `APOLLO_SMOKE_REQUIRED=1` | integration | 16 |
| apollo-palette contract | `$P/tests/test_check.py`, `test_tables.py` | unit | 1–2 |
| Site 17/34 + no dead links | `test_site` counts, plus `test_no_links_to_deleted_repositories` | unit | 19, 20b |
| Org has 3 repos | `gh repo list apollo-theme --json name -q '.[].name' \| sort` | acceptance | 21 |

Local tools: vim (`/usr/bin/vim`), nvim, tmux, rmux, bat, eza, node, and xmllint are present; **pwsh is absent**, so the PowerShell smoke test skips locally. CI job `smoke` runs on macos-15 with every tool installed and `APOLLO_SMOKE_REQUIRED=1`.

## Component Map

Existing code near the change (bottom-up):

| component | job | key files | depends on | evidence |
| --- | --- | --- | --- | --- |
| App registry | 13 repo-keyed apps + light artifacts | `scripts/common.py` | — | common.py:16-48 |
| Generate driver | runs each child `scripts/generate.py` | `scripts/generate.py` | common | generate.py:12-19 |
| Submodule check | validates `.gitmodules`, profile repo | `scripts/check.py` | git | check.py:153-196 |
| README contract | branding fragments per child | `scripts/check.py` | common | check.py:385-440 |
| Repo check + gecko | snapshot bytes, gecko IDs | `scripts/check.py` | common | check.py:443-474, 466-471 |
| Root CI | 3-OS root gate, checks out submodules | `.github/workflows/ci.yml` | — | ci.yml:13-29 |
| Firefox release | tag→version check, build, publish | `firefox-apollo-theme/.github/workflows/release.yml` | npm | release.yml:37-46 |
| App generators | read `ROOT/palette` with ROOT = parents[1] | `*/scripts/generate.py` | own palette | verified, all 17 |
| Site app list | 13 `App` rows, repo URL property | `apollo-theme.github.io/scripts/generate.py` | — | generate.py:18-45, 201-205 |
| Site hash check | hard-coded `EXPECTED_HASHES` | site `scripts/check.py` | — | check.py:77-107 |
| Retired site code | 17-app generator/tests | site commit `1af8853` | — | `git show 22a4240 --stat` (3 files) |
| Parent tests | site/profile/retired assertions | `tests/test_palette.py` | common, check | test_palette.py:75,142-160,518-530 |

New or changed components (each passes fitness: one job, one-way deps, small interface, testable through it):

| component | job | interface | reuses or extends | likely change | test seam |
| --- | --- | --- | --- | --- | --- |
| `common.APPS` | Single registry of 17 apps keyed by slug | `APPS: dict[str,dict]`, `SLUGS`, `CLONE_APPS`, `readme_blocks(text, marker)` | extends `APP_METADATA`+`LIGHT_ARTIFACTS` | add an app | `test_palette` metadata tests |
| `palette/SOURCE.json` | Pin to the apollo-palette commit + hashes | JSON `{repository, commit, sha256{}}` | new | palette bump | `check_source_pin` |
| `check.py` | Portable gate: layout, pin, snapshots, gecko, README | `check_layout()`, `check_source_pin(root)`, `check_readme_contract(slug, readme)` | replaces `check_submodules`, extends contract | new README rule | `test_layout`, `test_readme_contract` |
| `sync_palette.py` | Apply an apollo-palette ref everywhere | `sync(repo, ref, root, slugs, run) -> str` | reuses generate pattern | new target file | `test_sync_palette` |
| `firefox_release.py` | All release logic, never publishes | `version_from_tag`, `check_versions`, `build`, `release_notes`; CLI `--dry-run TAG` | moves release.yml:37-75 | packaging change | `test_firefox_release` |
| `ci.yml` / `firefox-release.yml` | Run root + per-app gates / publish firefox | YAML | extends ci.yml; ports 17 child workflows | runner bump | `test_ci` |
| `migration.py` | Migration facts only | `SOURCES`, `ALLOWLIST`, `MIGRATION_LINE`, `migrated_body()` | new | allowlist edit | used by both scripts' tests |
| `verify_migration.py` | Pre-deletion gate | CLI `[--app S] [--offline] [--live-source R]`; `check_tree/history/tags/releases/pin/live_source` → `list[str]` errors | uses migration.py | new check | `test_verify_migration` |
| `restore_releases.py` | Re-create backed-up releases idempotently | CLI `[--apply]`; `plan_releases(backup)` | uses migration.py | — | `test_restore_releases` |
| smoke harness | Executes documented install/uninstall | `tests/test_smoke_install.py` | `readme_blocks` | new app | itself |
| site `App.repo` + pin | Monorepo links, SOURCE pin | `App.repo`, `App.readme`, `App.releases` | restores 1af8853 rows | link format | site tests |
| `$P` check/tables | Palette repo contract | `check_readme(text, palettes) -> list[str]`, `tables.py --check/--write` | copies parent check.py:77-150 + common.py contrast | new section | `$P/tests` |

## Design comparison

| Decision | Options | Chosen and why |
| --- | --- | --- |
| Site as parent submodule | keep / drop | **Drop.** The three-repo model makes the site a peer that consumes the palette through its own `SOURCE.json`. A gitlink forces a parent commit after every deploy, and the parent tests that read site files (test_palette.py:75,142-160) move into the site repo. `.github/organization` is dropped because the repo is deleted. |
| Where to build | in `$R` / fresh clone `$W` | **`$W`.** Submodule deinit and 17 subtree merges stay out of the user's checkout. `$R` fast-forwards at the end. |
| Smoke commands | duplicated in tests / extracted from README | **Extracted** from `<!-- smoke:install -->`/`<!-- smoke:uninstall -->` fenced blocks, so tests run exactly the documented path. Probes stay test-owned. |
| Release restore | manual `gh` / script | **Script** (`restore_releases.py`): 33 releases, idempotent, and shares `migrated_body()` with the verifier. |
| Lazy.nvim test | real lazy / emulate | **Emulate**: evaluate the README's spec table and call `spec.config({dir=clone})`. That is the exact code lazy runs, and it needs no network. |
| Merge to main | PR squash / fast-forward | **Fast-forward** (`git push origin HEAD:main`). A squash would destroy the subtree ancestry that Behavior 4 checks. |

## Second-opinion reconciliation

Blind sketch: GPT-6 Astra.

| Topic | agree | differ | chosen and why |
| --- | --- | --- | --- |
| Component split (adapters, orchestration, palette authority, sync, CI/releases, site, verifier) | Same seven responsibilities | Mine also separates `migration.py` (facts) from the verifier and restorer | **Mine.** Restorer and verifier share `migrated_body()` and `SOURCES`, so neither can drift from the other. |
| Freeze sources before conversion | Yes | Sketch freezes a new inventory. Mine treats the existing bundles + `releases/*.json` as the frozen inventory | **Both.** Bundles + `releases/*.json` are the frozen inventory; T0 and T21 compare every live repo to them (`--live-source`), and T21 archives all 15 first so nothing changes between check and delete. Parent `v0.1.0`–`v0.3.1` compare against backup JSON (T13). |
| 15 gitlinks out, 17 unsquashed subtrees, pinned retired HEADs, one docs commit | Identical | — | Same (T5–T7, T15). |
| Child independence; site comparisons leave parent tests; snapshot + Gecko enforcement | Identical | — | Same (T8, T17, T19). |
| Palette repo first, byte-identical, fresh history, prose/ratio checks | Identical | — | Same (T1–T4). |
| Firefox publish validates prefix/version **and both Gecko IDs** | Prefix/version | Mine checked IDs only in `check.py` | **Astra.** `firefox_release.py` adds `check_gecko_ids` (T10), so a tag push cannot publish a changed ID. |
| Restore releases without rebuilding assets | Yes: upload backed-up files, verify SHA-256 | — | Same (T13, T20). |
| Shared-clone smoke for 7 apps, Vim rtp, lazy config, uninstall isolation | Identical scope | Mine extracts commands from README markers | **Mine.** Tests then execute exactly what users read. |
| Verifier behaviour on errors | — | Astra: fail-closed | **Astra.** Any `gh`/git error, missing backup file, or missing release counts as a failure, never a skip (T12/T13). |
| Order: site + CI before deletion, verifier gates, then exactly three | Identical | — | Same (T18–T21). |
| `.github` profile releases v1.0.0–v1.1.1 | Not addressed | — | **Not migrated (spec Decision 11); the verified backup is their archive.** All three are text-only (0 assets); their tags point at profile commits not imported into `apollo-theme`, so `profile-v*` tags would misrepresent history. T21 verifies `dot-github.bundle`, the 3 JSON files, and live == backup before deletion. |

## File Structure

`apollo-palette` (`$P`): `palette/apollo.json`, `palette/apollo-light.json` (bytes copied), `scripts/common.py` (contrast, from parent common.py:61-112), `scripts/check.py`, `scripts/tables.py`, `tests/test_check.py`, `tests/test_tables.py`, `README.md`, `NOTICE`, `LICENSE`, `CLAUDE.md`, `.gitattributes`, `.github/workflows/ci.yml`.

`apollo-theme` (`$W`):
- Delete: `.gitmodules`; gitlinks `*-apollo-theme`, `.github/organization`, `apollo-theme.github.io`; `<slug>/.github/` (all 17).
- Add (subtree): `sonicterm windows-terminal firefox vscode visual-studio vim nvim xcode tmux rmux powershell bat eza wezterm iterm2 apple-terminal alacritty`.
- Create: `palette/SOURCE.json`, `scripts/{sync_palette,firefox_release,migration,verify_migration,restore_releases}.py`, `.github/workflows/firefox-release.yml`, `tests/{test_layout,test_sync_palette,test_firefox_release,test_ci,test_verify_migration,test_restore_releases,test_readme_contract,test_readme_paths,test_smoke_install}.py`.
- Modify: `scripts/common.py`, `scripts/generate.py`, `scripts/check.py`, `.github/workflows/ci.yml`, `tests/test_palette.py`, `README.md`, `CLAUDE.md`, `<slug>/README.md`, `<slug>/CLAUDE.md` (17), `firefox/package.json`, `vscode/package.json`, `vscode/scripts/check.py`, `powershell/scripts/generate.py`+`ApolloTheme.psd1`, `wezterm/scripts/{generate,check}.py`+`apollo*.toml`.

Site (`$S`): modify `scripts/generate.py`, `scripts/check.py`, `tests/test_site.py`, `index.html`, `previews/*` (34), `README.md`, `CLAUDE.md`; create `palette/SOURCE.json`.

## Tasks

Parallel groups (independent files): **A** = Tasks 10, 11, 12. **C** = Task 14b's 4 apps (tmux, rmux, eza, bat). **B** = Task 15's 13 per-app sub-tasks (one worktree per app, branch `docs/<slug>` off the consolidation branch, merged back in slug order). Everything else is sequential.

### Phase 0: preflight

### Task 0: Workspace, backup integrity, live repos equal backups
**Files:** none (creates `$W`). **Acceptance first:** loop 1 prints exactly 15 `OK` (13 apps + site + org profile `.github/organization`) and no `MISMATCH`; loop 2 prints 15 `LIVE-OK` (13 apps + `.github` + `demo-repository`) and no `LIVE-MISMATCH`.
```bash
set -uo pipefail; cd $R
bundle_for() { case $1 in .github|.github/organization) echo $B/dot-github.bundle;; *) echo $B/$1.bundle;; esac; }
for d in *-apollo-theme apollo-theme.github.io .github/organization; do b=$(bundle_for $d)
  git bundle verify -q $b && git bundle list-heads $b refs/heads/main | grep -q "^$(git -C $d rev-parse HEAD)" && [ -z "$(git -C $d status --porcelain --untracked-files=no)" ] && echo "OK $d" || echo "MISMATCH $d"; done
DEL="$(for s in $APPS13; do printf '%s-apollo-theme ' $s; done).github demo-repository"
for r in $DEL; do b=$(bundle_for $r)
  diff <(git bundle list-heads $b | grep -E ' refs/(heads|tags)/' | sort) <(git ls-remote --heads --tags https://github.com/apollo-theme/$r | grep -v '\^{}$' | tr '\t' ' ' | sort) >/dev/null &&
  diff <(ls $B/releases/$r | sed -n 's/\.json$//p' | sort) <(gh release list -R apollo-theme/$r -L 100 --json tagName -q '.[].tagName' | sort) >/dev/null && echo "LIVE-OK $r" || echo "LIVE-MISMATCH $r"; done
for p in wezterm:0a23a76 iterm2:4b8666d apple-terminal:67551c9 alacritty:563ac97; do git -C $X/${p%%:*}-apollo-theme rev-parse --short HEAD | grep -qx ${p#*:} || echo "BAD $p"; done
git clone --no-recurse-submodules $R $W && cd $W && git remote set-url origin https://github.com/apollo-theme/apollo-theme.git && git fetch origin && git switch -c consolidate-three-repos origin/main
mkdir -p docs/plans && cp $R/docs/specs/2026-11-09-three-repo-consolidation-design.md docs/specs/ && cp $R/docs/plans/2026-11-09-three-repo-consolidation-plan.md $R/docs/plans/2026-11-09-three-repo-consolidation-smoke-subplan.md docs/plans/
git add docs && c "Add three-repository consolidation design and plans"
```
**Done:** 15 `OK`, 15 `LIVE-OK`, no `BAD`; the docs commit (spec, plan, smoke sub-plan; `git ls-files docs | grep -c consolidation` = 3) sits on `d18075e`. Any mismatch stops the plan. Full asset-digest equality is re-checked in Task 21 by `--live-source`.

### Phase 1: apollo-palette (must be green before any pin)

### Task 1: Palette repo check (schema, slots, contrast, README sections)
**Files:** create `$P/palette/*`, `$P/scripts/{common,check}.py`, `$P/tests/test_check.py`.
- [ ] **Test first** (`$P/tests/test_check.py`):
```python
import copy, sys, unittest; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check import check_readme, check_schema, check_slots, check_contrast, REQUIRED_SECTIONS, load_palettes
WORDS = " ".join(["word"] * 80)
HEAD = "| Role | Hex | Background | Ratio | Reason |\n| --- | --- | --- | --- | --- |\n"
def table(v, rows): return f"<!-- example:{v} -->\n{HEAD}{rows}<!-- /example:{v} -->\n"
def doc(dark="| Text | #cfbc97 | #141617 | 9.76 | primary |\n", light="| Text | #3c3836 | #f9f5d7 | 10.53 | primary |\n"):
    return "".join(f"## {s}\n\n{WORDS}\n\n" for s in REQUIRED_SECTIONS) + table("dark", dark) + table("light", light)
class ReadmeTests(unittest.TestCase):
    def errs(self, text): return check_readme(text, load_palettes())
    def test_valid_is_error_free(self): self.assertEqual([], self.errs(doc()))
    def test_wrong_ratio_fails(self): self.assertTrue(any("ratio 1.00" in e for e in self.errs(doc().replace("9.76", "1.00"))))
    def test_unknown_hex_fails(self): self.assertTrue(any("not in dark" in e for e in self.errs(doc().replace("#cfbc97", "#123456"))))
    def test_empty_example_fails(self): self.assertIn("light: worked example has no rows", self.errs(doc(light="")))
    def test_short_section_fails(self): self.assertTrue(any("80 words" in e for e in self.errs(doc().replace(WORDS, "short", 1))))
    def test_missing_section_fails(self): self.assertTrue(any("missing section" in e for e in self.errs(doc().replace("## Lineage", "## Other"))))
class PaletteTests(unittest.TestCase):
    def setUp(self): self.p = copy.deepcopy(load_palettes())
    def test_real_palettes_pass(self): self.assertEqual([], check_schema(self.p) + check_slots(self.p) + check_contrast(self.p))
    def test_schema(self): del self.p["dark"]["roles"]; self.assertIn("dark: missing key roles", check_schema(self.p))
    def test_slot_order(self):
        a = self.p["light"]["terminal"]["ansi"]; a[1], a[2] = a[2], a[1]; self.assertIn("light: terminal.ansi slot order differs", check_slots(self.p))
    def test_contrast(self): self.p["light"]["colors"]["foreground"] = "#e0e0e0"; self.assertTrue(any(e.startswith("light foreground") for e in check_contrast(self.p)))
```
- [ ] Run `cd $P && python3 -m unittest discover -s tests -v`. Expected: FAIL, `ModuleNotFoundError: No module named 'check'`.
- [ ] **Implement:** `git init -b main $P`. Copy `palette/*.json`, `NOTICE`, `LICENSE`, `.gitattributes` from `$R` (`cmp` each). `scripts/common.py` = parent common.py:61-112 (load, `iter_hex_colors`, luminance, `contrast_ratio`) with `ROOT/palette`. `scripts/check.py` = parent `check_palette()` and `EXPECTED_*` (check.py:27-150) verbatim, plus:
```python
REQUIRED_SECTIONS = ("Lineage", "Roles", "Contrast rules", "Why Apollo Light darkens semantic colors", "ANSI slot order", "Choosing colors for a new app")
def sections(text):
    out, name = {}, None
    for line in text.splitlines():
        if line.startswith("## "): name = line[3:].strip(); out[name] = []
        elif name: out[name].append(line)
    return out
def prose_words(lines):
    keep, fence = [], False
    for l in lines:
        if l.startswith("```"): fence = not fence; continue
        if fence or l.lstrip().startswith(("|", "<!--")): continue
        keep.append(l)
    return len(re.findall(r"[A-Za-z][\w'-]*", " ".join(keep)))
def check_readme(text, palettes):
    errs, secs = [], sections(text)
    for s in REQUIRED_SECTIONS:
        if s not in secs: errs.append(f"missing section {s}")
        elif prose_words(secs[s]) < 80: errs.append(f"{s}: under 80 words of prose")
    for variant in ("dark", "light"):
        m = re.search(rf"<!-- example:{variant} -->(.*?)<!-- /example:{variant} -->", text, re.S)
        if not m: errs.append(f"missing worked example {variant}"); continue
        known = set(iter_hex_colors(palettes[variant]))
        rows = [r for r in m.group(1).strip().splitlines()[2:] if r.startswith("|")]
        if not rows: errs.append(f"{variant}: worked example has no rows")
        for row in rows:
            role, fg, bg, ratio, _ = [c.strip() for c in row.strip("|").split("|")]
            for h in (fg, bg):
                if h not in known: errs.append(f"{variant} {role}: {h} not in {variant} palette")
            if f"{contrast_ratio(fg, bg):.2f}" != ratio: errs.append(f"{variant} {role}: ratio {ratio} != {contrast_ratio(fg, bg):.2f}")
    return errs
REQUIRED_KEYS = ("schemaVersion", "id", "name", "appearance", "provenance", "colors", "roles", "terminal", "constraints")
TEXT_ROLES = ("foreground", "foregroundSecondary", "foregroundInactive", "accent", "danger", "success", "info")
def check_schema(p): return [f"{v}: missing key {k}" for v, d in p.items() for k in REQUIRED_KEYS if k not in d] + [f"{v}: bad hex {h}" for v, d in p.items() for h in iter_hex_colors(d) if not HEX_COLOR.match(h)]
def check_slots(p): return [f"{v}: terminal.{k} slot order differs" for v in p for k in ("ansi", "bright") if p[v]["terminal"][k] != EXPECTED_TERMINAL[v][k]]
def check_contrast(p): return [f"{v} {r}: {contrast_ratio(d['colors'][r], d['colors']['background']):.2f} < 4.5" for v, d in p.items() for r in TEXT_ROLES if contrast_ratio(d["colors"][r], d["colors"]["background"]) < 4.5]
```
Verified today: real ratios are 9.76 (dark text) and 10.53 (light text), and every `TEXT_ROLES` entry is ≥4.95 on its canvas. `main()` runs `check_palette()`, the three list checks, `tables.check()` (Task 2), and `check_readme(README)`, and exits 1 on any error. Add `import tables` lazily in `main` so Task 1 tests stay green.
- [ ] Run the tests. Expected: PASS (10), with `test_valid_is_error_free` returning exactly `[]`. Then `git add -A && c "Add canonical palettes and contract checks"`. The first-commit message body must name the source: run instead `git commit -m "Import Apollo palettes from apollo-theme d18075e" -m "Source: https://github.com/apollo-theme/apollo-theme/commit/$(git -C $R rev-parse d18075e)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"`.

### Task 2: Generated role and contrast tables
**Files:** `$P/scripts/tables.py`, `$P/tests/test_tables.py`.
- [ ] **Test first:** `render(palettes)` returns a role table (`| Role | Apollo Dark | Apollo Light |`, one row per `roles` key sorted) and a contrast table (text roles `foreground, foregroundSecondary, foregroundInactive, accent, danger, success, info` × `background, surface, selection`, ratios `:.2f`). Tests: `replace_between(text, "roles", body)` swaps only between `<!-- tables:roles:start -->`/`<!-- tables:roles:end -->`; `stale(readme)` returns `["roles"]` when the block content differs; missing markers raise `ValueError("missing tables:roles markers")`.
- [ ] Run. Expected: FAIL `No module named 'tables'`.
- [ ] **Implement** `render`, `replace_between`, `stale`, and CLI `--write|--check` (check exits 1 listing stale blocks). Run. PASS. `c "Generate role and contrast tables"`.

### Task 3: README rationale and worked example; review gate
**Files:** `$P/README.md`, `$P/CLAUDE.md`.
- [ ] **Acceptance first:** `python3 scripts/check.py` fails with `missing section Lineage` (README absent).
- [ ] Write the six sections, each ≥80 words of substance. Lineage: Gruvbox Dark/Light Hard and SonicTerm modified variant, as in `$R/NOTICE` and `palette/*.json` `provenance`. Roles. Contrast rules: 4.5:1, with `#665c54` dark-restricted. Why Light darkens semantic colors: `#8a5200`/`#9d0006`/`#6b6700`/`#076678` vs the Gruvbox originals on `#f9f5d7`. ANSI slot order. Choosing colors: a worked example mapping **tmux** UI roles (status text, status bg, active border, inactive border, message, mode selection) in two `example:` tables, ratios from `python3 -c "from scripts.common import contrast_ratio as c;print(f'{c(\"#cfbc97\",\"#141617\"):.2f}')"`. Then `python3 scripts/tables.py --write`. CLAUDE.md covers the purpose, commands (`check.py`, tests, `tables.py --write`), that the palette bytes are consumed by `apollo-theme` and the site via `SOURCE.json`, and that a palette change requires `sync_palette.py` downstream.
- [ ] `python3 scripts/check.py && python3 -m unittest discover -s tests` → exit 0. `c "Explain Apollo palette roles, contrast, and app mapping"`.
- [ ] **Gate:** send `$P/README.md` to the Tech Lead (launching agent) for substance review. Do not continue to Task 4 until approved; fold fixes into a new commit.

### Task 4: Publish apollo-palette
**Files:** `$P/.github/workflows/ci.yml` (ubuntu/macos/windows matrix, `actions/checkout@v4`, `setup-python@v5` 3.11, `python scripts/check.py`, `python -m unittest discover -s tests -v`).
- [ ] `c "Add CI"`, then `gh repo create apollo-theme/apollo-palette --public --source $P --push --description "Canonical Apollo Dark and Light palettes and the reasoning behind every color."`
- [ ] `gh run watch --repo apollo-theme/apollo-palette --exit-status $(gh run list --repo apollo-theme/apollo-palette -L1 --json databaseId -q '.[0].databaseId')`. Expected: success.
- [ ] **Done:** `PALETTE_SHA=$(git -C $P rev-parse HEAD)`; `git -C $P show $PALETTE_SHA:palette/apollo.json | cmp - $R/palette/apollo.json` (and the light file) are silent.

### Phase 2: monorepo on branch `consolidate-three-repos` (in `$W`)

### Task 5: Remove all 15 submodules
- [ ] **Acceptance first:** `git ls-files -s | awk '$1==160000' | wc -l` prints `15`.
- [ ] `git rm -q .gitmodules $(git ls-files -s | awk '$1==160000{print $4}') && c "Remove application and management submodules"`
- [ ] **Done:** same command prints `0`; `ls -d *-apollo-theme 2>/dev/null` is empty.

### Task 6: Subtree-import 13 apps with tags
- [ ] **Acceptance first:** `git rev-parse -q --verify refs/tags/bat-v0.1.0` fails.
```sh
for s in sonicterm windows-terminal firefox vscode visual-studio vim nvim xcode tmux rmux powershell bat eza; do
  b=$B/$s-apollo-theme.bundle
  git subtree add --prefix=$s "$b" main -m "Import $s-apollo-theme history into $s/" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || break
  git fetch -q --no-tags "$b" "refs/tags/*:refs/tags/$s-*" || break
done
```
- [ ] **Done:** for each slug, `git merge-base --is-ancestor $(git bundle list-heads $b refs/heads/main | cut -d' ' -f1) HEAD`; `git tag -l '*-v*' | wc -l` = 33 (bundle tag counts: firefox 7, bat 3, powershell 3, ten apps × 2); `git blame -s bat/README.md | head -1` shows a pre-import commit.

### Task 7: Import the retired four
```sh
for p in wezterm:0a23a76 iterm2:4b8666d apple-terminal:67551c9 alacritty:563ac97; do s=${p%%:*}; src=$X/$s-apollo-theme
  git fetch -q --no-tags $src "refs/tags/*:refs/tags/$s-*" && git fetch -q $src main
  [ "$(git rev-parse --short FETCH_HEAD)" = "${p#*:}" ] || { echo "HEAD drift $s"; break; }
  git subtree add --prefix=$s FETCH_HEAD -m "Import $s-apollo-theme history into $s/" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
done
```
**Done:** tags `wezterm-v0.1.0 wezterm-v0.1.1 iterm2-v0.1.0 apple-terminal-v0.1.0 alacritty-v0.1.0` exist; `cmp $s/palette/apollo.json palette/apollo.json` is silent for all four (verified identical today).

### Task 8: 17-app registry, layout and pin checks
**Files:** `scripts/common.py`, `scripts/generate.py`, `scripts/check.py`, `palette/SOURCE.json`, `tests/test_layout.py`, `tests/test_palette.py` (registry assertions, test-first).
- [ ] **Test first** (`tests/test_layout.py`):
```python
import json, subprocess, sys, tempfile, unittest, shutil; from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
from common import APPS, SLUGS; import check
class LayoutTests(unittest.TestCase):
    def test_seventeen_slugs(self): self.assertEqual(17, len(SLUGS))
    def test_every_app_is_a_tracked_folder(self):
        modes = subprocess.run(["git", "ls-files", "-s"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertNotIn("160000", modes); check.check_layout()
    def test_source_pin_matches_palette_bytes(self): check.check_source_pin(ROOT)
    def test_bad_pin_fails(self):
        with tempfile.TemporaryDirectory() as t:
            shutil.copytree(ROOT / "palette", Path(t) / "palette"); p = Path(t) / "palette" / "SOURCE.json"
            d = json.loads(p.read_text()); d["sha256"]["apollo.json"] = "0" * 64; p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError, "apollo.json"): check.check_source_pin(Path(t))
    def test_gecko_ids_unchanged(self):
        for f, gid in (("firefox/manifest.json", "humble-apollo@d0n9x1n"), ("firefox/variants/light/manifest.json", "apollo-light@d0n9x1n")):
            self.assertEqual(gid, json.loads((ROOT / f).read_text())["browser_specific_settings"]["gecko"]["id"])
```
- [ ] Run `python3 -m unittest tests.test_layout -v`. Expected: FAIL `ImportError: cannot import name 'APPS'`.
- [ ] **Implement.** `common.py`: replace `LIGHT_ARTIFACTS`, `APP_METADATA`, `REPOSITORIES`, `MANAGEMENT_REPOSITORIES` with `APPS` keyed by slug. For each existing entry: key = old `slug`; keep `name, family, platform, badge_fragment, install_anchor`; add `light_artifact` = old `LIGHT_ARTIFACTS[repo]`; drop `slug, workflow, description, topics`. Append:
```python
"wezterm": {"name": "WezTerm", "family": "terminal", "platform": "Cross-platform", "badge_fragment": "target-WezTerm%20%C2%B7%20cross--platform-", "install_anchor": "install", "light_artifact": "apollo-light.toml"},
"iterm2": {"name": "iTerm2", "family": "terminal", "platform": "macOS", "badge_fragment": "target-iTerm2%20%C2%B7%20macOS-", "install_anchor": "install", "light_artifact": "Apollo Light.itermcolors"},
"apple-terminal": {"name": "Apple Terminal", "family": "terminal", "platform": "macOS", "badge_fragment": "target-Apple%20Terminal%20%C2%B7%20macOS-", "install_anchor": "install", "light_artifact": "Apollo Light.terminal"},
"alacritty": {"name": "Alacritty", "family": "terminal", "platform": "Cross-platform", "badge_fragment": "target-Alacritty%20%C2%B7%20cross--platform-", "install_anchor": "install", "light_artifact": "apollo-light.toml"},
```
plus `SLUGS = tuple(APPS)`, `CLONE_APPS = ("vim", "nvim", "tmux", "rmux", "powershell", "bat", "eza")`, `MONOREPO = "https://github.com/apollo-theme/apollo-theme"`, and `readme_blocks(text, marker) -> list[str]` (the fenced block bodies following `<!-- smoke:<marker> -->`). `generate.py` and `check.py`: `--repo` → `--app` (choices `SLUGS`), `ROOT / slug`. `check.py`: delete `check_submodules` and the profile check; add:
```python
def check_layout() -> None:
    if (ROOT / ".gitmodules").exists(): raise ValueError(".gitmodules must not exist")
    for slug in SLUGS:
        if not (ROOT / slug).is_dir() or (ROOT / slug / ".git").exists(): raise ValueError(f"{slug}: must be a plain tracked folder")
def check_source_pin(root: Path = ROOT) -> None:
    pin = json.loads((root / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
    if pin.get("repository") != "https://github.com/apollo-theme/apollo-palette" or not re.fullmatch(r"[0-9a-f]{40}", pin.get("commit", "")):
        raise ValueError("SOURCE.json: repository or commit invalid")
    for name in ("apollo.json", "apollo-light.json"):
        if hashlib.sha256((root / "palette" / name).read_bytes()).hexdigest() != pin["sha256"].get(name): raise ValueError(f"SOURCE.json: {name} sha256 mismatch")
```
The nested-`.github` rule is added in Task 11 after those folders are removed, so this task's layout acceptance passes with them present. `check_repository(slug)` uses `APPS[slug]["light_artifact"]` and keeps the gecko block (466-471) under `slug == "firefox"`. `.gitattributes` is still required per folder (retired four: add it if missing, in Task 15). `main()` calls `check_layout(); check_source_pin(); check_palette()`. Write `palette/SOURCE.json` with `python3 scripts/sync_palette.py` in Task 9; for now write it by hand from `$PALETTE_SHA` and `shasum -a 256 palette/*.json`. In `tests/test_palette.py`, written before `common.py` changes, replace lines 131–174:
  - `test_every_repository_declares_a_light_artifact` → `test_every_app_declares_an_existing_light_artifact`: `(ROOT / s / APPS[s]["light_artifact"]).is_file()` for every slug.
  - `test_repository_names_follow_convention` → `test_registry_shape`: `len(SLUGS) == 17`; unique; each slug matches `^[a-z0-9-]+$`, is a folder, and has no `-apollo-theme` suffix; `common` has none of `REPOSITORIES, APP_METADATA, LIGHT_ARTIFACTS, MANAGEMENT_REPOSITORIES`.
  - `test_retired_integrations_are_absent_from_public_surfaces` → `test_retired_apps_are_present`: `wezterm iterm2 apple-terminal alacritty` are in `SLUGS` with folders.
  - `test_app_preview_slugs_are_stable_and_unique` → 17 unique `APPS` keys with no spaces.
  - `test_app_metadata_supports_readmes_and_repository_settings` → `test_app_metadata_supports_readmes`: keys == `{name, family, platform, badge_fragment, install_anchor, light_artifact}` (no `slug/workflow/description/topics`); family is one of the six; the README badge-fragment and install-anchor assertions are kept against `ROOT/slug/README.md`. The retired READMEs already carry both, verified today.
  Also test-first: `test_palette.py:466` `eza-apollo-theme`→`eza`; `:483` `metadata["slug"]`→the `APPS` key; `scripts/check.py:378` SonicTerm identity exception matches slug `sonicterm` (new test: `forbidden_identity_terms("sonicterm", "SonicTerm Apollo Theme") == []`, `("vim", "SonicTerm theme") == ["sonicterm"]`). Gate: `git grep -nE '[a-z-]+-apollo-theme' -- scripts tests` lists only URL/backup strings named in `migration.py`.
  Elsewhere, rename `REPOSITORIES`→`SLUGS`, `APP_METADATA[r]`→`APPS[s]`, `ROOT / repo`→`ROOT / slug`, and delete `test_website_carries_both_exact_palette_snapshots` (line 75; re-homed in the site's own tests).
- [ ] Run `python3 -m unittest tests.test_layout -v && python3 scripts/generate.py --check`. Expected: PASS; 17 `current` lines. `c "Register 17 slug folders and pin apollo-palette"`.

### Task 9: `sync_palette.py`
**Files:** `scripts/sync_palette.py`, `tests/test_sync_palette.py`.
- [ ] **Test first:** in a tmpdir, `git init` a palette repo, commit `palette/apollo.json` = `{"x":1}` and `palette/apollo-light.json` = `{"y":1}`, tag `t1`. Make a root with `palette/`, apps `a`, `b`, each with `palette/` and `scripts/generate.py` containing `open("ran","w").write("1")`. Call `sync(repo, "t1", root, ("a","b"))`. Assert: root, a, and b palette bytes equal the source; `SOURCE.json["commit"]` equals `git rev-parse t1`; `sha256` matches; `a/ran` and `b/ran` exist. A second test runs the CLI with ref `nope`, expecting returncode 2 and stderr `unknown ref nope`.
- [ ] Run. FAIL `No module named 'sync_palette'`.
- [ ] **Implement:**
```python
def sync(repo, ref, root=ROOT, slugs=SLUGS, run=subprocess.run) -> str:
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", f"{ref}^{{commit}}"], capture_output=True, text=True).stdout.strip()
    if not sha: raise LookupError(f"unknown ref {ref}")
    files = {n: subprocess.run(["git", "-C", str(repo), "show", f"{sha}:palette/{n}"], capture_output=True, check=True).stdout for n in ("apollo.json", "apollo-light.json")}
    for target in (root, *(root / s for s in slugs)):
        for n, data in files.items(): (target / "palette" / n).write_bytes(data)
    pin = {"repository": "https://github.com/apollo-theme/apollo-palette", "commit": sha, "sha256": {n: hashlib.sha256(d).hexdigest() for n, d in files.items()}}
    (root / "palette" / "SOURCE.json").write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    for s in slugs: run([sys.executable, "scripts/generate.py"], cwd=root / s, check=True)
    return sha
```
CLI `sync_palette.py <palette-repo> <ref>` maps `LookupError` to stderr and exit 2. Run tests. PASS. Then `python3 scripts/sync_palette.py $P $PALETTE_SHA && git diff --stat -- . ':!palette/SOURCE.json'` is empty. `c "Add palette sync from apollo-palette"`.

### Task 10 (group A): `firefox_release.py` and release workflow
**Files:** `scripts/firefox_release.py`, `.github/workflows/firefox-release.yml`, `tests/test_firefox_release.py`; delete `firefox/.github/workflows/release.yml` in Task 11.
- [ ] **Test first:** `version_from_tag("firefox-v1.1.1") == "1.1.1"`; `version_from_tag("v1.1.1")` and `("firefox-v1.1")` raise `ValueError("tag must look like firefox-vX.Y.Z")`; `check_versions(ROOT/"firefox", "1.1.1")` passes and `"9.9.9"` raises `ValueError` naming dark manifest, light manifest, and package; `check_gecko_ids(dir)` passes, and a tmp copy with a changed light ID raises `ValueError("gecko id changed")`; `build(dir, run=fake)` records `["npm","run","build"]` and returns the two paths `web-ext-artifacts/apollo-theme.zip` and `apollo-light-theme.zip`; `main(["--dry-run","firefox-v9.9.9","--skip-build"])` returns 1 and `main(["--dry-run","firefox-v1.1.1","--skip-build"])` returns 0.
- [ ] Run. FAIL `No module named 'firefox_release'`.
- [ ] **Implement.** `release_notes(tag)` ports release.yml:52-75 with `git describe --tags --abbrev=0 --match 'firefox-v*' "$tag^"`, `git log --no-merges --pretty='- %s (%h) — %an' PREV..TAG -- firefox/`, and the compare URL on `apollo-theme/apollo-theme`. `check_gecko_ids` asserts `humble-apollo@d0n9x1n`/`apollo-light@d0n9x1n`. CLI: `--dry-run TAG` (required), `--skip-build`, `--notes-out PATH`; it runs tag → versions → gecko IDs → build. It prints `attachments:` with both paths (failing if either is missing after the build) and never invokes `gh`. Workflow:
```yaml
name: Firefox release
on: { push: { tags: ["firefox-v*"] } }
permissions: { contents: write }
jobs:
  release:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: firefox } }
    steps:
      - { uses: actions/checkout@v4, with: { fetch-depth: 0 } }
      - { uses: actions/setup-node@v4, with: { node-version: 20, cache: npm, cache-dependency-path: firefox/package-lock.json } }
      - { uses: actions/setup-python@v5, with: { python-version: "3.11" } }
      - run: npm ci && npm run check && npm test && npm run lint
      - run: python3 ../scripts/firefox_release.py --dry-run "$GITHUB_REF_NAME" --notes-out RELEASE_NOTES.md
      - uses: softprops/action-gh-release@v2
        with: { name: "Apollo Themes for Firefox ${{ github.ref_name }}", body_path: firefox/RELEASE_NOTES.md, fail_on_unmatched_files: true,
                files: "firefox/web-ext-artifacts/apollo-theme.zip\nfirefox/web-ext-artifacts/apollo-light-theme.zip" }
```
- [ ] Run tests. PASS. Then locally `(cd firefox && npm ci) && python3 scripts/firefox_release.py --dry-run firefox-v1.1.1` exits 0 and lists two attachments; `--dry-run firefox-v1.1.2` exits 1. `c "Move Firefox release logic into a dry-runnable script"`.

### Task 11 (group A): One root CI
**Files:** `.github/workflows/ci.yml`, delete `*/.github/` (17), `vscode/package.json`, `vscode/scripts/check.py`, `tests/test_ci.py`.
- [ ] **Test first** (`tests/test_ci.py`): read `ci.yml` text; split on `^  ([a-z0-9-]+):$` job keys; assert the job set ⊇ `{"validate","smoke", *SLUGS}`; each slug job body contains `working-directory: {slug}`; `validate` contains `ubuntu-latest, macos-latest, windows-latest`; `smoke` contains `APOLLO_SMOKE_REQUIRED: "1"`; `firefox` job contains `firefox_release.py --dry-run firefox-v`; `glob("*/.github")` is empty; `firefox-release.yml` contains `"firefox-v*"`; `vscode/package.json` `scripts.package` contains `--baseContentUrl https://github.com/apollo-theme/apollo-theme/blob/main/vscode` and `--baseImagesUrl https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/vscode`.
- [ ] Run. FAIL (missing jobs).
- [ ] **Implement.** `validate`: the current ci.yml matrix with `submodules` removed and `fetch-depth: 0`. `smoke`: `macos-15`, `brew install vim neovim tmux rmux bat eza && brew install --cask powershell`, env `APOLLO_SMOKE_REQUIRED: "1"`, `python3 -m unittest tests.test_smoke_install -v`. Per-app job rule: copy `steps` from `<slug>/.github/workflows/<file>` verbatim after `actions/checkout@v4`, set `runs-on` from the source, `defaults.run.working-directory: <slug>`, and rewrite path inputs (`cache-dependency-path: <slug>/package-lock.json`). Example (vim): `runs-on: ubuntu-latest`, `defaults.run.working-directory: vim`, steps checkout → `setup-python` 3.12 → `rhysd/action-setup-vim@v1` (`version: v9.1.0000`) → `python3 scripts/check.py`.
Runners: bat/eza/sonicterm/windows-terminal/wezterm/alacritty/nvim/vim/rmux/tmux/vscode ubuntu-latest; firefox ubuntu-latest + an added step `python3 ../scripts/firefox_release.py --dry-run "firefox-v$(node -p "require('./package.json').version")"`; powershell windows-latest; visual-studio keeps both its ubuntu and windows jobs as `visual-studio` and `visual-studio-windows`; xcode/iterm2/apple-terminal macos-15. Triggers: `push: {branches: [main]}`, `pull_request`, `workflow_dispatch`. `git rm -r -q */.github`, then add to `check_layout` the rule `if (ROOT / slug / ".github").exists(): raise ValueError(f"{slug}: nested .github is not allowed")`. In vscode, append the two flags to `vsce package` and change check.py:261 to `https://github.com/apollo-theme/apollo-theme.git`, together with `repository/homepage/bugs` in package.json (`…/apollo-theme/tree/main/vscode`, `…/apollo-theme/issues`). Run `(cd vscode && python3 scripts/check.py)`.
- [ ] Run tests. PASS. `c "Run every app gate from one root CI workflow"`.

### Task 12 (group A): Migration facts and the offline verifier
**Files:** `scripts/migration.py`, `scripts/verify_migration.py`, `tests/test_verify_migration.py`.
- [ ] **Test first:** in a tmpdir, build `src` repo (commit `README.md`, `a.txt`; tag `v0.1.0`); `git bundle create src.bundle --all`; `mono` repo with one commit, `git subtree add --prefix=x src.bundle main`, `git fetch --no-tags src.bundle 'refs/tags/*:refs/tags/x-*'`. With `source = Source(slug="x", rev=<src main>, tags={"v0.1.0": <sha>}, allow=("README.md",))`: `check_tree(mono, source) == []`; after editing `x/README.md` and committing → still `[]`; after editing `x/a.txt` and committing → `["x: a.txt differs from source"]`; `check_history` passes; after `git tag -f x-v0.1.0 HEAD`, `check_tags` → `["x: tag x-v0.1.0 not on <sha>"]`. `check_live_source("bat-apollo-theme", backup, ls_remote=fake, api=fake)` → `[]` when refs and releases match the bundle and JSON, `["bat-apollo-theme: refs differ from bundle"]` for a moved fake ref, `["bat-apollo-theme: release v0.1.0 differs from backup"]` for an edited fake body or digest.
- [ ] Run. FAIL `No module named 'migration'`.
- [ ] **Implement** `migration.py`:
```python
MIGRATION_LINE = "_Migrated from `apollo-theme/{repo}` on 2026-11-09; the original repository was consolidated into `apollo-theme/apollo-theme`._"
def migrated_body(original: str, repo: str) -> str: return original.rstrip("\n") + "\n\n" + MIGRATION_LINE.format(repo=repo) + "\n"
COMMON_ALLOW = ("README.md", "CLAUDE.md", ".github/*", ".gitattributes")
ALLOWLIST = {"firefox": ("package.json",), "vscode": ("package.json", "scripts/check.py"), "powershell": ("ApolloTheme.psd1", "scripts/generate.py"),
             "wezterm": ("apollo.toml", "apollo-light.toml", "scripts/generate.py", "scripts/check.py"),
             "tmux": ("scripts/check.py", "tests/test_theme.py"), "rmux": ("scripts/check.py", "tests/test_theme.py"), "eza": ("scripts/check.py", "tests/test_theme.py"), "bat": ("tests/test_theme.py",)}
RETIRED = {"wezterm": "0a23a76", "iterm2": "4b8666d", "apple-terminal": "67551c9", "alacritty": "563ac97"}
@dataclass(frozen=True)
class Source: slug: str; rev: str; tags: dict; allow: tuple
def sources(backup: Path, retired: Path) -> list[Source]  # bundle list-heads for 13; `git -C clone show-ref -d --tags` + full rev-parse for RETIRED
```
`verify_migration.py`: `check_tree` uses `git diff --name-only <rev>^{tree} HEAD:<slug>` filtered by `fnmatch` against `COMMON_ALLOW + ALLOWLIST.get(slug, ())`; `check_history` uses `git merge-base --is-ancestor`; `check_tags` compares commits only: source tags are peeled (`git -C <mirror-of-bundle> rev-parse <tag>^{commit}`; retired: `show-ref -d`), destination via `git rev-parse <slug>-<tag>^{commit}` (offline) or the `^{}` line when present else the plain line from `git ls-remote --tags origin` (online). Fixtures: a lightweight tag, an annotated tag (Firefox `v1.1.1`: object `66a5737`, commit `c4bc29f`) that must pass, and a moved tag that must fail. Online only: `check_pushed` (`ls-remote origin refs/heads/main` == `HEAD`) and `check_pin` (`gh api repos/apollo-theme/apollo-palette/contents/palette/<f>?ref=<commit> -H 'Accept: application/vnd.github.raw'` sha256 == SOURCE). `check_live_source(repo, backup, ls_remote, api)` (online; CLI `--live-source REPO`, combinable with `--app`): `git ls-remote --heads --tags https://github.com/apollo-theme/<repo>` minus `^{}` lines equals the bundle's `refs/heads|refs/tags` list, and `gh api repos/apollo-theme/<repo>/releases --paginate` equals the backup JSON after `normalize` (tag, name, body, asset name, size, SHA-256) (`.github` → `dot-github.bundle`). An app's allowlist may grow only in the commit that edits that file. Release comparisons go through `normalize(release, download=None) -> dict`. It accepts the backup shape (`gh release view` JSON: `tagName`, `name`, `body`, `assets[].name/size/digest`) or the REST shape (`tag_name`, `name`, `body`, `assets[].name/size/digest`) and returns `{tag, name, body (CRLF→LF, trailing whitespace stripped), assets: sorted (name, size, sha256)}`. Raw `id`/`node_id`/`apiUrl`/`url`/download counts are never compared; a missing `digest` is filled by `download(asset)` + sha256. Test-first fixtures: `tests/fixtures/releases/bat-v0.1.0.backup.json` (copy of `$B/releases/bat-apollo-theme/v0.1.0.json`) and `bat-v0.1.0.rest.json` (recorded now with `gh api repos/apollo-theme/bat-apollo-theme/releases/tags/v0.1.0`, while the repo exists). Tests: `normalize(backup) == normalize(rest)`; with REST `digest` removed and a fake downloader returning bytes hashing to `f9d7c4af…d65b`, still equal; a changed `size` or `body` differs. Fail-closed: any subprocess error, missing bundle/backup file, or missing release becomes an error string, never a skip. CLI `[--app SLUG] [--offline] [--backup B] [--retired X]` prints each error and exits 1 if any, else prints `verified N apps` and exits 0.
- [ ] Run. PASS. Then `python3 scripts/verify_migration.py --offline`. Expected: `verified 17 apps`, exit 0, because so far only allowlisted files (`.github/*`, vscode `package.json`/`scripts/check.py`) have changed. `c "Add offline migration verifier"`.

### Task 13: Release restore and release verification
**Files:** `scripts/restore_releases.py`, `scripts/verify_migration.py` (add `check_releases`), `tests/test_restore_releases.py`.
- [ ] **Test first:** a temp backup `releases/bat-apollo-theme/v0.1.0.json` (name `v0.1.0`, body `b`, asset `Apollo.tmTheme` with digest `sha256:<h>`) plus `v0.1.0/Apollo.tmTheme`. `plan_releases(backup)` → `[Plan(tag="bat-v0.1.0", title="bat v0.1.0", body=migrated_body("b","bat-apollo-theme"), assets=[path])]`. If the name ≠ tag, the title keeps the original name. A JSON with assets but no asset dir raises `FileNotFoundError`. A local asset whose sha ≠ JSON digest raises `ValueError`. `apollo-theme/` and `apollo-theme.github.io/` and `.github/` are excluded. `check_releases(backup, api=fake, download=fake)` returns `[]` for matching data and `["bat-v0.1.0: body differs"]` / `["bat-v0.1.0: Apollo.tmTheme sha256 differs"]` / `["v0.3.1: release changed"]` for the corresponding fakes.
- [ ] Run. FAIL.
- [ ] **Implement.** `--apply` loops the plans and skips tags already present (`gh release view TAG`). Otherwise it runs `gh release create TAG --repo apollo-theme/apollo-theme --verify-tag --title T --notes-file tmp --latest=false ASSETS...`. Without `--apply` it prints the plans. In `check_releases`, `api` = `gh api repos/apollo-theme/apollo-theme/releases --paginate` and `download` = `gh release download TAG -p NAME -D tmp` + sha256. Each restored release must satisfy `normalize(live) == normalize(backup)` after mapping tag → `<slug>-<tag>`, name → planned title, and body → `migrated_body`; each local backup file's sha256 must also equal the JSON digest. For `apollo-theme/v0.1.0…v0.3.1`, `name`, `body`, and the tag commit must be unchanged. Retired apps are not checked here. Run tests. PASS. `c "Add release restore and release verification"`.

### Task 14: README contract for the monorepo
**Files:** `scripts/check.py` (`check_readme_contract`), `tests/test_readme_contract.py`.
- [ ] **Test first:** build a valid README string for `bat` from a helper, then assert `ValueError` messages for: missing `[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"`; `rm -rf "$HOME/.config/apollo-theme"` inside `## Uninstall`; a missing `## Remove the shared clone` section or one omitting any `CLONE_APPS` name; a missing `smoke:install`/`smoke:uninstall` marker; any `github.com/apollo-theme/<x>-apollo-theme` URL. A non-clone app (`xcode`) needs none of the clone rules.
- [ ] Run. FAIL.
- [ ] **Implement.** Change the fragments to: workflow badge `img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml`; release badge `img.shields.io/github/v/release/apollo-theme/apollo-theme?filter={slug}-v`; license links `href="LICENSE"` or `{MONOREPO}/blob/main/{slug}/LICENSE`; keep the preview/deep-link/appearance rules. Add the clone rules for `CLONE_APPS` and the dead-URL regex `github\.com/apollo-theme/[a-z0-9-]+-apollo-theme` over README, CLAUDE.md, and `public_identity_metadata`. Unit tests PASS. Full `check.py` fails until Task 15 lands (expected). `c "Require monorepo URLs and shared-clone install docs"`.

### Task 14b (group C, 4 parallel worktrees): Shared-clone paths in tmux, RMUX, eza, bat checks
Each app on branch `paths/<slug>` off the consolidation branch, merged with `--no-ff`. This task also does that app's full Task 15 README rewrite; the files are on its Task 12 allowlist.
- [ ] **Test first** (`<slug>/tests/test_theme.py`): tmux expects `'tmux source-file "$HOME/.config/apollo-theme/tmux/apollo.tmux"'` / `…/apollo-light.tmux` (lines 270-271); rmux expects `'rmux source-file "$HOME/.config/apollo-theme/rmux/apollo-rmux.conf"'` / `…-light.conf` (269-270); eza expects `'EZA_CONFIG_DIR="$HOME/.config/apollo-theme/eza" eza --color=always -la'` / `…/eza/light …` (270-271); bat replaces `.installed-theme-hashes` with `.apollo-theme-hashes` (line 308) and its fixture's marker (line 327) with `"$theme_dir/.apollo-theme-hashes"`, keeping the hash-guarded uninstall assertions.
- [ ] Run `cd <slug> && python3 -m unittest discover -s tests`. Expected: FAIL (`README contract missing dark source command` for tmux/rmux, `…dark activation command` for eza, `'.apollo-theme-hashes' not found` for bat).
- [ ] Set tmux/rmux/eza `scripts/check.py` `README_CONTRACT_MARKERS` (lines 21-25) to the same strings and rewrite the README with the Task 15 template in the same commit. Run the app tests, `python3 scripts/check.py`, and `python3 ../scripts/verify_migration.py --offline --app <slug>`. All exit 0. `c "Use shared-clone paths in <slug> checks"`.

### Task 15 (group B, 13 parallel sub-tasks): Per-app docs and URLs
For each slug not done in Task 14b: `git worktree add $W-$s -b docs/$s consolidate-three-repos`. **Acceptance first:** `python3 scripts/check.py --app $s` fails with the Task 14 messages. Edit only `$s/` files on that app's allowlist (Task 12). Then run `python3 scripts/check.py --app $s && (cd $s && python3 scripts/generate.py --check && python3 -m unittest discover -s tests)` (exit 0) and `c "Point $s docs at the monorepo"`. Merge back with `git merge --no-ff docs/$s` in slug order.
- Clone apps' README template: Install starts with the idempotent clone line, then a `<!-- smoke:install -->` `sh` block that activates from `$HOME/.config/apollo-theme/<slug>/…`. Uninstall is a `<!-- smoke:uninstall -->` block removing only the activation. Then `## Remove the shared clone`: "Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `rm -rf "$HOME/.config/apollo-theme"`." Activation lines (exact, since probes depend on them):
  - vim: `printf '%s\n' 'set runtimepath^=~/.config/apollo-theme/vim' 'colorscheme apollo' >> "$HOME/.vimrc"`; uninstall `sed -i.bak '/apollo-theme\/vim/d;/^colorscheme apollo/d' "$HOME/.vimrc"`. Also document `Plug 'apollo-theme/apollo-theme', { 'rtp': 'vim' }`.
  - nvim: the lazy spec (`<!-- smoke:lazy -->` lua block) `{ 'apollo-theme/apollo-theme', lazy = false, priority = 1000, config = function(plugin) vim.opt.rtp:append(plugin.dir .. "/nvim"); vim.cmd.colorscheme("apollo") end }`. Manual: `mkdir -p "$HOME/.config/nvim" && printf '%s\n' 'vim.opt.rtp:append(vim.env.HOME .. "/.config/apollo-theme/nvim")' 'vim.cmd.colorscheme("apollo")' >> "$HOME/.config/nvim/init.lua"`; uninstall `sed -i.bak '/apollo-theme\/nvim/d;/colorscheme("apollo/d' "$HOME/.config/nvim/init.lua"`.
  - tmux: `echo "source-file \"$HOME/.config/apollo-theme/tmux/apollo.tmux\"" >> "$HOME/.tmux.conf"`; uninstall `sed -i.bak '/apollo-theme\/tmux/d' "$HOME/.tmux.conf"`. RMUX: the same with `rmux/apollo-rmux.conf` into `~/.rmux.conf` (RMUX's default config file, named in its README); uninstall `sed -i.bak '/apollo-theme\/rmux/d' "$HOME/.rmux.conf"`.
  - bat: the existing hash-guarded copy/remove blocks with `clone_dir="$HOME/.config/apollo-theme/bat"` and the marker moved to `"$theme_dir/.apollo-theme-hashes"`, so nothing is written inside the clone.
  - eza: `echo 'export EZA_CONFIG_DIR="$HOME/.config/apollo-theme/eza"' >> "$HOME/.profile"`; uninstall `sed -i.bak '/apollo-theme\/eza/d' "$HOME/.profile"`.
  - powershell (pwsh blocks): install `New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null; Add-Content $PROFILE 'Import-Module "$HOME/.config/apollo-theme/powershell/ApolloTheme.psd1"', 'Enable-ApolloTheme -Variant Dark'`, documenting `-Variant Light` as the alternative line; uninstall `Set-Content $PROFILE (Get-Content $PROFILE | Where-Object { $_ -notmatch 'ApolloTheme' })`, plus `Disable-ApolloTheme; Remove-Module ApolloTheme` for a running session. Regenerate the psd1 with `ProjectUri = 'https://github.com/apollo-theme/apollo-theme/tree/main/powershell'`.
- Copy-based apps (sonicterm, xcode, wezterm, alacritty): Install starts with the idempotent clone line, and every `cp` uses full quoted sources, e.g. `cp "$HOME/.config/apollo-theme/xcode/Apollo Light.xccolortheme" ~/Library/Developer/Xcode/UserData/FontAndColorThemes/`. Uninstall removes only the copies; they are not in `CLONE_APPS` because the copies outlive the clone. Import-based apps (windows-terminal, iterm2, apple-terminal, visual-studio) name the file by full path `~/.config/apollo-theme/<slug>/<file>` after the clone line and offer `https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/<slug>/<file>` as the no-clone alternative. vscode installs by local packaging from the clone: `cd ~/.config/apollo-theme/vscode && npm ci && npm run package && code --install-extension dist/apollo-theme.vsix` (uninstall `code --uninstall-extension apollo-theme.apollo-theme`). Release assets carry no dual-theme VSIX, so the README never points at them; sub-plan Step 1 tests this. firefox installs from release assets at `…/releases?q=firefox-v`. All repo URLs become `…/apollo-theme/tree/main/<slug>`; firefox `package.json` repository → monorepo `directory: firefox`. Any app test or checker asserting old README text is updated test-first in the same commit, and its file is added to that app's allowlist.
- Retired four: one commit, `c "Raise retired app docs to the current contract"`, covering README/CLAUDE to the contract, a `.gitattributes` with `* text=auto eol=lf` if missing, and wezterm `REPOSITORY_URL` → `…/tree/main/wezterm` + `python3 scripts/generate.py`.
- **Done:** `python3 scripts/check.py` exit 0; `python3 scripts/verify_migration.py --offline` exit 0.

### Task 16: Documented paths and Behavior 5 smoke tests (sub-plan)
**Files:** `tests/test_readme_paths.py`, `tests/test_smoke_install.py`, `tests/fixtures/readme_paths/*`. Execute `docs/plans/2026-11-09-three-repo-consolidation-smoke-subplan.md` Steps 1–4 exactly. In summary: copy sources parsed with `shlex` (relative sources fail; variables, loops, and spaced names handled); the VS Code local-packaging path; loader probes (bat uses its own `BAT_CONFIG_DIR`/`BAT_CACHE_PATH`) kept separate from activation probes; `COLORTERM=truecolor`; tmux/RMUX on `-L apollo-smoke-<uuid>` with a fresh server per assertion and `kill-server` in `finally`; argument lists only; runs only in CI job `smoke` (macos-15). It skips with explicit messages on Windows, in other CI jobs, and when a tool is absent locally.
- [ ] **Done:** `python3 -m unittest tests.test_readme_paths tests.test_smoke_install -v` PASS locally, with pwsh SKIP ("pwsh not installed locally; CI job 'smoke' runs it"). Committed.

### Task 17: Parent tests, README, CLAUDE.md
**Files:** `tests/test_palette.py`, `README.md`, `CLAUDE.md`.
- [ ] **Test first:** `test_authoritative_readmes…` surfaces = parent `README.md` only (the site and profile surfaces are removed), plus an assertion that it links all 17 `tree/main/<slug>` folders and `apollo-palette`, and has no `-apollo-theme` repo URL. Run. FAIL on README.
- [ ] Rewrite `README.md` as the landing page: Dark/Light statement, link to the site and `apollo-palette`, a 17-row app table (name, folder link, platform, preview links), the shared-clone note, development commands (`generate.py --check`, `check.py`, unit tests, `sync_palette.py`), release-tag scheme `<slug>-vX.Y.Z`. Rewrite `CLAUDE.md` with: the monorepo shape (17 folders, each standalone: `cd <slug> && python3 scripts/generate.py --check`); palette flow (change in apollo-palette → CI green → `sync_palette.py $P <ref>` → check → commit); release tags `<slug>-v*`, with `firefox-v*` publishing via `firefox-release.yml`; gecko ID invariant; the site as a peer repo pinned by its own `SOURCE.json`; removal of all submodule and organization-profile rules; and the palette invariants kept verbatim.
- [ ] Run the full gate: `python3 scripts/generate.py --check && python3 scripts/check.py && python3 -m unittest discover -s tests -v`. PASS. `c "Describe the Apollo monorepo"`.

### Task 18: Push branch and get CI green (main not yet)
- [ ] `git push -u origin consolidate-three-repos && gh pr create --repo apollo-theme/apollo-theme --title "Consolidate app repositories into the monorepo" --body-file <(printf 'Implements docs/specs/2026-11-09-three-repo-consolidation-design.md.\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n')`
- [ ] `git push origin --tags` (one push of more than 3 tags creates no tag-push events; imported `firefox-v*` tags point at commits without the root `firefox-release.yml`). Check: `git ls-remote --tags origin | grep -v '\^{}' | grep -c -- '-v'` = 38 (33 + 5 retired).
- [ ] `gh pr checks --watch --fail-fast` → every check passes (validate×3, smoke, 17 app jobs + visual-studio-windows). On failure, fix with a new commit; never squash.
- [ ] **Done:** every PR check is green on the branch. `main` is not pushed until the previews (Task 19) and releases (Task 20) are live.

### Phase 3: previews only (public links unchanged)

### Task 19: Site publishes 34 previews; ports and links unchanged
**Files (in `$S`):** `scripts/generate.py`, `scripts/check.py`, `tests/test_site.py`, `palette/SOURCE.json`, `previews/*`, `index.html`, `CLAUDE.md`.
- [ ] `git clone https://github.com/apollo-theme/apollo-theme.github.io $S && cd $S && git show 22a4240 -- scripts tests | git apply -R` restores the 4 App rows and renderers. Add `App.listed: bool` (the retired four `False`). `render_index` iterates only listed apps; previews render for all 17.
- [ ] **Test first:** `test_previews_for_all_apps` expects 34 SVGs, including `wezterm iterm2 apple-terminal alacritty` (+`-light`). `test_index_lists_only_listed_apps` expects 13 ports, each linking its existing `github.com/apollo-theme/<slug>-apollo-theme` (live until Task 21). `test_hash_reads_source_pin` expects a wrong sha in a tmp `SOURCE.json` to fail `check_palette`. The restored 17-port counts become `len(LISTED)`. Run. FAIL: 8 previews missing.
- [ ] **Implement:** `check.py` reads `EXPECTED_HASHES` from `palette/SOURCE.json` (a byte copy of the monorepo's) and expects `2 * len(APPS)` SVGs and `len(LISTED)` ports. `python3 scripts/generate.py && python3 scripts/check.py && python3 -m unittest discover -s tests -v` → PASS. `c "Publish previews for all 17 apps"`, `git push origin main`.
- [ ] **Done:** Pages succeeds; the live index has 13 `class="app-port"`; `for s in wezterm iterm2 apple-terminal alacritty; do for f in $s $s-light; do curl -sfI https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/$f.svg >/dev/null || echo MISSING $f; done; done` prints nothing.

### Phase 4: releases → main → full verification → final site links

### Task 20: Re-create releases (tags are on the remote since Task 18)
- [ ] `cd $W && python3 scripts/restore_releases.py` prints 33 plans (no `.github`, site, or apollo-theme entries). Then `python3 scripts/restore_releases.py --apply`.
- [ ] **Done:** `gh release list -R apollo-theme/apollo-theme -L 100 --json tagName -q '.[].tagName' | wc -l` = 38 (33 + `v0.1.0`–`v0.3.1`); `gh release view -R apollo-theme/apollo-theme --json tagName -q .tagName` (no tag = latest) prints `v0.3.1`.

### Task 20b: Publish main, verify, then switch site links
- [ ] `git push origin HEAD:main` (fast-forward; never squash). CI gate bound to the final SHA: `SHA=$(git rev-parse HEAD); id=$(gh run list -R apollo-theme/apollo-theme --commit $SHA --workflow ci.yml -L1 --json databaseId -q '.[0].databaseId'); gh run watch $id -R apollo-theme/apollo-theme --exit-status` (exit 0 required; any root or per-app job failure fails). On exit 0 run `echo $SHA > $R/.build/ci-green-sha`. Repeat this gate after every corrective commit; Task 21 aborts unless `$(cat $R/.build/ci-green-sha)` equals `git ls-remote origin refs/heads/main`.
- [ ] `python3 scripts/verify_migration.py` (online). Expected `verified 17 apps`, exit 0. Fix only by new commits or by re-creating a release; never edit backups.
- [ ] **Test first** (`$S`): `test_all_apps_listed_with_monorepo_links` (17 ports, each with `tree/main/<slug>`, `blob/main/<slug>/README.md`, `releases?q=<slug>-v`) and `test_no_links_to_deleted_repositories` (`re.findall(r'github\.com/apollo-theme/([\w.-]+)', html + readme)` ⊆ `{"apollo-theme", "apollo-theme.github.io", "apollo-palette"}`). Run. FAIL. Set every `listed=True`; `App.repo/readme/releases` → `f"{MONOREPO}/tree/main/{slug}"`, `…/blob/main/{slug}/README.md`, `…/releases?q={slug}-v`. Update README/CLAUDE.md (17 anchors, 34 SVGs, SOURCE pin, monorepo + `apollo-palette` links, no org profile). PASS. `c "List 17 apps with monorepo links"`, `git push origin main`.
- [ ] **Done:** Pages succeeds; 17 ports; `curl -s https://apollo-theme.github.io/ | grep -o 'apollo-theme/apollo-theme/tree/[a-z0-9-]*/' | sort -u` prints only `…/tree/main/`.

### Phase 5: deletion (only after Task 20b's verify exits 0)

### Task 21: Freeze, re-verify, delete 15 repositories, then clean up
Freeze: remaining repos are archived first (reversible with `-F archived=false`); archived repos stay readable for `ls-remote`, release APIs, and downloads. Resumable through the ledger `$R/.build/deletion-ledger.json` (`[{repo, verified_and_deleted_at}]`). A rerun skips exactly the ledger repos after confirming they return 404; any 404 for a repo not in the ledger aborts. `set -e`: any failing gate aborts the whole script before later deletions, including `.github` and `demo-repository`.
```bash
set -euo pipefail; cd $W; L=$R/.build/deletion-ledger.json; [ -f "$L" ] || echo '[]' > "$L"
[ "$(cat $R/.build/ci-green-sha)" = "$(git ls-remote origin refs/heads/main | cut -f1)" ] || { echo 'CI not green on final main'; exit 1; }
DEL="$(for s in $APPS13; do printf '%s-apollo-theme ' $s; done).github demo-repository"
status() { gh api -i "repos/apollo-theme/$1" 2>/dev/null | awk 'NR==1{print $2}'; }
in_ledger() { python3 -c 'import json,sys; sys.exit(sys.argv[2] not in [e["repo"] for e in json.load(open(sys.argv[1]))])' "$L" "$1"; }
record() { python3 -c 'import json,sys,datetime as d; l=json.load(open(sys.argv[1])); l.append({"repo":sys.argv[2],"verified_and_deleted_at":d.datetime.now(d.timezone.utc).isoformat()}); json.dump(l,open(sys.argv[1],"w"),indent=2)' "$L" "$1"; }
TODO=""; for r in $DEL; do st="$(status "$r" || true)"
  if in_ledger "$r"; then [ "$st" = 404 ] || { echo "ledger has $r but HTTP $st"; exit 1; }
  else [ "$st" = 200 ] || { echo "$r is HTTP $st but not in ledger"; exit 1; }; TODO="$TODO $r"; fi; done
for r in $TODO; do gh api -X PATCH "repos/apollo-theme/$r" -F archived=true >/dev/null; done
python3 scripts/verify_migration.py                                    # full online gate (reads only apollo-theme + backups)
for r in $TODO; do python3 scripts/verify_migration.py --live-source "$r"; done   # live == backup before any delete
git bundle verify -q $B/dot-github.bundle; git bundle verify -q $B/demo-repository.bundle; [ "$(ls $B/releases/.github/*.json | wc -l)" -eq 3 ]
for r in $TODO; do s="${r%-apollo-theme}"; a=(); [ "$s" != "$r" ] && a=(--app "$s")
  python3 scripts/verify_migration.py ${a[@]+"${a[@]}"} --live-source "$r"   # empty-array safe on bash 3.2   # .github: text-only releases not migrated; verified backup is their archive (Decision 11)
  gh repo delete "apollo-theme/$r" --yes; record "$r"; done
[ "$(gh repo list apollo-theme --limit 50 --json name -q '.[].name' | sort | tr '\n' ' ')" = "apollo-palette apollo-theme apollo-theme.github.io " ]
```
On abort: fix the cause, unarchive anything that needs a write, rerun (the ledger resumes). Then `gh repo edit apollo-theme/apollo-theme --description "Apollo Dark and Light themes for 17 apps" --homepage https://apollo-theme.github.io`.
- [ ] Transition `$R` without `deinit --all`. For each of the 13 `*-apollo-theme`, `apollo-theme.github.io`, and `.github/organization`, record `git -C $d status --porcelain --ignored`, `git -C $d stash list`, `git -C $d log --branches --not --remotes --oneline`, `lsof +D $d`, `.git/modules/<d>/index.lock`, and `tmux`/`rmux list-sessions -F '#{session_path}'` under it. Run `git submodule deinit -f -- $d` only when every check is empty (ignored `node_modules`, `web-ext-artifacts`, `__pycache__` allowed); otherwise keep it and report it. Then `cmp` and move aside the untracked spec/plan copies, `git pull --ff-only`, `git status`. The work clones `$W`, `$W-<slug>` worktrees, and `$S` are **not** removed here. They are left for the final /fc-clean step with the same checks (lsof, sessions, locks, worktrees, stashes, `git log --branches --not --remotes`). `$B`, `$X`, `.git/modules`, and the ledger are kept and reported.
- [ ] **Done:** `git -C $R log -1 --oneline` equals `origin/main`; Behaviors 1–8 each have a recorded command output in the report.

## Concerns (for the report)

1. Spec Decision 11: the `.github` text-only releases (v1.0.0–v1.1.1) are not migrated; the verified backup (`$B/dot-github.bundle`, `$B/releases/.github/*.json`) is their archive. Task 21 re-verifies both and live == backup before deleting `.github`.
2. 13 backed-up app releases have 0 assets (every v0.2.0 plus nvim v0.1.0) and are re-created as body-only releases. 33 releases are restored in total, one per imported app tag.
3. Five generators/tests hard-code palette SHA-256s (vim, nvim, visual-studio, vscode, xcode). They are unaffected now, but a future `sync_palette.py` with a new palette fails until those pins move. The plan does not change that (non-goal: palette changes).
4. Lazy.nvim and vim-plug clone into their own directories, not `~/.config/apollo-theme`. The plugin-manager paths are documented, and the smoke tests run their exact `config`/`rtp` code against the shared clone.
