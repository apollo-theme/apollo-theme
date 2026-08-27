# Apollo for Alacritty

Apollo is SonicTerm's high-contrast Gruvbox Dark Hard variant, with its near-black canvas and bright Base16 terminal colors. This repository is standalone; `palette/apollo.json` is the pinned source snapshot and `apollo.toml` is generated from it.

Repository: https://github.com/apollo-theme/alacritty-apollo-theme

## Install and activate

```sh
mkdir -p ~/.config/alacritty/themes
cp apollo.toml ~/.config/alacritty/themes/apollo.toml
```

Import it from `~/.config/alacritty/alacritty.toml` using current Alacritty syntax:

```toml
[general]
import = ["~/.config/alacritty/themes/apollo.toml"]
```

Alacritty reloads the configuration automatically; restart if reload is disabled.

## Uninstall

Remove the Apollo entry from `[general].import`, then remove `~/.config/alacritty/themes/apollo.toml`.

## Visual check

Print ANSI colors 0–15, move the cursor over text, and select text. Confirm the `#141617` canvas, warm foreground, yellow cursor, preserved selected-text color, and the exact normal/bright palette in `palette/apollo.json`. Automated checks validate the importable fragment, not rendered pixels.

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
