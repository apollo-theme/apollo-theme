<h1 align="center">Neovim Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light colorschemes to Neovim with native UI, syntax, diagnostic, LSP, Tree-sitter, and terminal coverage.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-nvim"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/nvim-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/nvim-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/nvim-apollo-theme/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/nvim-apollo-theme?style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-8ec07c?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://neovim.io/"><img alt="Target: Neovim" src="https://img.shields.io/badge/target-Neovim-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-nvim"><img alt="Simulated preview of Apollo in Neovim" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/nvim.svg" width="960"></a>
  <a href="https://apollo-theme.github.io/#app-nvim-light"><img alt="Simulated preview of Apollo Light in Neovim" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/nvim-light.svg" width="960"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Font, terminal, and syntax rendering may vary; Apollo remains native and plugin-neutral.</sub></p>

The public **Apollo Dark** variant uses the existing `apollo` colorscheme and unsuffixed compatibility identity; **Apollo Light** uses the existing `apollo-light` colorscheme.

## Highlights

- Core Neovim UI, syntax, diff, diagnostic, and LSP highlighting.
- Neovim 0.12 Tree-sitter captures and exact terminal ANSI colors.
- Generated Lua entry point, palette data, and implementation with no runtime dependencies.
- Plugin-neutral scope: Apollo does not depend on or style third-party plugins.

## Install

### lazy.nvim

Add this plugin spec and run `:Lazy sync`:

```lua
{
  'https://github.com/apollo-theme/nvim-apollo-theme',
  lazy = false,
  priority = 1000,
  config = function()
    vim.cmd.colorscheme('apollo')
  end,
}
```

### Manual package

```sh
git clone --depth 1 https://github.com/apollo-theme/nvim-apollo-theme \
  ~/.local/share/nvim/site/pack/apollo/start/nvim-apollo-theme
```

## Activate

If your plugin manager does not activate the theme, add this to `init.lua`:

```lua
vim.cmd.colorscheme('apollo')
```

Use `vim.cmd.colorscheme('apollo-light')` for the light variant. `require('apollo').load()` remains the dark default.

## Visual verification

Open a syntax-rich buffer in both variants. Apollo should use `#cfbc97` on `#141617`; Apollo Light should use `#3c3836` on `#f9f5d7`. Confirm active/search cues, comments, diagnostics, diff states, and Tree-sitter captures remain distinct. To verify the colorscheme loads cleanly with representative highlights and terminal colors, run:

```sh
nvim --headless --clean -u NONE -l tests/headless.lua
```

## Uninstall

For lazy.nvim, remove the plugin spec and run `:Lazy clean`. For the manual package:

```sh
rm -rf ~/.local/share/nvim/site/pack/apollo/start/nvim-apollo-theme
```

Then remove the `apollo` or `apollo-light` colorscheme call from your configuration.

## Develop and validate

Both files under `palette/` are exact canonical snapshots. All shipped Lua files are deterministic generated output and must not be edited directly. Build and run the full validation set from the repository root:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 -m compileall -q scripts tests
python3 scripts/check.py
```

Run the focused Python and clean editor checks with:

```sh
python3 -m unittest tests.test_theme.ThemeTests.test_generated_theme_is_current
nvim --headless --clean -u NONE -l tests/headless.lua
```

Only Python's standard library is used by the build and check scripts.

## License

[MIT](LICENSE).
