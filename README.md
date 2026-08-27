# Apollo Theme

Apollo is a higher-contrast take on Gruvbox Dark Hard: a near-black `#141617` canvas, warm text, a yellow focus accent, and the bright Base16 terminal palette used by SonicTerm.

This repository is the source of truth and synchronized catalog. Each application directory is a Git submodule backed by its own public, independently installable repository in the [`apollo-theme`](https://github.com/apollo-theme) organization.

## Palette

| Role | Color |
| --- | --- |
| Canvas | `#141617` |
| Raised surface | `#1d2021` |
| Primary text | `#cfbc97` |
| Secondary text | `#d5c4a1` |
| Inactive text | `#928374` |
| Focus and cursor | `#fabd2f` |
| Selection | `#3c3836` |
| Error | `#fb4934` |
| Success | `#b8bb26` |
| Information | `#83a598` |

The canonical data is [`palette/apollo.json`](palette/apollo.json). It records the exact SonicTerm source revision and terminal color order. See [`NOTICE`](NOTICE) for Gruvbox and SonicTerm lineage. This project is not based on the unrelated 46-color pixel-art palette also named Apollo.

## Applications

| Application | Repository | Artifact |
| --- | --- | --- |
| SonicTerm | [`sonicterm-apollo-theme`](sonicterm-apollo-theme) | TOML theme |
| WezTerm | [`wezterm-apollo-theme`](wezterm-apollo-theme) | TOML color scheme |
| iTerm2 | [`iterm2-apollo-theme`](iterm2-apollo-theme) | `.itermcolors` |
| Apple Terminal | [`apple-terminal-apollo-theme`](apple-terminal-apollo-theme) | `.terminal` profile |
| Alacritty | [`alacritty-apollo-theme`](alacritty-apollo-theme) | TOML import |
| Windows Terminal | [`windows-terminal-apollo-theme`](windows-terminal-apollo-theme) | JSON scheme |
| Firefox | [`firefox-apollo-theme`](firefox-apollo-theme) | Firefox theme extension |
| Visual Studio Code | [`vscode-apollo-theme`](vscode-apollo-theme) | VSIX extension |
| Visual Studio | [`visual-studio-apollo-theme`](visual-studio-apollo-theme) | `.vstheme` |
| Vim | [`vim-apollo-theme`](vim-apollo-theme) | Vim colorscheme |
| Neovim | [`nvim-apollo-theme`](nvim-apollo-theme) | Lua colorscheme plugin |
| Xcode | [`xcode-apollo-theme`](xcode-apollo-theme) | `.xccolortheme` |
| tmux | [`tmux-apollo-theme`](tmux-apollo-theme) | sourceable tmux theme |
| RMUX | [`rmux-apollo-theme`](rmux-apollo-theme) | sourceable RMUX theme |
| PowerShell | [`powershell-apollo-theme`](powershell-apollo-theme) | PowerShell module |
| bat | [`bat-apollo-theme`](bat-apollo-theme) | `.tmTheme` |
| eza | [`eza-apollo-theme`](eza-apollo-theme) | YAML theme |

Each child README contains application-specific installation and removal instructions.

## Clone and validate

```sh
git clone --recurse-submodules https://github.com/apollo-theme/apollo-theme.git
cd apollo-theme
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

To refresh an existing checkout:

```sh
git pull --ff-only
git submodule update --init --recursive
```

## License

MIT
