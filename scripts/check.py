#!/usr/bin/env python3
"""Validate generated PowerShell files and run native assertions when available."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "ApolloTheme.psm1"
MANIFEST = ROOT / "ApolloTheme.psd1"
RESTRICTED_DARK = "#665c54"
REQUIRED_KEYS = {
    "ContinuationPrompt", "Emphasis", "Error", "Default", "Comment", "Keyword",
    "String", "Operator", "Variable", "Command", "Parameter", "Type", "Number",
    "Member", "Selection", "InlinePrediction", "ListPrediction",
    "ListPredictionSelected", "ListPredictionTooltip",
}


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def validate_static() -> None:
    text = MODULE.read_text(encoding="utf-8")
    variant_table = text.split("$script:ApolloVariantColors = @{\n", 1)[1]
    dark_table = variant_table.split("    Light = @{", 1)[0]
    if RESTRICTED_DARK in dark_table.lower():
        raise AssertionError(f"{RESTRICTED_DARK} remains restricted in Apollo Dark")
    if "    Light = @{" not in variant_table:
        raise AssertionError("missing Apollo Light color table")
    for required in ("Get-ApolloPSReadLineColors", "Enable-ApolloTheme", "Disable-ApolloTheme"):
        if f"function {required}" not in text:
            raise AssertionError(f"missing exported function {required}")
    if text.count("[ValidateSet('Dark', 'Light')]") != 2:
        raise AssertionError("public variant parameters must accept exactly Dark and Light")
    if text.count("[string] $Variant = 'Dark'") != 2:
        raise AssertionError("public variant parameters must default to Dark")
    if "$Options.PSObject.Properties[$entry.Value]" not in text:
        raise AssertionError("PSReadLine properties must be filtered for version compatibility")
    if "$PROFILE" in text:
        raise AssertionError("module must not rewrite or reference $PROFILE")
    manifest = MANIFEST.read_text(encoding="utf-8")
    if "ModuleVersion = '0.2.0'" not in manifest:
        raise AssertionError("module version must be 0.2.0")
    if "GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'" not in manifest:
        raise AssertionError("module GUID changed")


def validate_powershell() -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise FileNotFoundError("pwsh")
    script = ROOT / "tests" / "Test-ApolloTheme.ps1"
    result = run([shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(script)])
    if "PowerShell Apollo theme tests passed" not in result.stdout:
        raise AssertionError(result.stdout + result.stderr)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"])
    validate_static()
    if shutil.which("pwsh") or shutil.which("powershell"):
        validate_powershell()
        print("direct PowerShell assertions passed")
    else:
        print("PowerShell not installed; native assertions skipped")
    print("PowerShell Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
