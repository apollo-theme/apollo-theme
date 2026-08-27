# Apollo for SonicTerm

Apollo is SonicTerm's high-contrast Gruvbox Dark Hard variant, with its near-black canvas and bright Base16 terminal colors. This repository is standalone; `palette/apollo.json` is the pinned source snapshot and `apollo.toml` is generated from it.

Repository: https://github.com/apollo-theme/sonicterm-apollo-theme

## Install and activate

```sh
mkdir -p ~/.sonicterm/themes
cp apollo.toml ~/.sonicterm/themes/apollo.toml
```

Set the theme in `~/.sonicterm/sonicterm.toml`:

```toml
theme = "apollo"
```

Start SonicTerm, or run **Reload Config** in an existing session.

## Uninstall

Select another theme in `~/.sonicterm/sonicterm.toml`, reload, then remove `~/.sonicterm/themes/apollo.toml`.

## Visual check

Open tabs in active, inactive, and hover states, select text, and print ANSI colors 0–15. Confirm a `#141617` canvas, yellow cursor/active tab, muted inactive labels, grey-brown selection, and the exact normal/bright palette in `palette/apollo.json`. Automated checks validate files and values, not rendered pixels.

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```
