<h1 align="center">Vim Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light colorschemes to Vim with broad native highlighting, exact terminal colors, and truecolor or xterm-256 support.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-vim"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/vim-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/vim-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/vim-apollo-theme/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/vim-apollo-theme?style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-8ec07c?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://www.vim.org/"><img alt="Target: Vim" src="https://img.shields.io/badge/target-Vim-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-vim"><img alt="Simulated preview of Apollo in Vim" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vim.svg" width="960"></a>
  <a href="https://apollo-theme.github.io/#app-vim-light"><img alt="Simulated preview of Apollo Light in Vim" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vim-light.svg" width="960"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Font, terminal, and syntax rendering may vary; Apollo supplies both GUI colors and xterm-256 fallbacks.</sub></p>

The public **Apollo Dark** variant uses the existing `apollo` colorscheme and unsuffixed compatibility identity; **Apollo Light** uses the existing `apollo-light` colorscheme.

## Highlights

- Native Vim UI, syntax, diff, and diagnostic highlighting.
- Exact canonical normal and bright terminal ANSI colors.
- Truecolor presentation with deterministic xterm-256 fallbacks.
- Standalone generated `colors/apollo.vim` and `colors/apollo-light.vim` files with no runtime dependencies.

## Install

### vim-plug

Add this to your `.vimrc`, run `:PlugInstall`, and restart Vim:

```vim
call plug#begin()
Plug 'https://github.com/apollo-theme/vim-apollo-theme'
call plug#end()
```

### Manual package

```sh
git clone --depth 1 https://github.com/apollo-theme/vim-apollo-theme \
  ~/.vim/pack/apollo/start/vim-apollo-theme
```

## Activate

Add this to `.vimrc`:

```vim
if has('termguicolors')
  set termguicolors
endif
colorscheme apollo
```

Use `colorscheme apollo-light` for the light variant. Without `termguicolors`, each variant uses its independently selected hue-preserving 256-color fallbacks.

## Visual verification

Open a syntax-rich buffer in both variants. Apollo should use `#cfbc97` on `#141617`; Apollo Light should use `#3c3836` on `#f9f5d7`. Confirm active/search cues, comments, diffs, and diagnostics remain distinguishable in truecolor and 256-color modes. To verify the colorscheme loads cleanly with both GUI and 256-color highlight assertions, run:

```sh
vim -Nu NONE -n -es -i NONE -S tests/headless.vim
```

## Uninstall

For vim-plug, remove the `Plug` line, restart Vim, and run `:PlugClean`. For the manual package:

```sh
rm -rf ~/.vim/pack/apollo/start/vim-apollo-theme
```

Then remove `colorscheme apollo` or `colorscheme apollo-light` from `.vimrc`.

## Develop and validate

Both files under `palette/` are exact canonical snapshots. Both files under `colors/` are deterministic generated outputs and must not be edited directly. Build and run the full validation set from the repository root:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 -m compileall -q scripts tests
python3 scripts/check.py
```

Run the focused Python and clean editor checks with:

```sh
python3 -m unittest tests.test_theme.ThemeTests.test_generated_theme_is_current
vim -Nu NONE -n -es -i NONE -S tests/headless.vim
```

Only Python's standard library is used by the build and check scripts.

## License

[MIT](LICENSE).
