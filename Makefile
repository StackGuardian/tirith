# Makefile for Tirith

.PHONY: help bump-version

help:
	@echo "Tirith Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  bump-version VERSION=X.Y.Z [TYPE=type] [DESC=description]"
	@echo "      Bump version to X.Y.Z"
	@echo "      Optional: TYPE (Added|Changed|Fixed|etc), DESC (description)"
	@echo ""
	@echo "Examples:"
	@echo "  make bump-version VERSION=1.0.5"
	@echo "  make bump-version VERSION=1.0.5 TYPE=Fixed DESC='Bug fix'"
	@echo "  make bump-version VERSION=1.1.0 TYPE=Added DESC='New feature'"

bump-version:
ifndef VERSION
	$(error VERSION is not set. Usage: make bump-version VERSION=X.Y.Z [TYPE=type] [DESC=description])
endif
ifdef TYPE
ifdef DESC
	@python3 tools/bump_version.py $(VERSION) --change-type $(TYPE) --description "$(DESC)"
else
	$(error If TYPE is set, DESC must also be set)
endif
else
	@python3 tools/bump_version.py $(VERSION)
endif
