# Apollo Dark and Light Documentation Consistency

## Purpose

Make every Apollo repository and demo surface explicitly present **Apollo Dark** and **Apollo Light**, including how each appearance is installed or selected, while preserving all existing dark compatibility identities.

## Scope

- Parent repository documentation and validation.
- All 17 application submodule READMEs and their standalone checks.
- `apollo-theme.github.io` README, generated site, generated previews, checker, and tests.
- `.github/organization/profile/README.md` consistency.
- A separate local checkout of private `apollo-theme/demo-repository`, without adding it as a parent submodule.

## Naming contract

- **Apollo Dark** is the public appearance label.
- Existing unsuffixed `Apollo` / `apollo` files, selectors, package names, and activation paths remain the dark compatibility identity.
- **Apollo Light** / `apollo-light` remains the public and native light identity where supported.
- Documentation must explain this distinction in visible prose. Image alt text, badges, code blocks, filenames, or hidden markup alone do not satisfy the contract.
- Firefox keeps the official display names **Apollo Theme** and **Apollo Light Theme**, dark GUID `humble-apollo@d0n9x1n`, and light GUID `apollo-light@d0n9x1n`. Its documentation maps those identities to Apollo Dark and Apollo Light without renaming them.

## Required behavior

1. Every application README visibly names Apollo Dark and Apollo Light and gives accurate installation or activation guidance for both.
2. Existing commands and native identifiers remain valid; documentation changes must not rename artifacts or selectors.
3. The parent README and Pages README show paired Dark and Light previews and explain the compatibility naming rule. The Pages README links directly to the live catalog.
4. The organization profile continues to show both appearances, all 17 integrations, paired previews, and current wording.
5. The generated Pages catalog uses Apollo Dark and Apollo Light for descriptive headings, captions, metadata, alt text, SVG titles, and appearance stamps. Native examples inside simulations continue to use `Apollo` / `apollo` for dark.
6. Generated output preserves exactly 17 app sections, 34 SVGs, stable unsuffixed dark preview URLs, and existing app/deep-link anchors.
7. Firefox’s README documents separate permanent-signing invocations for the root dark manifest and `variants/light`, without claiming marketplace availability or performing signing.
8. tmux and RMUX visual-check instructions cover both appearances.
9. The Firefox “one night palette” line and RMUX `Viewport pass pending` / asymmetric 17-versus-34 preview text are replaced with accurate paired/completed wording.
10. The private demo repository receives local, uncommitted README/page copy naming both appearances and linking the public catalog. Its existing GitHub demonstration workflows and Primer dependency remain intact; its HTML workflow gains simple Dark/Light copy assertions.

## Validation contract

- The parent `scripts/check.py` rejects any child README whose visible prose lacks either exact appearance name.
- Parent tests cover all child READMEs and all parent/management README surfaces, including paired preview references and stale rollout wording.
- Each child’s own checker enforces its visible naming contract and app-specific dark/light install or activation markers so standalone clones do not depend on the parent. The markers must be exact native commands, filenames, selectors, or manifest paths used by that app—not generic occurrences of “dark” and “light.” Tests must demonstrate that removing either variant’s marker fails the contract.
- Pages checks require 17 Apollo Dark labels, 17 Apollo Light labels, exact inventory and anchors, accurate completed fixture wording, and preservation of native dark `Apollo` examples.
- Generated files are changed only through `apollo-theme.github.io/scripts/generate.py` and pass drift checks.
- All child checks/tests, Pages checks/tests, and parent aggregate checks/tests pass.
- The public Pages site and private demo page are exercised through local HTTP servers in a browser at desktop and narrow widths with both browser color schemes; paired content, deep links, focus, overflow, console, and network behavior are inspected.

## Non-goals

- No palette or native-theme color changes.
- No artifact, selector, package, repository, manifest display-name, or GUID renames.
- No new app integration, JavaScript framework, analytics, backend, or external runtime dependency.
- No AMO or marketplace action.
- No commit, push, tag, release, deployment, signing, or remote private-demo edit.
- Do not add the private demo repository to `.gitmodules` or the synchronized repository count.
