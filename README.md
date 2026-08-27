# Apollo for Vim

Apollo is a high-contrast dark colorscheme derived from the canonical SonicTerm Apollo palette. It provides broad Vim UI, syntax, diff, and diagnostic highlighting, exact terminal ANSI colors, and both truecolor and xterm-256 definitions.

Repository: https://github.com/apollo-theme/vim-apollo-theme

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

Without `termguicolors`, Apollo uses its 256-color fallbacks.

## Uninstall

For vim-plug, remove the `Plug` line, restart Vim, and run `:PlugClean`. For the manual package:

```sh
rm -rf ~/.vim/pack/apollo/start/vim-apollo-theme
```

Then remove `colorscheme apollo` from `.vimrc`.

## Development

`palette/apollo.json` is an exact palette snapshot. Regenerate `colors/apollo.vim` and run every check with:

```sh
python3 scripts/generate.py
python3 scripts/check.py
```

## License

MIT
