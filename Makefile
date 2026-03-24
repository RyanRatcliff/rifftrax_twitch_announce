LABEL      = com.rifftrax.bot
PLIST_PATH = $(HOME)/Library/LaunchAgents/$(LABEL).plist
PYTHON    := $(shell which python3)
DIR       := $(CURDIR)
LOG        = $(HOME)/.rifftrax_bot.log
ERR        = $(HOME)/.rifftrax_bot_error.log

define PLIST_XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Label</key>
	<string>$(LABEL)</string>
	<key>ProgramArguments</key>
	<array>
		<string>$(PYTHON)</string>
		<string>$(DIR)/bot.py</string>
	</array>
	<key>WorkingDirectory</key>
	<string>$(DIR)</string>
	<key>KeepAlive</key>
	<true/>
	<key>RunAtLoad</key>
	<true/>
	<key>StandardOutPath</key>
	<string>$(LOG)</string>
	<key>StandardErrorPath</key>
	<string>$(ERR)</string>
</dict>
</plist>
endef
export PLIST_XML

.PHONY: install start stop restart uninstall logs status

## Install and start the bot as a background service (auto-restarts on crash)
install:
	@echo "$$PLIST_XML" > "$(PLIST_PATH)"
	@launchctl load "$(PLIST_PATH)"
	@echo "Installed and started. Logs: $(LOG)"

## Start the service (after install or following a stop)
start:
	@launchctl load "$(PLIST_PATH)"
	@echo "Service started."

## Stop the service
stop:
	@launchctl unload "$(PLIST_PATH)"
	@echo "Service stopped."

## Restart the service
restart: stop start

## Remove the service entirely (stop + delete plist)
uninstall:
	@-launchctl unload "$(PLIST_PATH)" 2>/dev/null; true
	@rm -f "$(PLIST_PATH)"
	@echo "Service uninstalled."

## Follow the bot log in real time
logs:
	@tail -f "$(LOG)"

## Show whether the service is running
status:
	@launchctl list | grep -q "$(LABEL)" && echo "Running" || echo "Stopped"

## Run the test suite
test:
	@python3 -m pytest tests/ -v
