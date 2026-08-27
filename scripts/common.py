from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")

REPOSITORIES = (
    "sonicterm-apollo-theme",
    "wezterm-apollo-theme",
    "iterm2-apollo-theme",
    "apple-terminal-apollo-theme",
    "alacritty-apollo-theme",
    "windows-terminal-apollo-theme",
    "firefox-apollo-theme",
    "vscode-apollo-theme",
    "visual-studio-apollo-theme",
    "vim-apollo-theme",
    "nvim-apollo-theme",
    "xcode-apollo-theme",
    "tmux-apollo-theme",
    "rmux-apollo-theme",
    "powershell-apollo-theme",
    "bat-apollo-theme",
    "eza-apollo-theme",
)


def load_palette(path: Path = PALETTE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def palette_sha256(path: Path = PALETTE_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
