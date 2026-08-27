# Apollo for tmux

A standalone, theme-only tmux configuration generated from the bundled Apollo palette snapshot. It changes colors only: no prefix, key bindings, status content, commands, or shell behavior.

Repository: https://github.com/apollo-theme/tmux-apollo-theme

## Install

Clone without modifying your tmux configuration:

```sh
git clone https://github.com/apollo-theme/tmux-apollo-theme "$HOME/.config/tmux-apollo-theme"
```

## Activate

Apply it to the running server:

```sh
tmux source-file "$HOME/.config/tmux-apollo-theme/apollo.tmux"
```

For future servers, manually add this line to your tmux configuration:

```tmux
source-file ~/.config/tmux-apollo-theme/apollo.tmux
```

No installer edits your configuration.

## Uninstall

Remove the `source-file` line, then remove the cloned directory:

```sh
rm -rf "$HOME/.config/tmux-apollo-theme"
```

A running server keeps its current option values; reload your usual theme/configuration, or restart tmux after your sessions have ended.

## Visual check

Open or attach to a tmux session. The status canvas should be near-black with warm primary text, the active window should be blue, active pane borders and messages should be gold, and alerts should be red. Confirm the base status values with:

```sh
tmux show-options -gv status-style
# bg=#141617,fg=#cfbc97
```

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
