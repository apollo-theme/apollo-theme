# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project shape

This is the synchronized parent for the Apollo Theme family. `palette/apollo.json` is the original dark source of truth derived from SonicTerm's higher-contrast Gruvbox Dark Hard variant. `palette/apollo-light.json` is the accessibility-hardened Gruvbox Light Hard source of truth. Both record their upstream path, commit, and checksum. Do not substitute the unrelated 46-color palette also named Apollo or the obsolete mixed palette in `dot-configs/themes/apollo/`.

Every `*-apollo-theme/` directory is an independent public application repository represented here as a direct Git submodule. A child must remain cloneable, understandable, generatable, and testable without the parent checkout. Its committed dark and light palette files are exact snapshots of the parent palettes, while native artifacts and app semantics belong to that child. Existing `Apollo` / `apollo` names and unsuffixed files always mean the dark compatibility variant; light uses `Apollo Light` / `apollo-light`.

Two additional management repositories are submodules but are not application integrations:

- `apollo-theme.github.io/` is the organization-root GitHub Pages site and owns all generated app preview SVGs.
- `.github/organization/` is `apollo-theme/.github`. It lives below the parent `.github/` directory because `.github/workflows/` must remain owned by this parent repository. The organization repository contains exactly one file: `profile/README.md`.

Publish the website before README changes so every embedded preview URL is live. Then publish the organization profile and application children, update repository metadata/topics, and commit the parent gitlinks last.

A palette update moves outward in this order:

1. Update the relevant root palette and its tests without changing the other variant.
2. Regenerate and validate both variants in every child.
3. Publish website preview assets before README changes that embed them.
4. Commit and push each child repository and wait for CI.
5. Commit the resulting child and management gitlinks in the parent and push the parent last.

Never publish a parent gitlink that points to an unpushed child commit. Rollbacks use new child commits followed by a new parent gitlink commit; do not rewrite published history.

## Commands

Initialize or refresh all application repositories:

```sh
git submodule update --init --recursive
```

Generate all native artifacts, or fail if committed artifacts are stale:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
```

Limit generation to one child:

```sh
python3 scripts/generate.py --repo vscode-apollo-theme
python3 scripts/generate.py --check --repo vscode-apollo-theme
```

Run portable aggregate validation, one child gate, app-native checks, or the parent tests:

```sh
python3 scripts/check.py
python3 scripts/check.py --repo vscode-apollo-theme
python3 scripts/check.py --native
python3 -m unittest discover -s tests -v
```

Run a single parent test:

```sh
python3 -m unittest tests.test_palette.PaletteTests.test_terminal_slots -v
```

Each child `CLAUDE.md` documents its generation and validation commands, plus app-native smoke or packaging commands where that ecosystem has them. Run those commands inside the child when its artifact or mapping changes. The default root gate is portable: it verifies submodules, palette identity, and generated-file drift. Add `--native` only on a machine with the relevant applications installed; child CI owns the authoritative native checks.

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

The Firefox child preserves history from `D0n9X1n/humble-apollo`. Its public Mozilla Add-ons identity already uses Gecko GUID `humble-apollo@d0n9x1n`; never change that GUID, because existing installations depend on it for upgrades. Repository and display names may change independently. Do not publish to AMO or any application marketplace as part of an ordinary repository release.

RMUX and tmux have separate repositories by project decision even though their theme syntax is compatible. Keep both artifacts theme-only: no prefixes, keybindings, shell commands, or unrelated session behavior.

## Documentation and generated files

Root documentation describes the family and synchronization model; app installation details belong in child READMEs. Generated Dark and Light native artifacts are committed so users can install them without Python, but edits go through a canonical palette or that child's generator. Existing unsuffixed dark artifacts are compatibility surfaces and must not be renamed. After generation, `git diff --exit-code` should be empty in check mode.
