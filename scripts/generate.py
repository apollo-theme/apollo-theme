#!/usr/bin/env python3
"""Generate the Apollo PSReadLine module from the bundled palette snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "ApolloTheme.psm1"
MANIFEST_PATH = ROOT / "ApolloTheme.psd1"
PROFILE_PATH = ROOT / "ApolloTheme.profile.ps1"
PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"


def load_palette() -> dict:
    raw = PALETTE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PALETTE_SHA256:
        raise ValueError(f"palette snapshot hash mismatch: {digest}")
    palette = json.loads(raw)
    if palette.get("id") != "apollo" or palette.get("schemaVersion") != 1:
        raise ValueError("unsupported Apollo palette snapshot")
    return palette


def resolve_role(palette: dict, role: str) -> str:
    reference = palette["roles"][role]
    if not (reference.startswith("{colors.") and reference.endswith("}")):
        raise ValueError(f"role {role!r} is not a color reference")
    return palette["colors"][reference[8:-1]]


def render_module(palette: dict) -> str:
    role = lambda name: resolve_role(palette, name)
    colors = palette["colors"]
    token_colors = {
        "ContinuationPrompt": role("textSecondary"),
        "Emphasis": role("focus"),
        "Error": role("error"),
        "Default": role("textPrimary"),
        "Comment": role("textInactive"),
        "Keyword": role("information"),
        "String": role("success"),
        "Operator": role("textSecondary"),
        "Variable": colors["cyan"],
        "Command": role("focus"),
        "Parameter": colors["magenta"],
        "Type": role("information"),
        "Number": colors["magenta"],
        "Member": colors["cyan"],
        "Selection": f'\x1b[38;2;{int(role("textPrimary")[1:3], 16)};{int(role("textPrimary")[3:5], 16)};{int(role("textPrimary")[5:7], 16)};48;2;{int(role("selection")[1:3], 16)};{int(role("selection")[3:5], 16)};{int(role("selection")[5:7], 16)}m',
        "InlinePrediction": role("textInactive"),
        "ListPrediction": role("textSecondary"),
        "ListPredictionSelected": f'\x1b[38;2;{int(role("canvas")[1:3], 16)};{int(role("canvas")[3:5], 16)};{int(role("canvas")[5:7], 16)};48;2;{int(role("information")[1:3], 16)};{int(role("information")[3:5], 16)};{int(role("information")[5:7], 16)}m',
        "ListPredictionTooltip": role("textInactive"),
    }
    entries = []
    for key, value in token_colors.items():
        if value.startswith("\x1b"):
            rendered_value = f'"{value.replace(chr(27), "`e")}"'
        else:
            rendered_value = f"'{value}'"
        entries.append(f"        {key} = {rendered_value}")
    table = "\n".join(entries)
    return f'''# Generated from palette/apollo.json by scripts/generate.py; do not edit.
Set-StrictMode -Version Latest

$script:ApolloPreviousColors = $null
$script:ApolloColorProperties = @{{
    ContinuationPrompt = 'ContinuationPromptColor'
    Emphasis = 'EmphasisColor'
    Error = 'ErrorColor'
    Default = 'DefaultTokenColor'
    Comment = 'CommentColor'
    Keyword = 'KeywordColor'
    String = 'StringColor'
    Operator = 'OperatorColor'
    Variable = 'VariableColor'
    Command = 'CommandColor'
    Parameter = 'ParameterColor'
    Type = 'TypeColor'
    Number = 'NumberColor'
    Member = 'MemberColor'
    Selection = 'SelectionColor'
    InlinePrediction = 'InlinePredictionColor'
    ListPrediction = 'ListPredictionColor'
    ListPredictionSelected = 'ListPredictionSelectedColor'
    ListPredictionTooltip = 'ListPredictionTooltipColor'
}}

function Get-ApolloPSReadLineColors {{
    [CmdletBinding()]
    param()

    return @{{
{table}
    }}
}}

function Enable-ApolloTheme {{
    [CmdletBinding()]
    param()

    if (-not (Get-Module -Name PSReadLine)) {{
        Import-Module PSReadLine -ErrorAction Stop
    }}

    if ($null -eq $script:ApolloPreviousColors) {{
        $options = Get-PSReadLineOption
        $script:ApolloPreviousColors = @{{}}
        foreach ($entry in $script:ApolloColorProperties.GetEnumerator()) {{
            $script:ApolloPreviousColors[$entry.Key] = $options.($entry.Value)
        }}
    }}

    Set-PSReadLineOption -Colors (Get-ApolloPSReadLineColors)
}}

function Disable-ApolloTheme {{
    [CmdletBinding()]
    param()

    if ($null -eq $script:ApolloPreviousColors) {{
        return
    }}

    Set-PSReadLineOption -Colors $script:ApolloPreviousColors
    $script:ApolloPreviousColors = $null
}}

Export-ModuleMember -Function Get-ApolloPSReadLineColors, Enable-ApolloTheme, Disable-ApolloTheme
'''


def render_manifest() -> str:
    return """@{
    RootModule = 'ApolloTheme.psm1'
    ModuleVersion = '1.0.0'
    GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'
    Author = 'D0n9X1n'
    CompanyName = 'Apollo Theme'
    Copyright = '(c) 2026 D0n9X1n. MIT License.'
    Description = 'Apollo semantic token colors for PSReadLine with reversible activation.'
    PowerShellVersion = '7.2'
    FunctionsToExport = @('Get-ApolloPSReadLineColors', 'Enable-ApolloTheme', 'Disable-ApolloTheme')
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
    PrivateData = @{
        PSData = @{
            ProjectUri = 'https://github.com/apollo-theme/powershell-apollo-theme'
            LicenseUri = 'https://github.com/apollo-theme/powershell-apollo-theme/blob/main/LICENSE'
            Tags = @('Apollo', 'Theme', 'PSReadLine')
        }
    }
}
"""


def render_profile() -> str:
    return """# Source this file from your PowerShell profile to opt in to Apollo.
Import-Module (Join-Path $PSScriptRoot 'ApolloTheme.psd1') -Force
Enable-ApolloTheme
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated module files are stale")
    args = parser.parse_args()
    expected = {
        OUTPUT_PATH: render_module(load_palette()),
        MANIFEST_PATH: render_manifest(),
        PROFILE_PATH: render_profile(),
    }
    if args.check:
        stale = [path.relative_to(ROOT) for path, text in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
        if stale:
            print("stale generated file(s): " + ", ".join(map(str, stale)))
            return 1
        print("PowerShell module is up to date")
        return 0
    for path, text in expected.items():
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
