# Apollo for PowerShell

A small PowerShell module that applies Apollo colors to PSReadLine semantic tokens and restores the options that were active before Apollo. It never edits `$PROFILE` automatically.

Repository: https://github.com/apollo-theme/powershell-apollo-theme

## Install

```powershell
git clone https://github.com/apollo-theme/powershell-apollo-theme "$HOME/.config/powershell-apollo-theme"
```

This only creates the clone.

## Activate

For the current session:

```powershell
Import-Module "$HOME/.config/powershell-apollo-theme/ApolloTheme.psd1" -Force
Enable-ApolloTheme
```

To opt in for future sessions, manually dot-source `ApolloTheme.profile.ps1` from your profile. The repository does not write that line for you.

## Restore and uninstall

Restore the PSReadLine colors captured at first activation, unload the module, then remove the clone:

```powershell
Disable-ApolloTheme
Remove-Module ApolloTheme
Remove-Item -Recurse -Force "$HOME/.config/powershell-apollo-theme"
```

Calling `Enable-ApolloTheme` repeatedly does not replace the saved pre-Apollo values. Calling `Disable-ApolloTheme` when inactive is safe.

## Visual check

In an interactive PowerShell session, type (without immediately submitting):

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
