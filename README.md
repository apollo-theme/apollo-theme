# Apollo for WezTerm

Apollo is SonicTerm's high-contrast Gruvbox Dark Hard variant, with its near-black canvas and bright Base16 terminal colors. This repository is standalone; `palette/apollo.json` is the pinned source snapshot and `apollo.toml` is generated from it.

Repository: https://github.com/apollo-theme/wezterm-apollo-theme

## Install and activate

On Unix-like systems:

```sh
mkdir -p ~/.config/wezterm/colors
cp apollo.toml ~/.config/wezterm/colors/apollo.toml
```

On Windows, copy `apollo.toml` to the `colors` directory beside `wezterm.exe`. Then add this to `wezterm.lua` (the included `wezterm.lua` is a minimal example):

```lua
config.color_scheme = 'Apollo'
```

Reload the configuration or restart WezTerm.

## Uninstall

Select another `color_scheme`, reload, then remove the copied `apollo.toml`.

## Visual check

Print ANSI colors 0–15, move the cursor over text, and select differently colored cells. Confirm the `#141617` canvas, warm foreground, yellow cursor, a 50%-alpha grey-brown selection that preserves each cell's foreground, and the exact normal/bright arrays in `palette/apollo.json`. Automated checks validate the TOML and installed WezTerm can load it, but rendered pixels still require this manual check.

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
