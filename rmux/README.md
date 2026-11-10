<h1 align="center">RMUX Apollo Theme</h1>

<p align="center">A standalone, theme-only RMUX configuration built with the canonical Apollo palette.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-rmux"><img alt="Preview" src="https://img.shields.io/badge/Preview-Website-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=rmux-v"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=rmux-v&amp;sort=semver&amp;style=flat-square&amp;label=Release&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-b8bb26?style=flat-square&amp;labelColor=141617"></a>
  <a href="apollo-rmux.conf"><img alt="Target RMUX" src="https://img.shields.io/badge/Target-RMUX-83a598?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-rmux"><img alt="RMUX Apollo Dark simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux.svg" width="900"></a>
  <a href="https://apollo-theme.github.io/#app-rmux-light"><img alt="RMUX Apollo Light simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux-light.svg" width="900"></a>
</p>

<p align="center"><em>Simulated preview — terminal fonts and rendering can change the final appearance.</em></p>

## About

RMUX keeps its own `rmux/` folder, separate from the tmux theme. Apollo Dark preserves the existing unsuffixed `apollo-rmux.conf` artifact and default selector for compatibility. Apollo Light is the explicit `apollo-rmux-light.conf` companion. Both contain only RMUX/tmux-compatible color options; neither copies status content, key bindings, prefixes, commands, hooks, or unrelated RMUX configuration. Source exactly one variant at a time.

Source: <https://github.com/apollo-theme/apollo-theme/tree/main/rmux>

## Install

Clone the shared Apollo Theme checkout once; it is reused by every app that reads from `~/.config/apollo-theme`:

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

Then add Apollo Dark to your RMUX configuration (`~/.rmux.conf`) so future daemons load it:

<!-- smoke:install -->
```sh
echo "source-file \"$HOME/.config/apollo-theme/rmux/apollo-rmux.conf\"" >> "$HOME/.rmux.conf"
```

For Apollo Light, append `apollo-rmux-light.conf` instead. Keep exactly one Apollo `source-file` line; the last one sourced would replace the same theme options.

## Activate

Apply exactly one variant to the running RMUX daemon:

```sh
# Apollo Dark (default)
rmux source-file "$HOME/.config/apollo-theme/rmux/apollo-rmux.conf"

# Apollo Light
rmux source-file "$HOME/.config/apollo-theme/rmux/apollo-rmux-light.conf"
```

RMUX controls its status, pane-border, message, and mode chrome but cannot change the terminal canvas behind pane content, so pair Apollo Light with a light terminal profile.

## Uninstall

Remove the Apollo `source-file` line from your RMUX configuration (a backup is kept at `~/.rmux.conf.bak`):

<!-- smoke:uninstall -->
```sh
sed -i.bak '/apollo-theme\/rmux/d' "$HOME/.rmux.conf"
```

A running daemon keeps its current option values; reload your normal theme/configuration or restart RMUX when safe.

## Remove the shared clone

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `rm -rf "$HOME/.config/apollo-theme"`.

## Visual check

Attach to RMUX, then source and query Apollo Dark before Apollo Light:

```sh
# Apollo Dark
rmux source-file "$HOME/.config/apollo-theme/rmux/apollo-rmux.conf"
rmux show-options -gv status-style
# bg=#141617,fg=#cfbc97

# Apollo Light
rmux source-file "$HOME/.config/apollo-theme/rmux/apollo-rmux-light.conf"
rmux show-options -gv status-style
# bg=#f9f5d7,fg=#3c3836
```

For Apollo Dark, the status canvas should be near-black with warm text. For Apollo Light, it should use a warm light canvas with dark text. In both variants, the active window, pane borders, messages, and alerts should remain distinct.

## Development

From the `rmux/` folder of the monorepo. The checker prefers installed `rmux` and otherwise validates the source in an isolated compatible tmux server.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
