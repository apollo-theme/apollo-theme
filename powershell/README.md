<h1 align="center">PowerShell Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast semantic color to PowerShell and PSReadLine.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-powershell"><img alt="Preview" src="https://img.shields.io/badge/status-Preview-fabd2f?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&style=flat-square&label=CI&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=powershell"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=powershell-v*&display_name=tag&sort=semver&style=flat-square&label=Release&color=d3869b&labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-b8bb26?style=flat-square&labelColor=141617"></a>
  <a href="https://learn.microsoft.com/powershell/"><img alt="PowerShell 7.2 or newer" src="https://img.shields.io/badge/PowerShell-7.2%2B-83a598?style=flat-square&logo=powershell&logoColor=white&labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=flat-square&labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-powershell"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/powershell.svg" alt="Simulated PowerShell Apollo Dark preview"></a>
  <a href="https://apollo-theme.github.io/#app-powershell-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/powershell-light.svg" alt="Simulated PowerShell Apollo Light preview"></a>
</p>
<p align="center"><em>Simulated preview. Terminal, font, and PSReadLine rendering may vary.</em></p>

Apollo Dark remains the compatibility default for unsuffixed `Enable-ApolloTheme`; Apollo Light is the explicit opt-in variant. The single PowerShell module maps both canonical palettes to PSReadLine semantic tokens. Activation captures the colors already in use only on first activation and restores those true pre-Apollo values after any number of Dark/Light switches without rewriting your profile.

## Install

Apollo lives in the `powershell/` folder of [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme). Clone it once into the shared location (this is a no-op when the clone already exists; on Windows run it from Git Bash or any POSIX shell):

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

Cloning does not edit `$PROFILE`. To load Apollo Dark in every new session, append the import and activation lines to your profile:

<!-- smoke:install -->
```pwsh
New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null; Add-Content $PROFILE 'Import-Module "$HOME/.config/apollo-theme/powershell/ApolloTheme.psd1"', 'Enable-ApolloTheme -Variant Dark'
```

For Apollo Light, use `'Enable-ApolloTheme -Variant Light'` as the second line instead. Update later with `git -C "$HOME/.config/apollo-theme" pull`.

## Activate

To try either variant in the current session without touching your profile, import the module and enable a variant. Dark remains the default:

```pwsh
Import-Module "$HOME/.config/apollo-theme/powershell/ApolloTheme.psd1" -Force
Enable-ApolloTheme                 # Dark compatibility default
Enable-ApolloTheme -Variant Dark   # Explicit Dark
Enable-ApolloTheme -Variant Light  # Explicit Light
```

`Get-ApolloPSReadLineColors` accepts the same `-Variant Dark|Light` parameter. Apollo Light changes PSReadLine token colors only, so use it with a terminal profile that has a light background.

## Restore and uninstall

Remove the Apollo lines from your profile:

<!-- smoke:uninstall -->
```pwsh
Set-Content $PROFILE (Get-Content $PROFILE | Where-Object { $_ -notmatch 'ApolloTheme' })
```

In a session that is still running, restore the PSReadLine colors captured at first activation and unload the module:

```pwsh
Disable-ApolloTheme; Remove-Module ApolloTheme
```

Repeated calls to `Enable-ApolloTheme` do not replace the saved pre-Apollo values, and calling `Disable-ApolloTheme` while inactive is safe. Apollo only sets color properties exposed by the installed PSReadLine version, so the PSReadLine bundled with PowerShell 7.2 works without newer list-prediction properties.

## Remove the shared clone

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza all read from `~/.config/apollo-theme`. Uninstall each of them first, then run `rm -rf "$HOME/.config/apollo-theme"`.

## Visual check

In an interactive PowerShell session, type this without immediately submitting it:

```powershell
Get-ChildItem -Path $HOME | Where-Object { $_.Name -like '*.txt' } # Apollo
```

For Dark, commands should be gold, parameters magenta, variables cyan, strings green, keywords blue, ordinary text warm beige, and comments muted brown-gray. Light uses darker equivalents on a light terminal background. Errors should be red in either variant.

## Development

PowerShell 7 and PSReadLine are required for native assertions; no Pester dependency is used. Run these from the `powershell/` folder of the monorepo:

```sh
cd powershell
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
pwsh -NoLogo -NoProfile -NonInteractive -File tests/Test-ApolloTheme.ps1
```

Generated module and profile files are deterministic. Make mapping changes in `scripts/generate.py`, then regenerate rather than editing generated output directly. The root CI job `powershell` runs these checks on every change.

## License

[MIT](LICENSE)
