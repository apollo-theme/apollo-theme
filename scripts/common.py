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

LIGHT_ARTIFACTS = {
    "sonicterm-apollo-theme": "apollo-light.toml",
    "wezterm-apollo-theme": "apollo-light.toml",
    "iterm2-apollo-theme": "Apollo Light.itermcolors",
    "apple-terminal-apollo-theme": "Apollo Light.terminal",
    "alacritty-apollo-theme": "apollo-light.toml",
    "windows-terminal-apollo-theme": "apollo-light.json",
    "firefox-apollo-theme": "variants/light/manifest.json",
    "vscode-apollo-theme": "themes/apollo-light-color-theme.json",
    "visual-studio-apollo-theme": "themes/Apollo Light.vstheme",
    "vim-apollo-theme": "colors/apollo-light.vim",
    "nvim-apollo-theme": "colors/apollo-light.lua",
    "xcode-apollo-theme": "Apollo Light.xccolortheme",
    "tmux-apollo-theme": "apollo-light.tmux",
    "rmux-apollo-theme": "apollo-rmux-light.conf",
    "powershell-apollo-theme": "ApolloTheme.psm1",
    "bat-apollo-theme": "Apollo Light.tmTheme",
    "eza-apollo-theme": "light/theme.yml",
}

APP_METADATA = {
    "sonicterm-apollo-theme": {"slug": "sonicterm", "name": "SonicTerm", "family": "terminal", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-SonicTerm%20%C2%B7%20cross--platform-", "install_anchor": "install", "description": "SonicTerm Apollo Theme — dark and light.", "topics": ("sonicterm", "terminal-emulator", "terminal-theme")},
    "wezterm-apollo-theme": {"slug": "wezterm", "name": "WezTerm", "family": "terminal", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-WezTerm%20%C2%B7%20cross--platform-", "install_anchor": "install", "description": "WezTerm Apollo Theme — dark and light.", "topics": ("wezterm", "terminal-emulator", "terminal-theme")},
    "iterm2-apollo-theme": {"slug": "iterm2", "name": "iTerm2", "family": "terminal", "workflow": "check.yml", "platform": "macOS", "badge_fragment": "target-iTerm2%20%C2%B7%20macOS-", "install_anchor": "install", "description": "iTerm2 Apollo Theme — dark and light.", "topics": ("iterm2", "macos", "terminal-theme")},
    "apple-terminal-apollo-theme": {"slug": "apple-terminal", "name": "Apple Terminal", "family": "terminal", "workflow": "check.yml", "platform": "macOS", "badge_fragment": "target-Apple%20Terminal%20%C2%B7%20macOS-", "install_anchor": "install", "description": "Apple Terminal Apollo Theme — dark and light.", "topics": ("apple-terminal", "macos", "terminal-theme")},
    "alacritty-apollo-theme": {"slug": "alacritty", "name": "Alacritty", "family": "terminal", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-Alacritty%20%C2%B7%20cross--platform-", "install_anchor": "install", "description": "Alacritty Apollo Theme — dark and light.", "topics": ("alacritty", "terminal-emulator", "terminal-theme")},
    "windows-terminal-apollo-theme": {"slug": "windows-terminal", "name": "Windows Terminal", "family": "terminal", "workflow": "ci.yml", "platform": "Windows", "badge_fragment": "target-Windows%20Terminal%20%C2%B7%20Windows-", "install_anchor": "install", "description": "Windows Terminal Apollo Theme — dark and light.", "topics": ("windows-terminal", "windows", "terminal-theme")},
    "firefox-apollo-theme": {"slug": "firefox", "name": "Firefox", "family": "browser", "workflow": "ci.yml", "platform": "Browser", "badge_fragment": "Target-Firefox-", "install_anchor": "install-sign-and-uninstall", "description": "Firefox Apollo Theme — dark and light packages.", "topics": ("firefox", "firefox-theme", "browser-theme", "webextension")},
    "vscode-apollo-theme": {"slug": "vscode", "name": "Visual Studio Code", "family": "editor", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-Visual%20Studio%20Code-", "install_anchor": "install", "description": "Visual Studio Code Apollo Theme — dark and light.", "topics": ("vscode", "visual-studio-code", "editor-theme")},
    "visual-studio-apollo-theme": {"slug": "visual-studio", "name": "Visual Studio", "family": "editor", "workflow": "ci.yml", "platform": "Windows", "badge_fragment": "target-Visual%20Studio%202022%2B-", "install_anchor": "install", "description": "Visual Studio Apollo Theme — dark and light.", "topics": ("visual-studio", "windows", "ide-theme")},
    "vim-apollo-theme": {"slug": "vim", "name": "Vim", "family": "editor", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-Vim-", "install_anchor": "install", "description": "Vim Apollo Theme — dark and light.", "topics": ("vim", "vim-colorscheme", "editor-theme")},
    "nvim-apollo-theme": {"slug": "nvim", "name": "Neovim", "family": "editor", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "target-Neovim-", "install_anchor": "install", "description": "Neovim Apollo Theme — dark and light.", "topics": ("neovim", "nvim-colorscheme", "editor-theme")},
    "xcode-apollo-theme": {"slug": "xcode", "name": "Xcode", "family": "editor", "workflow": "check.yml", "platform": "macOS", "badge_fragment": "target-Xcode%2026-", "install_anchor": "install-and-activate", "description": "Xcode Apollo Theme — dark and light.", "topics": ("xcode", "macos", "ide-theme")},
    "tmux-apollo-theme": {"slug": "tmux", "name": "tmux", "family": "multiplexer", "workflow": "ci.yml", "platform": "Terminal", "badge_fragment": "Target-tmux-", "install_anchor": "install", "description": "tmux Apollo Theme — dark and light.", "topics": ("tmux", "terminal-multiplexer", "tmux-theme")},
    "rmux-apollo-theme": {"slug": "rmux", "name": "RMUX", "family": "multiplexer", "workflow": "ci.yml", "platform": "Terminal", "badge_fragment": "Target-RMUX-", "install_anchor": "install", "description": "RMUX Apollo Theme — dark and light.", "topics": ("rmux", "terminal-multiplexer", "terminal-theme")},
    "powershell-apollo-theme": {"slug": "powershell", "name": "PowerShell", "family": "shell", "workflow": "ci.yml", "platform": "Cross-platform", "badge_fragment": "PowerShell-7.2%2B-", "install_anchor": "install", "description": "PowerShell Apollo Theme for PSReadLine — dark and light.", "topics": ("powershell", "psreadline", "shell-theme")},
    "bat-apollo-theme": {"slug": "bat", "name": "bat", "family": "utility", "workflow": "ci.yml", "platform": "CLI", "badge_fragment": "app-bat-", "install_anchor": "install", "description": "bat Apollo Theme — dark and light.", "topics": ("bat", "syntax-highlighting", "cli-theme")},
    "eza-apollo-theme": {"slug": "eza", "name": "eza", "family": "utility", "workflow": "ci.yml", "platform": "CLI", "badge_fragment": "eza-0.23.5%2B-", "install_anchor": "install", "description": "eza Apollo Theme — dark and light.", "topics": ("eza", "ls", "cli-theme")},
}

REPOSITORIES = tuple(APP_METADATA)

MANAGEMENT_REPOSITORIES = {
    "apollo-theme.github.io": "https://github.com/apollo-theme/apollo-theme.github.io.git",
    ".github/organization": "https://github.com/apollo-theme/.github.git",
}

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
