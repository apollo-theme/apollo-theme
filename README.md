# Apollo for iTerm2

Apollo is SonicTerm's high-contrast Gruvbox Dark Hard variant for iTerm2, built on a near-black canvas with bright terminal colors.

Repository: <https://github.com/apollo-theme/iterm2-apollo-theme>

## Install and activate

1. Download [`Apollo.itermcolors`](https://github.com/apollo-theme/iterm2-apollo-theme/raw/main/Apollo.itermcolors).
2. In iTerm2, open **Settings → Profiles → Colors**.
3. Open **Color Presets… → Import…** and choose `Apollo.itermcolors`.
4. Open **Color Presets…** again and select **Apollo**.

## Visual inspection

Open a fresh profile and check normal, bold, selected, and cursor text plus ANSI colors 0–15. Foreground should be `#cfbc97`, the cursor `#fabd2f`, and the canvas `#141617`; selected text must remain readable. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Uninstall

In **Settings → Profiles → Colors → Color Presets…**, choose **Delete Preset…**, select **Apollo**, and confirm. Existing profiles retain their current colors until changed.

## Development

The committed theme is generated from `palette/apollo.json` using only Python's standard library.

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.ItermThemeTests.test_required_color_roles -v
```

## License

MIT. See [LICENSE](LICENSE).
