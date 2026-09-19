.DEFAULT_GOAL := help
.PHONY: help setup build check docker-run docker-stop start stop status logs canton-console compose-config clean
help setup build check docker-run docker-stop start stop status logs canton-console compose-config clean:
	@$(MAKE) --no-print-directory -C quickstart $@
