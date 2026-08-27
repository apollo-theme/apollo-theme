# Apollo for Apple Terminal

Apollo is SonicTerm's high-contrast Gruvbox Dark Hard variant for macOS Terminal, built on a near-black canvas with bright terminal colors.

Repository: <https://github.com/apollo-theme/apple-terminal-apollo-theme>

## Install and activate

1. Download [`Apollo.terminal`](https://github.com/apollo-theme/apple-terminal-apollo-theme/raw/main/Apollo.terminal).
2. Double-click it, or in Terminal choose **Settings → Profiles → … → Import…**.
3. Select **Apollo** in **Settings → Profiles** and click **Default** if new windows should use it.
4. Existing windows are unchanged; open a new window to inspect the profile.

The import adds a theme profile only. It does not set a shell command or modify the currently selected profile.

## Visual inspection

Open a new Apollo window and check normal, bold, selected, and cursor text plus ANSI colors 0–15. Foreground should be `#cfbc97`, the cursor `#fabd2f`, and the canvas `#141617`; selected text must remain readable. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Uninstall

Open **Terminal → Settings → Profiles**, select **Apollo**, and click the minus button. Choose another default profile first if Apollo is the default. Removing it does not change open windows.

## Development

The committed profile is generated from `palette/apollo.json` using deterministic, standard-library `plistlib` NSKeyedArchiver color data.

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.TerminalThemeTests.test_archived_colors_match_palette -v
```

## License

MIT. See [LICENSE](LICENSE).
