config\autonomous_timer_config.json
# timings for discord check and autonomous timer check
**

config\claude_aliases.sh
# Claude Autonomy Platform Aliases
# This file contains all ClAP aliases and commands
# It's designed to be sourced by Claude Code sessions
*conflicts with natural_commands.sh?*

config\claude_env.sh
# Claude Autonomy Platform Environment Variables
# Source this file to set up path variables for ClAP scripts
*contains hardcoded "Sonnet" name*

config\claude_infrastructure_config.template.txt
*all good*

config\claude_init.sh
# Claude Code Session Initialization
# This script ensures all ClAP commands are available in Claude Code sessions
# Called by utils/claude_code_init_hook.sh 
*contains hardcoded paths*

config\claude_state_detector.sh
*seems to be an alias to /utils/claude_state_detector_color.sh, combine into claude_aliases or natural_commands as appropriate*

config\comms_monitor_config.json
*contains timing for discord and gmail check, and alert message format*
*obsolete?*

config\context_hats_config.template.json
*fine for now*

config\context_monitoring.json
*threshold size, warning levels etc for filesize-baased context monitoring*
*probably obsolete*

config\my_discord_channels.json.template
*all good*

config\natural_commands.sh
*conflicts with claude_aliases.sh?*

config\prompts.json
*prompt templates for context escalation, new message alerts, etc*
*Seems up to date*

