local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme_dirs = { wezterm.config_dir .. '/..' }
config.color_scheme = 'Apollo'

return config
