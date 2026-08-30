<h1 align="center">tmux Apollo Theme</h1>

<p align="center">A standalone, theme-only tmux configuration built with the canonical Apollo palette.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-tmux"><img alt="Preview" src="https://img.shields.io/badge/Preview-Website-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/tmux-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/tmux-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/tmux-apollo-theme/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/tmux-apollo-theme?sort=semver&amp;style=flat-square&amp;label=Release&amp;labelColor=141617&amp;color=b8bb26"></a>
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

Repository: <https://github.com/apollo-theme/tmux-apollo-theme>

## Install

Clone without modifying your tmux configuration:

```sh
git clone https://github.com/apollo-theme/tmux-apollo-theme "$HOME/.config/tmux-apollo-theme"
```

## Activate

Apply exactly one variant to the running server:

```sh
# Dark (default)
tmux source-file "$HOME/.config/tmux-apollo-theme/apollo.tmux"

# Light
tmux source-file "$HOME/.config/tmux-apollo-theme/apollo-light.tmux"
```

For future servers, manually add one corresponding `source-file` line to your tmux configuration. Do not source both variants; the last one would simply replace the same theme options. tmux controls status, pane-border, message, and mode chrome but cannot change the terminal canvas behind pane content, so pair Apollo Light with a light terminal profile.

No installer edits your configuration.

## Uninstall

Remove the `source-file` line, then remove the cloned directory:

```sh
rm -rf "$HOME/.config/tmux-apollo-theme"
```

A running server keeps its current option values; reload your usual theme/configuration, or restart tmux after your sessions have ended.

## Visual check

Open or attach to a tmux session, then source and query Apollo Dark before Apollo Light:

```sh
# Apollo Dark
tmux source-file "$HOME/.config/tmux-apollo-theme/apollo.tmux"
tmux show-options -gv status-style
# bg=#141617,fg=#cfbc97

# Apollo Light
tmux source-file "$HOME/.config/tmux-apollo-theme/apollo-light.tmux"
tmux show-options -gv status-style
# bg=#f9f5d7,fg=#3c3836
```

For Apollo Dark, the status canvas should be near-black with warm primary text. For Apollo Light, it should use a warm light canvas with dark text. In both variants, the active window, pane borders, messages, and alerts should remain distinct.

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
