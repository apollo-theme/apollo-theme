# Three-Repository Consolidation Design

## Purpose

Reduce the `apollo-theme` GitHub organization to exactly three repositories:

| Repository | Role |
| --- | --- |
| `apollo-palette` (new) | Canonical Dark and Light palettes plus why and how each color was chosen. |
| `apollo-theme` (existing) | Every app theme: 13 current apps plus WezTerm, iTerm2, Apple Terminal, Alacritty. |
| `apollo-theme.github.io` (existing) | Demo site. Org-root Pages requires this name. |

All other repositories (13 apps, `.github`, `demo-repository`) are deleted only after `scripts/verify_migration.py` passes. Backups are in `.build/org-backup-2026-11-09/`.

## Decisions (agent's calls under the session goal)

1. Layout is top-level `<slug>/` folders; no slug collides with `scripts/`, `tests/`, `palette/`, or `docs/`.
2. Import with `git subtree add --prefix=<slug> <bundle> main` (no `--squash`). The retired four come from `.build/apollo-light-crlf-audit/<slug>-apollo-theme` at HEADs wezterm `0a23a76`, iterm2 `4b8666d`, apple-terminal `67551c9`, alacritty `563ac97`, then one commit raises their docs to the current contract.
3. Each app keeps its `palette/` snapshot, generator, checks, and tests; `cd <slug> && python3 scripts/generate.py --check` works standalone.
4. `palette/SOURCE.json` in `apollo-theme` and the site records the `apollo-palette` commit and both SHA-256s.
5. Tags import as `<slug>-v<version>`. Backed-up releases are re-created on them with original notes, a migration line, and identical assets. Existing `apollo-theme` releases `v0.1.0`–`v0.3.1` stay. The retired four get tags only (their release assets were lost).
6. Firefox releases trigger on `firefox-v*`; version is `${GITHUB_REF_NAME#firefox-v}`. Gecko IDs `humble-apollo@d0n9x1n` and `apollo-light@d0n9x1n` never change.
7. One root `ci.yml`: root gate on ubuntu/macOS/Windows plus one job per app reproducing its old workflow with `working-directory: <slug>`. Nested workflow files are removed.
8. Repo URLs move to `github.com/apollo-theme/apollo-theme` or `…/tree/main/<slug>`. Every clone-based install clones once to `~/.config/apollo-theme` and references `<slug>/…` beneath it. Per-app uninstall removes only that app's activation (config line, copied files, cache entry) and never deletes the shared clone; a separate "Remove the shared clone" step names every app that depends on it. VS Code packaging passes `--baseContentUrl`/`--baseImagesUrl`.
9. Vim: `Plug 'apollo-theme/apollo-theme', { 'rtp': 'vim' }`. lazy.nvim: `lazy = false`, `config = function(plugin) vim.opt.rtp:append(plugin.dir .. "/nvim") end`. If that fails headless, add root `colors/` shims.
10. The site returns to 17 apps; links target `tree/main/<slug>`, its README, and `releases?q=<slug>-v`.
11. `.github` (org profile) and `demo-repository` are deleted; the site and `apollo-theme` README become landing pages. The `.github` text-only releases are not migrated; the verified backup is their archive.
12. `apollo-palette` starts with fresh history; its first commit names the source `apollo-theme` commit.

## `apollo-palette`

- `palette/apollo.json`, `palette/apollo-light.json`, byte-identical to today's files.
- `README.md` sections: Lineage; Roles; Contrast rules; Why Apollo Light darkens semantic colors; ANSI slot order; Choosing colors for a new app, with a worked example mapping one app's UI roles in both variants.
- `scripts/tables.py` generates the role and contrast tables between markers; `scripts/check.py` fails on stale tables, schema, slot-order, or contrast errors, a missing required README section, or a section under 80 words of prose.
- The worked example is a table per variant (role, chosen hex, background, contrast ratio, reason); `check.py` parses it and fails unless every hex exists in that variant's palette and every stated ratio matches the computed one to two decimals.
- `NOTICE`, `LICENSE`, `CLAUDE.md`, CI, tests.

## `apollo-theme` changes

- Replace 15 submodules with 17 subtree folders.
- `scripts/common.py`: 17 slug-keyed apps.
- `scripts/check.py`: drop submodule checks; require real folders, the SOURCE pin, gecko IDs, byte-identical app snapshots, README contracts.
- `scripts/sync_palette.py <palette-repo> <ref>`: resolve `<ref>`, write the root and 17 app snapshots plus `SOURCE.json`, run every generator.
- `scripts/verify_migration.py`: offline pre-deletion gate (Behavior 4).
- `scripts/firefox_release.py --dry-run <tag>`: the release workflow's only logic, covering tag parsing, version agreement with both manifests and `package.json`, building both ZIPs, and listing attachments, never publishing.
- Tests: rewritten for 17 folders, the pin, `sync_palette.py` against a fixture palette repository, and the Firefox dry run.
- `README.md`, `CLAUDE.md` describe the monorepo; `NOTICE` stays.

## Site changes

17 apps and 34 previews in the generator, check, and tests; hash check reads `palette/SOURCE.json`; the four restored previews are regenerated.

## Behavior (must pass)

1. `gh repo list apollo-theme` returns exactly `apollo-palette`, `apollo-theme`, `apollo-theme.github.io`.
2. In `apollo-theme`: `python3 scripts/generate.py --check`, `python3 scripts/check.py`, `python3 -m unittest discover -s tests -v` pass, and every folder passes its own generator check and tests.
3. Root CI is green on ubuntu, macOS, Windows, and every per-app job is green.
4. `python3 scripts/verify_migration.py` passes against the pushed `apollo-theme` and live GitHub releases, checking all 17 apps:
   - **Tree:** each folder equals its source revision except files on a per-app allowlist of migration edits (URLs, badges, workflows, install docs, retired-app docs).
   - **History:** the source revision is an ancestor of `HEAD`.
   - **Tags:** every source tag exists as `<slug>-<tag>` on the same commit.
   - **Releases:**
     - Every backed-up release exists with its original body plus the migration line, and the same asset names and SHA-256s.
     - Releases `v0.1.0`–`v0.3.1` are unchanged.

   Repository deletion runs only after this exits 0.
5. From a fresh clone of `apollo-theme` at `~/.config/apollo-theme` under a scratch `HOME`, smoke tests load `apollo` and `apollo-light` through every README's documented path: Vim (`rtp`), Neovim (lazy-style `rtp:append`), tmux and RMUX (`source-file`), bat (`cache --build`, `--list-themes`), eza (`EZA_CONFIG_DIR`), PowerShell (`Import-Module`). Each documented copy source path exists. Running each documented per-app uninstall leaves the shared clone, an unrelated local file in it, and every other installed app working.
6. `apollo-palette` CI is green; README sections, prose minimums, worked-example ratios, and tables pass its check; its palette bytes equal both pinned snapshots; the Tech Lead review reads the rationale for substance before publishing.
7. The site deploys; its HTML lists 17 apps with no link to a deleted repository.
8. `scripts/firefox_release.py --dry-run firefox-v<current>` passes and fails on a mismatched tag. Gecko IDs are unchanged.

## Non-goals

Store publishing; palette changes; GitHub restore; renaming.

## Prior art

Solarized (per-app folders, README rationale); Tokyo Night (`extras/<app>/`); Catppuccin (palette repository, style guide); release-please (`<component>-v<version>`).

## Trade-offs

19 palette snapshots duplicate data but keep standalone generation (byte checks prevent drift). Plugin managers clone all apps (~2 MB). Deleting `.github` loses the org profile.
