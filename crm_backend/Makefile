# Proxy Makefile — forwards all targets to the project root Makefile.
# This lets you run `make test`, `make lint`, etc. from inside crm_backend/.

ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || cd .. && pwd)

.DEFAULT_GOAL := help

help:
	@$(MAKE) -C $(ROOT) help

%:
	@$(MAKE) -C $(ROOT) $(MAKECMDGOALS)

.PHONY: help