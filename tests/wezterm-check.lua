local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme_dirs = { '.' }
config.color_scheme = 'Apollo'

return config
