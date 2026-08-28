<h1 align="center">PowerShell Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast semantic color to PowerShell and PSReadLine.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-powershell"><img alt="Preview" src="https://img.shields.io/badge/status-Preview-fabd2f?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/powershell-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/powershell-apollo-theme/ci.yml?branch=main&style=flat-square&label=CI&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/powershell-apollo-theme/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/powershell-apollo-theme?display_name=tag&sort=semver&style=flat-square&label=Release&color=d3869b&labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-b8bb26?style=flat-square&labelColor=141617"></a>
  <a href="https://learn.microsoft.com/powershell/"><img alt="PowerShell 7.2 or newer" src="https://img.shields.io/badge/PowerShell-7.2%2B-83a598?style=flat-square&logo=powershell&logoColor=white&labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=flat-square&labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-powershell"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/powershell.svg" alt="Simulated PowerShell Apollo Theme preview"></a>
</p>
<p align="center"><em>Simulated preview. Terminal, font, and PSReadLine rendering may vary.</em></p>

Apollo is a small PowerShell module that maps the canonical palette to PSReadLine semantic tokens. Activation is explicit, captures the colors already in use, and can restore them without rewriting your profile.

## Install

Clone the repository into a dedicated configuration directory:

```powershell
git clone https://github.com/apollo-theme/powershell-apollo-theme "$HOME/.config/powershell-apollo-theme"
```

This only creates the clone; it does not edit `$PROFILE` or enable the theme.

## Activate

Import and enable Apollo for the current session:

```powershell
Import-Module "$HOME/.config/powershell-apollo-theme/ApolloTheme.psd1" -Force
Enable-ApolloTheme
```

To opt in for future sessions, manually dot-source `ApolloTheme.profile.ps1` from your PowerShell profile. The repository never writes that line for you.

## Restore and uninstall

If you added the profile line, remove it first. Then restore the PSReadLine colors captured at first activation, unload the module, and remove the clone:

```powershell
Disable-ApolloTheme
Remove-Module ApolloTheme
Remove-Item -Recurse -Force "$HOME/.config/powershell-apollo-theme"
```

Repeated calls to `Enable-ApolloTheme` do not replace the saved pre-Apollo values, and calling `Disable-ApolloTheme` while inactive is safe. Apollo only sets color properties exposed by the installed PSReadLine version, so the PSReadLine bundled with PowerShell 7.2 works without newer list-prediction properties.

## Visual check

In an interactive PowerShell session, type this without immediately submitting it:

```powershell
Get-ChildItem -Path $HOME | Where-Object { $_.Name -like '*.txt' } # Apollo
```

Commands should be gold, parameters magenta, variables cyan, strings green, keywords blue, ordinary text warm beige, and comments muted brown-gray. Errors should be red.

## Development

PowerShell 7 and PSReadLine are required for native assertions; no Pester dependency is used.

```powershell
python scripts/generate.py --check
python scripts/check.py
python -m unittest discover -s tests -v
pwsh -NoLogo -NoProfile -NonInteractive -File tests/Test-ApolloTheme.ps1
```

Generated module and profile files are deterministic. Make mapping changes in `scripts/generate.py`, then regenerate rather than editing generated output directly.

## License

[MIT](LICENSE)
