#!/usr/bin/env python3
"""Generate the Apollo PSReadLine module from bundled palette snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "ApolloTheme.psm1"
MANIFEST_PATH = ROOT / "ApolloTheme.psd1"
PROFILE_PATH = ROOT / "ApolloTheme.profile.ps1"
VARIANTS = {
    "Dark": {
        "palette": ROOT / "palette" / "apollo.json",
        "sha256": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
        "id": "apollo",
    },
    "Light": {
        "palette": ROOT / "palette" / "apollo-light.json",
        "sha256": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        "id": "apollo-light",
    },
}


def load_palette(variant: str = "Dark") -> dict:
    config = VARIANTS[variant]
    raw = config["palette"].read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != config["sha256"]:
        raise ValueError(f"{variant} palette snapshot hash mismatch: {digest}")
    palette = json.loads(raw)
    if palette.get("id") != config["id"] or palette.get("schemaVersion") != 1:
        raise ValueError(f"unsupported Apollo {variant} palette snapshot")
    return palette


def load_palettes() -> dict[str, dict]:
    return {variant: load_palette(variant) for variant in VARIANTS}


def resolve_role(palette: dict, role: str) -> str:
    reference = palette["roles"][role]
    if not (reference.startswith("{colors.") and reference.endswith("}")):
        raise ValueError(f"role {role!r} is not a color reference")
    return palette["colors"][reference[8:-1]]


def selection_sequence(foreground: str, background: str) -> str:
    values = [
        int(foreground[index:index + 2], 16)
        for index in (1, 3, 5)
    ] + [
        int(background[index:index + 2], 16)
        for index in (1, 3, 5)
    ]
    return f"\x1b[38;2;{values[0]};{values[1]};{values[2]};48;2;{values[3]};{values[4]};{values[5]}m"


def token_colors(palette: dict) -> dict[str, str]:
    role = lambda name: resolve_role(palette, name)
    colors = palette["colors"]
    return {
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
        "Selection": selection_sequence(role("textPrimary"), role("selection")),
        "InlinePrediction": role("textInactive"),
        "ListPrediction": role("textSecondary"),
        "ListPredictionSelected": selection_sequence(role("canvas"), role("information")),
        "ListPredictionTooltip": role("textInactive"),
    }


def render_color_table(colors: dict[str, str]) -> str:
    entries = []
    for key, value in colors.items():
        if value.startswith("\x1b"):
            rendered_value = f'"{value.replace(chr(27), "`e")}"'
        else:
            rendered_value = f"'{value}'"
        entries.append(f"        {key} = {rendered_value}")
    return "\n".join(entries)


def render_module(palettes: dict[str, dict]) -> str:
    variant_tables = "\n".join(
        f"    {variant} = @{{\n{render_color_table(token_colors(palette))}\n    }}"
        for variant, palette in palettes.items()
    )
    return f'''# Generated from palette/apollo.json and palette/apollo-light.json by scripts/generate.py; do not edit.
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
$script:ApolloVariantColors = @{{
{variant_tables}
}}

function Get-ApolloPSReadLineColors {{
    [CmdletBinding()]
    param(
        [ValidateSet('Dark', 'Light')]
        [string] $Variant = 'Dark'
    )

    return $script:ApolloVariantColors[$Variant].Clone()
}}

function Get-ApolloSupportedColorProperties {{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Options
    )

    $supported = @{{}}
    foreach ($entry in $script:ApolloColorProperties.GetEnumerator()) {{
        if ($null -ne $Options.PSObject.Properties[$entry.Value]) {{
            $supported[$entry.Key] = $entry.Value
        }}
    }}
    return $supported
}}

function Enable-ApolloTheme {{
    [CmdletBinding()]
    param(
        [ValidateSet('Dark', 'Light')]
        [string] $Variant = 'Dark'
    )

    if (-not (Get-Module -Name PSReadLine)) {{
        Import-Module PSReadLine -ErrorAction Stop
    }}

    $options = Get-PSReadLineOption
    $supportedProperties = Get-ApolloSupportedColorProperties -Options $options
    $colors = Get-ApolloPSReadLineColors -Variant $Variant

    if ($null -eq $script:ApolloPreviousColors) {{
        $script:ApolloPreviousColors = @{{}}
        foreach ($entry in $supportedProperties.GetEnumerator()) {{
            $script:ApolloPreviousColors[$entry.Key] = $options.($entry.Value)
        }}
    }}

    $supportedColors = @{{}}
    foreach ($entry in $supportedProperties.GetEnumerator()) {{
        $supportedColors[$entry.Key] = $colors[$entry.Key]
    }}
    if ($supportedColors.Count -gt 0) {{
        Set-PSReadLineOption -Colors $supportedColors
    }}
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
    ModuleVersion = '0.2.0'
    GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'
    Author = 'D0n9X1n'
    CompanyName = 'Apollo Theme'
    Copyright = '(c) 2026 D0n9X1n. MIT License.'
    Description = 'Apollo Dark and Light semantic token colors for PSReadLine with reversible activation.'
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


def render_outputs() -> dict[Path, str]:
    return {
        OUTPUT_PATH: render_module(load_palettes()),
        MANIFEST_PATH: render_manifest(),
        PROFILE_PATH: render_profile(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated module files are stale")
    args = parser.parse_args()
    expected = render_outputs()
    if args.check:
        stale = [
            path.relative_to(ROOT)
            for path, text in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
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
