<h1 align="center">Neovim Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light colorschemes to Neovim with native UI, syntax, diagnostic, LSP, Tree-sitter, and terminal coverage.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-nvim"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=nvim"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=nvim-v*&amp;style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
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

Apollo lives in the `nvim/` folder of [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme).

### lazy.nvim

Add this plugin spec and run `:Lazy sync`. lazy.nvim clones the repository into its own plugin directory, not `~/.config/apollo-theme`, so the shared clone below is not needed:

<!-- smoke:lazy -->
```lua
{ 'apollo-theme/apollo-theme', lazy = false, priority = 1000, config = function(plugin) vim.opt.rtp:append(plugin.dir .. "/nvim"); vim.cmd.colorscheme("apollo") end }
```

Replace `"apollo"` with `"apollo-light"` for Apollo Light.

### Manual

Clone the repository once into the shared location (this is a no-op when the clone already exists):

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

Then add the `nvim/` folder to the runtime path and select Apollo Dark in `init.lua`:

<!-- smoke:install -->
```sh
mkdir -p "$HOME/.config/nvim" && printf '%s\n' 'vim.opt.rtp:append(vim.env.HOME .. "/.config/apollo-theme/nvim")' 'vim.cmd.colorscheme("apollo")' >> "$HOME/.config/nvim/init.lua"
```

Update later with `git -C "$HOME/.config/apollo-theme" pull`.

## Activate

The install steps above select Apollo Dark. To switch variants elsewhere in `init.lua`, call:

```lua
vim.cmd.colorscheme('apollo')
```

Use `vim.cmd.colorscheme('apollo-light')` for Apollo Light. `require('apollo').load()` remains the dark default.

## Visual verification

Open a syntax-rich buffer in both variants. Apollo should use `#cfbc97` on `#141617`; Apollo Light should use `#3c3836` on `#f9f5d7`. Confirm active/search cues, comments, diagnostics, diff states, and Tree-sitter captures remain distinct. To verify the colorscheme loads cleanly with representative highlights and terminal colors, run:

```sh
cd "$HOME/.config/apollo-theme/nvim"
nvim --headless --clean -u NONE -l tests/headless.lua
```

## Uninstall

For lazy.nvim, remove the plugin spec and run `:Lazy clean`. For the manual install, remove the activation lines from `init.lua` (a backup is kept as `init.lua.bak`):

<!-- smoke:uninstall -->
```sh
sed -i.bak '/apollo-theme\/nvim/d;/colorscheme("apollo/d' "$HOME/.config/nvim/init.lua"
```

Remove any other `apollo` or `apollo-light` colorscheme call you added yourself.

## Remove the shared clone

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `rm -rf "$HOME/.config/apollo-theme"`.

## Develop and validate

Both files under `palette/` are exact canonical snapshots. All shipped Lua files are deterministic generated output and must not be edited directly. Build and run the full validation set from the `nvim/` folder of the monorepo:

```sh
cd nvim
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 -m compileall -q scripts tests
python3 -m unittest discover -s tests
python3 scripts/check.py
```

Run the focused Python and clean editor checks with:

```sh
python3 -m unittest tests.test_theme.ThemeTests.test_generated_theme_is_current
nvim --headless --clean -u NONE -l tests/headless.lua
```

Only Python's standard library is used by the build and check scripts. The root CI job `nvim` runs these checks on every change.

## License

[MIT](LICENSE).
