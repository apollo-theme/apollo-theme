# Apollo Dark and Light Documentation Plan

## Constraints

- Work locally only; do not commit, push, tag, release, deploy, sign, or edit remote repository content.
- Preserve canonical palettes, generated native artifacts, package names, selectors, Firefox display names and GUIDs, dependencies, `.gitmodules`, and all repository HEADs.
- Keep unsuffixed `Apollo` / `apollo` as the native dark compatibility identity while using **Apollo Dark** as its public appearance label.
- Edit Pages generated files only through `apollo-theme.github.io/scripts/generate.py`.
- Keep the private `demo-repository` outside the parent and its submodule inventory.

## Task 1 — Record immutable baselines

- Record the parent HEAD, all 19 submodule HEADs, `.gitmodules`, canonical palette checksums, and clean status.
- Confirm the sibling private-demo destination does not already exist.
- Use the baselines in the final boundary audit; do not reset or discard user work if state changes unexpectedly.

## Task 2 — Strengthen the parent documentation contract first

Files: `scripts/check.py`, `tests/test_palette.py`

1. Add failing tests showing that image alt text, badges, comments, hidden HTML, code blocks, inline code, and filename-only occurrences cannot satisfy visible appearance naming.
2. Preserve visible Markdown link labels in `visible_prose()`.
3. Make `check_readme_contract()` accept injected README text for mutation tests while retaining all current branding checks.
4. Require visible **Apollo Dark** and **Apollo Light** in every child README.
5. Add parent/management tests requiring both names, compatibility wording, paired SonicTerm previews, the Pages live-catalog link, all 17 profile integrations, and no stale rollout/pending text.
6. Verify the extractor test passes while repository-wide tests remain red until the documentation tasks land.

## Tasks 3–19 — Add standalone child contracts and documentation

Each child owner edits only that repository’s `README.md`, `scripts/check.py`, and existing Python README test module (or the primary test module where none exists).

For every child:

1. Add a failing test for a local `validate_readme_contract(text)` seam.
2. Require both exact names in visible prose.
3. Require exact native dark and light install/activation markers, not generic words.
4. Mutation-test removal of each name and each marker independently.
5. Add a concise visible sentence explaining that Apollo Dark retains the existing unsuffixed/native `Apollo` identity and Apollo Light uses its current explicit light identity.
6. Leave commands, paths, selectors, packages, manifests, GUIDs, and generated artifacts unchanged.
7. Run its generator drift check, checker, full tests, and `git diff --check`.

| Repository | Exact dark marker | Exact light marker |
| --- | --- | --- |
| Alacritty | `import = ["~/.config/alacritty/themes/apollo.toml"]` | `import = ["~/.config/alacritty/themes/apollo-light.toml"]` |
| Apple Terminal | `Apollo.terminal` | `Apollo Light.terminal` |
| iTerm2 | `Apollo.itermcolors` | `Apollo Light.itermcolors` |
| SonicTerm | `theme = "apollo"` | `theme = "apollo-light"` |
| WezTerm | `config.color_scheme = 'Apollo'` | `config.color_scheme = 'Apollo Light'` |
| Windows Terminal | `"colorScheme": "Apollo"` | `"colorScheme": "Apollo Light"` |
| Neovim | `vim.cmd.colorscheme('apollo')` | `vim.cmd.colorscheme('apollo-light')` |
| Vim | `colorscheme apollo` | `colorscheme apollo-light` |
| Visual Studio | `themes/Apollo.vstheme` | `themes/Apollo Light.vstheme` |
| VS Code | native selector `**Apollo**` | native selector `**Apollo Light**` |
| Xcode | `Apollo.xccolortheme` | `Apollo Light.xccolortheme` |
| bat | complete `BAT_THEME=Apollo bat path/to/file` command | complete `BAT_THEME='Apollo Light' bat path/to/file` command |
| eza | complete root `EZA_CONFIG_DIR` command | complete `/light` `EZA_CONFIG_DIR` command |
| PowerShell | `Enable-ApolloTheme -Variant Dark` | `Enable-ApolloTheme -Variant Light` |
| tmux | complete unsuffixed `tmux source-file` command and dark status output | complete light `tmux source-file` command and light status output |
| RMUX | complete unsuffixed `rmux source-file` command and dark status output | complete light `rmux source-file` command and light status output |
| Firefox | `npm run dev:dark`, root signing source | `npm run dev:light`, `--source-dir variants/light` |

Additional child requirements:

- tmux and RMUX visual-check instructions source/query both appearances and show dark `bg=#141617,fg=#cfbc97` and light `bg=#f9f5d7,fg=#3c3836` expectations.
- PowerShell documents explicit `-Variant Dark` while retaining the unsuffixed command as the dark default.
- Firefox maps official **Apollo Theme** / fixed dark GUID to Apollo Dark and **Apollo Light Theme** / fixed light GUID to Apollo Light.
- Firefox gets separate `### Apollo Dark signing` and `### Apollo Light signing` examples. The dark command uses the root source and its complete ignore list; the light command uses `--source-dir variants/light`. Neither command is executed.
- Firefox tests require the existing exact disclaimers: the latest GitHub Release does not imply AMO publication, and the repository makes no claim that either current theme version is available from the marketplace. A negative mutation replaces those disclaimers with `Both themes are available from the marketplace.` and must fail validation. This replaces the rejected substring-only assertion.

## Tasks 20–22 — Update the Pages source under TDD

Files: `apollo-theme.github.io/README.md`, `scripts/generate.py`, `scripts/check.py`, `tests/test_site.py`, generated `index.html`, generated `previews/*.svg`

1. Change tests first to require 17 visible Apollo Dark labels and 17 Apollo Light labels.
2. Replace the test that freezes dark preview bytes to `HEAD` with compatibility invariants: stable filenames/anchors, canonical palette colors, and representative native dark `Apollo` / `apollo` examples.
3. Add checker/tests for appearance-specific alt text, SVG titles/descriptions/stamps, exact 17-app/34-SVG inventory, paired README previews, direct `#ports` link, and stale-copy rejection.
4. In the generator, separate public appearance names/stamps from native names. Descriptive headings, captions, metadata, alt/ARIA text, palette headings, and SVG titles/stamps use Apollo Dark/Apollo Light; simulated native controls and commands retain `Apollo`/`apollo` for dark.
5. Replace Firefox’s “one night palette” tagline with paired neutral wording.
6. Replace RMUX `Viewport pass pending` and asymmetric preview counts with `34 previews verified` and completed Dark/Light wording for both appearances.
7. Regenerate all owned output, then run Pages tests, drift check, complete checker, and `git diff --check`.
8. Update the Pages README with paired SonicTerm previews, compatibility wording, and the live catalog link.

## Tasks 23–24 — Align parent and organization presentation

- Root `README.md`: show paired SonicTerm previews, use descriptive Apollo Dark/Apollo Light palette labels, explain the unsuffixed compatibility identity, and preserve all 17 integrations.
- `.github/organization/profile/README.md`: retain paired previews and all 17 links; clarify that unsuffixed Apollo identities are Apollo Dark compatibility identities. Change no other profile-repository file.
- Run focused parent surface tests before the aggregate gate.

## Tasks 25–26 — Prepare the private demo locally

1. Clone `apollo-theme/demo-repository` into `/Users/d0n9x1n/Workspace/fun-code/demo-repository`; record its HEAD and verify it remains absent from `.gitmodules`.
2. Edit only `README.md`, `index.html`, and `.github/workflows/proof-html.yml`.
3. Replace generic starter copy with a small theme-aware page and README that visibly name both appearances, explain the compatibility identity, and link `https://apollo-theme.github.io/#ports`.
4. Preserve `package.json`, `@primer/css` version, `auto-assign.yml`, and the existing `anishathalye/proof-html@v1.1.0` step.
5. Add checkout plus fixed-string Dark/Light assertions to the HTML workflow.
6. Run local copy checks and an exact changed-file allowlist; do not claim the unpushed GitHub Action passed.

## Task 27 — Static integration gates

- Run every child’s documented generator/check/test path. Include available native/package checks such as plist/XML linting, VS Code packaging, PowerShell tests, and Firefox check/test/lint/build.
- Run Pages generator check, tests, complete checker, and diff check.
- Run parent generator check, tests, complete checker, and diff check.
- Validate the private demo’s dependency/workflow preservation and changed-file allowlist.
- Treat unavailable native applications as visually/native unverified rather than as passing.

## Task 28 — Browser acceptance

- Start local HTTP servers for Pages and the private demo.
- Use a real browser at desktop and narrow-mobile widths under dark and light emulation.
- Verify 34 loaded Pages images, paired appearance labels, representative dark/light deep links, visible focus, theme response, no horizontal overflow, no console errors, and no failed runtime requests.
- Verify both names, public catalog link, theme response, focus, and no overflow on the private demo.
- Stop both servers afterward.

## Task 29 — Final local-only boundary audit

- Compare HEADs and protected checksums with Task 1.
- Review status/diffs in the parent, all 19 submodules, and private-demo checkout.
- Confirm only the approved documentation/check/test/generated Pages files changed.
- Confirm no native artifact, palette, identity, GUID, dependency, `.gitmodules`, gitlink, commit, tag, signing artifact, or remote state changed.
- Run per-task spec QA/code QA and a final Tech Lead review; record that the mandated Sonnet review is same-family and therefore the Feature-Crew cross-family gate remains unsatisfied.
