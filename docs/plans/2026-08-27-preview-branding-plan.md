# Apollo Preview and Branding Implementation Plan

## Delivery order

Publish the website first, then the organization profile, then app READMEs, and the parent last. This prevents child READMEs from embedding preview URLs that do not yet exist.

## Task 1 — Website repository and visual system

Create public `apollo-theme/apollo-theme.github.io`, clone it at parent path `apollo-theme.github.io`, and implement:

- `.gitattributes`, `.gitignore`, `.nojekyll`, `LICENSE`, `CLAUDE.md`, `README.md`.
- `palette/apollo.json`, copied exactly from the parent.
- `index.html` with semantic landmarks and 17 permanent sections:
  `app-sonicterm`, `app-wezterm`, `app-iterm2`, `app-apple-terminal`, `app-alacritty`, `app-windows-terminal`, `app-firefox`, `app-vscode`, `app-visual-studio`, `app-vim`, `app-nvim`, `app-xcode`, `app-tmux`, `app-rmux`, `app-powershell`, `app-bat`, `app-eza`.
- `assets/site.css` and optional small `assets/site.js`; site remains complete without JS.
- `previews/<slug>.svg` for all 17 apps, generated deterministically from family-specific templates: terminal window, editor/IDE, Firefox chrome, multiplexer, shell prompt, and CLI output.
- `scripts/generate.py` owns the 17 SVGs from canonical colors and app metadata.
- `scripts/check.py` checks palette hash, exact IDs, SVG set, safe local/static links, forbidden external runtime dependencies, no-JS content, and text contrast.
- Unit tests and `.github/workflows/pages.yml`: test, upload static artifact, deploy Pages using pinned official action SHAs.

Design direction: Apollo night-flight console—one continuous dark instrument surface, crisp one-pixel rails, gold focus traces, dense but calm typography, and one memorable full-width “signal path” from palette through app simulations. Avoid generic rounded cards, gradients, and ornamental metrics. Every preview says `SIMULATED PREVIEW` visibly.

Validate locally with Python tests and a static HTTP server. Browser-test 1440, 768, and 320px; keyboard focus; deep links; reduced motion; JavaScript disabled; console errors; horizontal overflow.

Commit/push the website, enable GitHub Pages Actions deployment, wait for green workflow, and verify `https://apollo-theme.github.io/` plus every `#app-<slug>` anchor and raw SVG URL.

## Task 2 — Organization profile repository

Clone `apollo-theme/.github` at `.github/organization` without replacing `.github/workflows`.

- Delete `.github/organization/README.md`; keep `profile/README.md` as the repository's only file and rewrite it in place.
- Build a polished organization profile with Apollo-only headline, website preview, palette strip, categorized 17-app matrix, source/license links, and lineage thanks in a final credits section.
- Validate the single-file rule and live website links from the parent checker; do not add support files to the organization profile repository.
- Commit/push after the website is live.

Update the organization description to exactly `Yet, just another color theme.` and website to `https://apollo-theme.github.io/`.

## Task 3 — Shared README contract and validation

In the parent, add declarative app metadata to `scripts/common.py`: app display name, slug, family, workflow filename, platform badge, install anchor, description, and repository topics.

Extend `scripts/check.py` and tests to enforce for every app child:

- centered app-first title;
- one Apollo-only description;
- preview, CI, latest-release, MIT, and app/platform badges with correct workflow paths;
- linked raw SVG preview and website deep link;
- existing install/activate/uninstall/visual/development substance retained;
- no forbidden ancestry phrases (`Gruvbox`, `Base16`, `SonicTerm-modified`, `based on SonicTerm`, `derived from SonicTerm`); standalone `SonicTerm` allowed only as the app identity/path/command in its child;
- Firefox GUID/signing warnings and marketplace limitations remain intact.

Add management-submodule constants separate from the 17 app list. `check_submodules()` must require exactly 17 app submodules plus `apollo-theme.github.io` and `.github/organization`, all at canonical HTTPS URLs and clean recorded commits.

## Task 4 — README application groups

Run four parallel, non-overlapping implementation groups after website URLs are live:

1. Terminals: SonicTerm, WezTerm, iTerm2, Apple Terminal, Alacritty, Windows Terminal.
2. Editors: VS Code, Visual Studio, Vim, Neovim, Xcode.
3. Browser and multiplexers: Firefox, tmux, RMUX.
4. Shell/CLI: PowerShell, bat, eza.

Each group edits only child `README.md` and `CLAUDE.md`, preserving verified commands. Use a consistent top block:

- centered `<h1><App> Apollo Theme</h1>`;
- centered Apollo sentence;
- five or six linked shields with canonical `labelColor=141617` and Apollo role colors;
- linked `<img>` from `https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/<slug>.svg` to `https://apollo-theme.github.io/#app-<slug>`;
- visible “Simulated preview” caption.

No fabricated marketplace/install claims. Commit and push each child separately, run its existing native/portable checks, and wait for green CI.

## Task 5 — Repository metadata and topics

After child README commits are green, update every app repository:

- Description: `<App> Apollo Theme.` (PowerShell may add `PSReadLine`; Firefox must be `Firefox Apollo Theme.`).
- Homepage: `https://apollo-theme.github.io/#app-<slug>`.
- Topics: always `apollo-theme`, `color-theme`, the app slug/topic, and relevant ecosystem/platform topics; remove `gruvbox` from all child topics.

Update website, parent, and `.github` topics with their own management/site terms; lineage topics are permitted only there. Read back all 20 repositories to verify descriptions, homepages, topics, and default branches.

## Task 6 — Parent and release synchronization

Rewrite parent `README.md` with the shared visual language, root website CTA, palette/ANSI presentation, categorized integration table, clone instructions, and credits. Update `CLAUDE.md` with:

- 17 application submodules vs two management submodules;
- `.github/organization` collision rationale and single `profile/README.md` rule;
- website-first README dependency order;
- child-first commit/push ordering;
- preview/README validation commands and lineage policy.

Commit approved spec/plan and parent validation changes. Stage all 19 gitlinks only after their remote commits exist. Run:

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 scripts/check.py --native
python3 -m unittest discover -s tests -v
```

Run simulated Windows clone:

```sh
git -c core.autocrlf=true clone --recurse-submodules https://github.com/apollo-theme/apollo-theme.git
```

Run all documented portable checks in that clone. Commit/push the parent, wait for Linux/macOS/Windows CI, then publish parent `v0.2.0`. Child README-only updates do not create new app releases; website/profile may receive `v1.0.0` after deployment verification.

## QA gates

- Per-task spec QA and code QA in one-clue mode.
- Website visual QA via screenshots at 1440/768/320px and browser accessibility/console checks.
- Final tech-lead review covers website, profile, all 17 child diffs, metadata readback, parent diff, Pages deployment, release links, and clean worktrees.
- Same-family review limitation remains explicitly unsatisfied; automated and browser evidence must be included in the final report.

## Rollback

Child and management repositories roll back by new commits, never force-push. If website deployment fails, do not publish child README links. If any child CI fails, leave the parent pinned to its previous gitlink. If organization metadata is wrong, restore the recorded pre-change description/homepage/topics using ordinary API updates. Do not delete `demo-repository`, old releases, or marketplace listings.
