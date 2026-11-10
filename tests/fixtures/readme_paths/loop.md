# Loop and variables

```sh
clone_dir="$HOME/.config/apollo-theme/bat"
theme_dir="$(bat --config-dir)/themes"
for name in 'Apollo.tmTheme' 'Apollo Light.tmTheme'; do
  installed_theme="$theme_dir/$name"
  cp "$clone_dir/$name" "$installed_theme"
done
```
