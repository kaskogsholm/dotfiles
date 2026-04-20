local wezterm = require("wezterm")

local smart_splits = wezterm.plugin.require("https://github.com/mrjones2014/smart-splits.nvim")
local workspace_switcher = wezterm.plugin.require("https://github.com/MLFlexer/smart_workspace_switcher.wezterm")

local config = wezterm.config_builder()
config:set_strict_mode(true)

local is_windows = wezterm.target_triple:find("windows") ~= nil

config.color_scheme = "Argonaut"
config.window_close_confirmation = "NeverPrompt"

config.skip_close_confirmation_for_processes_named = {
	"bash",
	"sh",
	"zsh",
	"fish",
	"tmux",
	"nu",
	"cmd.exe",
	"pwsh.exe",
	"powershell.exe",
	"wsl.exe",
	"wezterm.exe",
	"wezterm-gui.exe",
	"wezterm",
	"wezterm-gui",
}

config.font = wezterm.font_with_fallback({
	"MesloLGS NF",
	"MesloLGS Nerd Font",
	"JetBrains Mono",
	"Noto Sans Mono",
})

config.background = {
	{
		source = {
			File = "lorenz.png",
		},
		repeat_x = "Mirror",
		hsb = { brightness = 0.3 },
		attachment = { Parallax = 0 },
	},
}

config.keys = {
	{
		key = "s",
		mods = "CTRL|SHIFT",
		action = workspace_switcher.switch_workspace(),
	},
	{
		key = "w",
		mods = "CTRL|SHIFT",
		action = wezterm.action.CloseCurrentTab({ confirm = false }),
	},
	{
		key = "x",
		mods = "SHIFT|ALT",
		action = wezterm.action.CloseCurrentPane({ confirm = false }),
	},
	{
		key = "|",
		mods = "SHIFT|ALT",
		action = wezterm.action.SplitHorizontal({ domain = "CurrentPaneDomain" }),
	},
	{
		key = "_",
		mods = "SHIFT|ALT",
		action = wezterm.action.SplitVertical({ domain = "CurrentPaneDomain" }),
	},
}

smart_splits.apply_to_config(config, {
	direction_keys = { "h", "j", "k", "l" },
	modifiers = {
		move = "CTRL",
		resize = "ALT",
	},
})

if is_windows then
	config.wsl_domains = {
		{
			name = "WSL:Ubuntu",
			distribution = "Ubuntu",
			default_cwd = "~",
		},
	}
	config.default_domain = "WSL:Ubuntu"
else
	-- On Linux/Unix, let wezterm use the normal local domain.
	-- Uncomment to force a specific shell:
	-- config.default_prog = { "/usr/bin/zsh", "-l" }
end

return config
