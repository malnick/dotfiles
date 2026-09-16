.PHONY: install link shell tools
.DEFAULT_GOAL := install

install:
	@bash ./install.sh

link:
	@bash ./install.sh --links-only

shell:
	@zsh -l

tools:
	@bash ./install-dev-tools.sh
