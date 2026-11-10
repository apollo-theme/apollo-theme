<h1 align="center">bat Apollo Theme</h1>

<p align="center">Apollo gives bat a warm, high-contrast syntax view with focused TextMate scope mappings.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-bat"><img alt="Preview" src="https://img.shields.io/badge/status-Preview-fabd2f?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/bat-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/bat-apollo-theme/ci.yml?branch=main&style=flat-square&label=CI&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/bat-apollo-theme/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/bat-apollo-theme?display_name=tag&sort=semver&style=flat-square&label=Release&color=d3869b&labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-b8bb26?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/sharkdp/bat"><img alt="Theme for bat" src="https://img.shields.io/badge/app-bat-83a598?style=flat-square&labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=flat-square&labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-bat"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/bat.svg" alt="Simulated bat Apollo Dark preview"></a>
  <a href="https://apollo-theme.github.io/#app-bat-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/bat-light.svg" alt="Simulated bat Apollo Light preview"></a>
</p>
<p align="center"><em>Simulated preview. Syntax grammar, terminal, and font rendering may vary.</em></p>

Apollo Dark preserves the existing `Apollo.tmTheme`, `BAT_THEME=Apollo`, and `Apollo` selector for compatibility. Apollo Light is its explicit light companion in `Apollo Light.tmTheme` and the `Apollo Light` selector. Both themes distinguish common syntax, markup, and diff scopes while leaving your bat configuration untouched until you explicitly select one.

## Install

Clone the repository, then copy each theme only when that destination is unused. The ownership ledger records the name and exact installed hash of files this clone created; pre-existing themes are never overwritten or claimed:

```sh
git clone https://github.com/apollo-theme/bat-apollo-theme "$HOME/.config/bat-apollo-theme"
clone_dir="$HOME/.config/bat-apollo-theme"
theme_dir="$(bat --config-dir)/themes"
marker="$clone_dir/.installed-theme-hashes"
installed=0
mkdir -p "$theme_dir"
touch "$marker"
for name in 'Apollo.tmTheme' 'Apollo Light.tmTheme'; do
  source_theme="$clone_dir/$name"
  installed_theme="$theme_dir/$name"
  if [ -e "$installed_theme" ]; then
    printf '%s\n' "$name already exists; nothing was overwritten."
  else
    cp "$source_theme" "$installed_theme"
    hash="$(shasum -a 256 "$installed_theme" | cut -d ' ' -f 1)"
    grep -F -v "$(printf '%s\t' "$name")" "$marker" > "$marker.tmp" || true
    mv "$marker.tmp" "$marker"
    printf '%s\t%s\n' "$name" "$hash" >> "$marker"
    installed=1
  fi
done
[ "$installed" -eq 0 ] || bat cache --build
```

## Activate

Use either variant for one command:

```sh
BAT_THEME=Apollo bat path/to/file
BAT_THEME='Apollo Light' bat path/to/file
```

Or opt in for the current shell with `export BAT_THEME=Apollo` or `export BAT_THEME='Apollo Light'`. No bat config file is edited.

## Uninstall

The uninstall guard considers only the two expected names recorded by this clone, and removes a file only if its current hash still matches the recorded installation hash. Pre-existing, unrecorded, moved, or modified themes are preserved. The cache is rebuilt once if at least one owned file is removed.

```sh
clone_dir="$HOME/.config/bat-apollo-theme"
theme_dir="$(bat --config-dir)/themes"
marker="$clone_dir/.installed-theme-hashes"
removed=0
if [ -f "$marker" ]; then
  while IFS="$(printf '\t')" read -r name expected_hash; do
    case "$name" in
      'Apollo.tmTheme'|'Apollo Light.tmTheme') ;;
      *) printf '%s\n' "Unknown ownership entry $name; it was preserved."; continue ;;
    esac
    installed_theme="$theme_dir/$name"
    [ -f "$installed_theme" ] || continue
    actual_hash="$(shasum -a 256 "$installed_theme" | cut -d ' ' -f 1)"
    if [ "$actual_hash" = "$expected_hash" ]; then
      rm -- "$installed_theme"
      removed=1
    else
      printf '%s\n' "$name has changed; it was preserved."
    fi
  done < "$marker"
fi
[ "$removed" -eq 0 ] || bat cache --build
unset BAT_THEME
rm -rf "$clone_dir"
```

## Visual check

Render a small Python sample without paging or decorations, selecting `Apollo` or `Apollo Light`:

```sh
printf '%s\n' 'def hello(name):' '    return "hello " + name' |
  bat --language=Python --style=plain --color=always --theme='Apollo Light'
```

Use Apollo Light with a light terminal background. In either variant, syntax roles should remain distinct and readable.

## Development

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

The checker validates the TextMate plist and, when bat is installed, builds an isolated cache and renders a sample. Change scope mappings in `scripts/generate.py`; do not hand-edit generated `Apollo.tmTheme`.

## License

[MIT](LICENSE)
