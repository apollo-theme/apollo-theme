# Apollo Light Design

## Purpose

Add a complete high-contrast light appearance across Apollo's 17 integrations without changing any existing dark install, selector, generated artifact, or Firefox upgrade identity.

## Compatibility

- `palette/apollo.json`, `Apollo`, `apollo`, and every unsuffixed native artifact remain the dark compatibility identity.
- Light uses `palette/apollo-light.json`, `Apollo Light`, `apollo-light`, and suffixed native artifacts.
- The application repository count remains 17. Firefox Light is a second package in the existing Firefox repository, with a distinct Gecko GUID.

## Palette

Apollo Light is pinned to Gruvbox Light Hard at commit `5d15b2765f59754d7ac263c88a0f6e3e58124951`, source SHA-256 `55116926ba2b625837d9ae89349a5688d60d0b32acdbd8887e1c0d225f079c3d`.

| Role | Color |
| --- | --- |
| Canvas | `#f9f5d7` |
| Surface | `#fbf1c7` |
| Hover | `#f2e5bc` |
| Selection | `#ebdbb2` |
| Primary | `#3c3836` |
| Secondary | `#504945` |
| Inactive / bright black | `#665c54` |
| Bright text | `#282828` |
| Focus / warning | `#8a5200` |
| Danger | `#9d0006` |
| Success | `#6b6700` |
| Information | `#076678` |
| Magenta | `#8f3f71` |
| Cyan | `#356b4d` |

Every normal and small text role must meet WCAG AA on canvas, surface, and hover backgrounds. Selected text, cursor text, and text on semantic fills are separate tested pairs. Light selection is opaque because a 50% overlay is too subtle on the paper canvas.

## Native behavior

Every app repository carries exact dark and light snapshots and generates both variants by default. Existing dark files remain unchanged. Firefox preserves `humble-apollo@d0n9x1n`; Light uses `apollo-light@d0n9x1n` and a separate package. PowerShell defaults to Dark when no variant is supplied and restores the true pre-Apollo colors after any variant-switch sequence.

No generator, test, or installer edits user preferences. Automatic appearance switching is optional user configuration.

## Website

The website keeps every `#app-<slug>` and `previews/<slug>.svg` dark compatibility URL, adds `#app-<slug>-light` and `previews/<slug>-light.svg`, and shows both variants without JavaScript. The site shell may follow `prefers-color-scheme`, but neither preview may be hidden.

## Publication

Publish the website assets before child README embeds, then application children and releases, organization profile and metadata, and parent gitlinks last. Never publish a parent gitlink for an unpushed child commit. Do not publish to AMO or application marketplaces.
