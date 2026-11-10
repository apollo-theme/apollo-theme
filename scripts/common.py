from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATHS = {
    "dark": ROOT / "palette" / "apollo.json",
    "light": ROOT / "palette" / "apollo-light.json",
}
PALETTE_PATH = PALETTE_PATHS["dark"]
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")

APPS = {
    "sonicterm": {"name": "SonicTerm", "family": "terminal", "platform": "Cross-platform", "badge_fragment": "target-SonicTerm%20%C2%B7%20cross--platform-", "install_anchor": "install", "light_artifact": "apollo-light.toml"},
    "windows-terminal": {"name": "Windows Terminal", "family": "terminal", "platform": "Windows", "badge_fragment": "target-Windows%20Terminal%20%C2%B7%20Windows-", "install_anchor": "install", "light_artifact": "apollo-light.json"},
    "firefox": {"name": "Firefox", "family": "browser", "platform": "Browser", "badge_fragment": "Target-Firefox-", "install_anchor": "install-sign-and-uninstall", "light_artifact": "variants/light/manifest.json"},
    "vscode": {"name": "Visual Studio Code", "family": "editor", "platform": "Cross-platform", "badge_fragment": "target-Visual%20Studio%20Code-", "install_anchor": "install", "light_artifact": "themes/apollo-light-color-theme.json"},
    "visual-studio": {"name": "Visual Studio", "family": "editor", "platform": "Windows", "badge_fragment": "target-Visual%20Studio%202022%2B-", "install_anchor": "install", "light_artifact": "themes/Apollo Light.vstheme"},
    "vim": {"name": "Vim", "family": "editor", "platform": "Cross-platform", "badge_fragment": "target-Vim-", "install_anchor": "install", "light_artifact": "colors/apollo-light.vim"},
    "nvim": {"name": "Neovim", "family": "editor", "platform": "Cross-platform", "badge_fragment": "target-Neovim-", "install_anchor": "install", "light_artifact": "colors/apollo-light.lua"},
    "xcode": {"name": "Xcode", "family": "editor", "platform": "macOS", "badge_fragment": "target-Xcode%2026-", "install_anchor": "install-and-activate", "light_artifact": "Apollo Light.xccolortheme"},
    "tmux": {"name": "tmux", "family": "multiplexer", "platform": "Terminal", "badge_fragment": "Target-tmux-", "install_anchor": "install", "light_artifact": "apollo-light.tmux"},
    "rmux": {"name": "RMUX", "family": "multiplexer", "platform": "Terminal", "badge_fragment": "Target-RMUX-", "install_anchor": "install", "light_artifact": "apollo-rmux-light.conf"},
    "powershell": {"name": "PowerShell", "family": "shell", "platform": "Cross-platform", "badge_fragment": "PowerShell-7.2%2B-", "install_anchor": "install", "light_artifact": "ApolloTheme.psm1"},
    "bat": {"name": "bat", "family": "utility", "platform": "CLI", "badge_fragment": "app-bat-", "install_anchor": "install", "light_artifact": "Apollo Light.tmTheme"},
    "eza": {"name": "eza", "family": "utility", "platform": "CLI", "badge_fragment": "eza-0.23.5%2B-", "install_anchor": "install", "light_artifact": "light/theme.yml"},
    "wezterm": {"name": "WezTerm", "family": "terminal", "platform": "Cross-platform", "badge_fragment": "target-WezTerm%20%C2%B7%20cross--platform-", "install_anchor": "install", "light_artifact": "apollo-light.toml"},
    "iterm2": {"name": "iTerm2", "family": "terminal", "platform": "macOS", "badge_fragment": "target-iTerm2%20%C2%B7%20macOS-", "install_anchor": "install", "light_artifact": "Apollo Light.itermcolors"},
    "apple-terminal": {"name": "Apple Terminal", "family": "terminal", "platform": "macOS", "badge_fragment": "target-Apple%20Terminal%20%C2%B7%20macOS-", "install_anchor": "install", "light_artifact": "Apollo Light.terminal"},
    "alacritty": {"name": "Alacritty", "family": "terminal", "platform": "Cross-platform", "badge_fragment": "target-Alacritty%20%C2%B7%20cross--platform-", "install_anchor": "install", "light_artifact": "apollo-light.toml"},
}

SLUGS = tuple(APPS)
CLONE_APPS = ("vim", "nvim", "tmux", "rmux", "powershell", "bat", "eza")
MONOREPO = "https://github.com/apollo-theme/apollo-theme"

FORBIDDEN_LINEAGE_PHRASES = (
    "gruvbox",
    "base16",
    "sonicterm-modified",
    "based on sonicterm",
    "derived from sonicterm",
)


def markdown_anchor(heading: str) -> str:
    normalized = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"\s+", "-", normalized.strip())


def readme_blocks(text: str, marker: str) -> list[str]:
    """Return the body of each fenced code block that directly follows ``<!-- smoke:<marker> -->``."""
    pattern = re.compile(
        rf"<!--\s*smoke:{re.escape(marker)}\s*-->[ \t]*\n(?:[ \t]*\n)*"
        r"[ \t]*(?P<fence>`{3,}|~{3,})[^\n]*\n(?P<body>.*?)^[ \t]*(?P=fence)[ \t]*$",
        re.MULTILINE | re.DOTALL,
    )
    return [match.group("body") for match in pattern.finditer(text)]


def palette_path(variant: str | Path = "dark") -> Path:
    if isinstance(variant, Path):
        return variant
    try:
        return PALETTE_PATHS[variant]
    except KeyError as error:
        raise ValueError(f"unknown Apollo variant: {variant}") from error


def load_palette(variant: str | Path = "dark") -> dict:
    return json.loads(palette_path(variant).read_text(encoding="utf-8"))


def load_palettes() -> dict[str, dict]:
    return {variant: load_palette(variant) for variant in PALETTE_PATHS}


def palette_sha256(variant: str | Path = "dark") -> str:
    return hashlib.sha256(palette_path(variant).read_bytes()).hexdigest()


def iter_hex_colors(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from iter_hex_colors(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_hex_colors(nested)
    elif isinstance(value, str) and value.startswith("#"):
        yield value


def relative_luminance(color: str) -> float:
    channels = []
    for offset in (1, 3, 5):
        channel = int(color[offset : offset + 2], 16) / 255
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)
