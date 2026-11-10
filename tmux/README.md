<h1 align="center">tmux Apollo Theme</h1>

<p align="center">A standalone, theme-only tmux configuration built with the canonical Apollo palette.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-tmux"><img alt="Preview" src="https://img.shields.io/badge/Preview-Website-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=tmux-v"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=tmux-v*&amp;sort=semver&amp;style=flat-square&amp;label=Release&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-b8bb26?style=flat-square&amp;labelColor=141617"></a>
  <a href="apollo.tmux"><img alt="Target tmux" src="https://img.shields.io/badge/Target-tmux-83a598?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-tmux"><img alt="tmux Apollo Dark simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/tmux.svg" width="900"></a>
  <a href="https://apollo-theme.github.io/#app-tmux-light"><img alt="tmux Apollo Light simulated preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/tmux-light.svg" width="900"></a>
</p>

<p align="center"><em>Simulated preview — terminal fonts and rendering can change the final appearance.</em></p>

## About

Apollo Dark preserves the existing unsuffixed `apollo.tmux` artifact and default selector for compatibility. Apollo Light is the explicit `apollo-light.tmux` companion. Each changes colors only: no prefix, key bindings, status content, commands, plugins, hooks, or shell behavior. Source exactly one variant at a time.

Source: <https://github.com/apollo-theme/apollo-theme/tree/main/tmux>

## Install

Clone the shared Apollo Theme checkout once; it is reused by every app that reads from `~/.config/apollo-theme`:

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

Then add Apollo Dark to your tmux configuration so future servers load it:

<!-- smoke:install -->
```sh
echo "source-file \"$HOME/.config/apollo-theme/tmux/apollo.tmux\"" >> "$HOME/.tmux.conf"
```

For Apollo Light, append `apollo-light.tmux` instead. Keep exactly one Apollo `source-file` line; the last one sourced would simply replace the same theme options.

## Activate

Apply exactly one variant to the running server:

```sh
# Apollo Dark (default)
tmux source-file "$HOME/.config/apollo-theme/tmux/apollo.tmux"

# Apollo Light
tmux source-file "$HOME/.config/apollo-theme/tmux/apollo-light.tmux"
```

tmux controls status, pane-border, message, and mode chrome but cannot change the terminal canvas behind pane content, so pair Apollo Light with a light terminal profile.

## Uninstall

Remove the Apollo `source-file` line from your tmux configuration (a backup is kept at `~/.tmux.conf.bak`):

<!-- smoke:uninstall -->
```sh
sed -i.bak '/apollo-theme\/tmux/d' "$HOME/.tmux.conf"
```

A running server keeps its current option values; reload your usual theme/configuration, or restart tmux after your sessions have ended.

## Remove the shared clone

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `rm -rf "$HOME/.config/apollo-theme"`.

## Visual check

Open or attach to a tmux session, then source and query Apollo Dark before Apollo Light:

```sh
# Apollo Dark
tmux source-file "$HOME/.config/apollo-theme/tmux/apollo.tmux"
tmux show-options -gv status-style
# bg=#141617,fg=#cfbc97

# Apollo Light
tmux source-file "$HOME/.config/apollo-theme/tmux/apollo-light.tmux"
tmux show-options -gv status-style
# bg=#f9f5d7,fg=#3c3836
```

For Apollo Dark, the status canvas should be near-black with warm primary text. For Apollo Light, it should use a warm light canvas with dark text. In both variants, the active window, pane borders, messages, and alerts should remain distinct.

## Development

From the `tmux/` folder of the monorepo:

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
