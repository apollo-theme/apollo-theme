# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project shape

This is the Apollo Theme monorepo, `apollo-theme/apollo-theme`. It is one of three repositories in the `apollo-theme` organization:

- [`apollo-theme/apollo-palette`](https://github.com/apollo-theme/apollo-palette) is the source of truth for both palettes and documents why and how each color was picked. The dark palette derives from SonicTerm's higher-contrast Gruvbox Dark Hard variant; the light palette is the accessibility-hardened Gruvbox Light Hard. Do not substitute the unrelated 46-color palette also named Apollo or the obsolete mixed palette in `dot-configs/themes/apollo/`.
- `apollo-theme/apollo-theme` (this repository) holds every application integration.
- [`apollo-theme/apollo-theme.github.io`](https://github.com/apollo-theme/apollo-theme.github.io) is the preview site at https://apollo-theme.github.io/ and owns all generated app preview SVGs. It is a peer repository, not part of this checkout, and is pinned to the revisions it renders by its own `SOURCE.json`.

`palette/apollo.json` and `palette/apollo-light.json` here are a pinned copy of apollo-palette, not the source of truth. `palette/SOURCE.json` records the apollo-palette repository, commit, and SHA-256 of both files; `scripts/check.py` fails if the bytes drift from the pin. Never hand-edit the root palette; change apollo-palette and sync.

The 17 app folders are listed in `APPS` in `scripts/common.py`: `sonicterm`, `windows-terminal`, `firefox`, `vscode`, `visual-studio`, `vim`, `nvim`, `xcode`, `tmux`, `rmux`, `powershell`, `bat`, `eza`, `wezterm`, `iterm2`, `apple-terminal`, `alacritty`. They are ordinary tracked folders (no submodules). Each folder stays standalone: its own `README.md`, `CLAUDE.md`, `LICENSE`, exact Dark and Light palette snapshots, generator, checker, and tests, so `cd <slug> && python3 scripts/generate.py --check` works without the root scripts. Native artifacts and app semantics belong to that folder. Existing `Apollo` / `apollo` names and unsuffixed files always mean the dark compatibility variant; light uses `Apollo Light` / `apollo-light`.

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza (`CLONE_APPS`) install from one shared clone at `~/.config/apollo-theme`, created by the idempotent line `[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"`. Copy and import apps take files from that clone, VS Code packages locally from it, and Firefox installs from `releases?q=firefox`. Keep app READMEs consistent with this model.

## Palette flow

A palette update moves outward in this order:

1. Change the palette in apollo-palette and wait for its CI to pass.
2. From this repository run `python3 scripts/sync_palette.py <path-to-apollo-palette> <ref>`. It copies both palettes into `palette/` and every app folder, rewrites `palette/SOURCE.json`, and regenerates every app.
3. Run the full gate (below) and commit the palette, pin, and regenerated artifacts together.
4. Publish site preview assets (update the site's `SOURCE.json` and regenerate there) before monorepo README changes that embed them, so every embedded preview URL is live.

Rollbacks are new commits; do not rewrite published history or move published tags.

## Releases

Each app is released independently with tags of the form `<slug>-vX.Y.Z` (`<slug>-v*`). Pushing a `firefox-v*` tag runs `.github/workflows/firefox-release.yml`, which validates and builds through `scripts/firefox_release.py` and publishes unsigned ZIPs as a GitHub release. `python3 scripts/firefox_release.py --dry-run firefox-vX.Y.Z` performs the same validation locally without publishing.

Every other `<slug>-v*` tag runs `.github/workflows/app-release.yml`: it runs that app's gate, then `scripts/app_release.py` builds the assets and the workflow publishes them as a GitHub release. Assets are the space-free raw files in `RAW_ASSETS` (a file is attached raw only when it imports as-is, so the Light themes for iTerm2, Xcode, bat, and eza ship only in the zip), `apollo-<slug>-<version>.zip` of the app folder without generators, tests, or palette snapshots, the VSIX for `vscode`, and `SHA256SUMS`. `python3 scripts/app_release.py --dry-run <slug>-vX.Y.Z --out <dir>` builds the same assets locally; CI runs `--check-all` on pull requests and `main`. The script refuses a non-empty output directory and fails unless the output holds exactly the expected assets. For `vscode` and `powershell` the tag version must match `package.json` / `ModuleVersion`.

## Commands

Generate all native artifacts, or fail if committed artifacts are stale:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
```

Limit generation to one app folder:

```sh
python3 scripts/generate.py --app vscode
python3 scripts/generate.py --check --app vscode
```

Run portable aggregate validation, one app gate, app-native checks, or the root tests:

```sh
python3 scripts/check.py
python3 scripts/check.py --app vscode
python3 scripts/check.py --native
python3 -m unittest discover -s tests -v
```

The full gate is:

```sh
python3 scripts/generate.py --check && python3 scripts/check.py && python3 -m unittest discover -s tests -v
```

Run a single root test:

```sh
python3 -m unittest tests.test_palette.PaletteTests.test_terminal_slots -v
```

Each app's `CLAUDE.md` documents its generation and validation commands, plus app-native smoke or packaging commands where that ecosystem has them. Run those commands inside the folder when its artifact or mapping changes. The default root gate is portable: it verifies the folder layout, the palette pin, palette identity, exact app snapshots, README contracts, and generated-file drift. Add `--native` only on a machine with the relevant applications installed.

CI is `.github/workflows/ci.yml`: a `validate` job on three operating systems, a `smoke` job on macOS that installs the clone-based apps and runs `tests.test_smoke_install`, and one job per app that runs that folder's own checks.

`scripts/verify_migration.py` and `scripts/restore_releases.py` are one-time tools from consolidating the per-app repositories into this monorepo (verifying folder history and recreating releases under `<slug>-<tag>` tags). They are not part of the ordinary workflow.

## Canonical palette invariants

Dark compatibility variant:

- Canvas `#141617`, terminal surface/black `#1d2021`, selection `#3c3836`.
- Primary text `#cfbc97`, secondary/ANSI white `#d5c4a1`, inactive text `#928374`, bright white `#fbf1c7`.
- Accent/cursor/warning `#fabd2f`, danger `#fb4934`, success `#b8bb26`, information `#83a598`.
- `#665c54` is terminal bright black only. Its contrast on the dark canvas is below 4.5:1, so do not use it for normal or small text.
- Selection alpha is 0.5 where the target supports alpha; otherwise the adapter must choose and test a legible opaque mapping.

Light variant:

- Canvas `#f9f5d7`, surface `#fbf1c7`, hover `#f2e5bc`, opaque selection `#ebdbb2`.
- Primary `#3c3836`, secondary `#504945`, inactive/bright black `#665c54`, brightest text `#282828`.
- Accent/warning `#8a5200`, danger `#9d0006`, success `#6b6700`, information `#076678`, magenta `#8f3f71`, cyan `#356b4d`.
- Every normal or small text role must remain at least 4.5:1 on canvas, surface, and hover backgrounds. Inverse control/cursor roles are explicit; adapters must not infer them from appearance polarity.

ANSI and bright arrays are ordered terminal slots, not unordered color collections. The root validator checks both schemas, canonical slot order, contrast, exact child snapshots, and generated-output drift. App adapters may derive native values such as plist RGB components, but derivation must be deterministic and covered by a fixture or semantic assertion.

## Application boundaries

Do not edit user preferences as part of generation or tests. Native smoke tests use scratch configs, isolated servers, temporary extension installs, or manual import instructions. Syntax/package validation is not visual validation; report an app as visually unverified when it cannot run on the current platform.

The Firefox folder preserves history from `D0n9X1n/humble-apollo`. Its public Mozilla Add-ons identity already uses Gecko GUID `humble-apollo@d0n9x1n` (Apollo Light uses `apollo-light@d0n9x1n`); never change either GUID, because existing installations depend on them for upgrades. Repository and display names may change independently. Do not publish to AMO or any application marketplace as part of an ordinary repository release.

RMUX and tmux have separate folders by project decision even though their theme syntax is compatible. Keep both artifacts theme-only: no prefixes, keybindings, shell commands, or unrelated session behavior.

## Documentation and generated files

Root documentation describes the family, the folder map, and the palette flow; app installation details belong in each app's README. Generated Dark and Light native artifacts are committed so users can install them without Python, but edits go through apollo-palette or that app's generator. Existing unsuffixed dark artifacts are compatibility surfaces and must not be renamed. After generation, `git diff --exit-code` should be empty in check mode.
