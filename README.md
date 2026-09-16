# Personal dotfiles

Configuration is stored in `home/`, preserving its original paths.
`manifest.txt` lists the paths installed by `./install.sh`.

## Before committing

Review every copied file for tokens, passwords, private URLs, and machine-specific
paths. Exclusions are only a convenience, not a complete secret scanner.
The collector does not discover arbitrary files sourced by your shell configuration.
Check custom ZSH, ZSH_CUSTOM, ZDOTDIR, and XDG_CONFIG_HOME paths manually.

The Oh My Zsh installation and editor/tmux plugins are copied when present, with
nested Git metadata removed. This preserves local modifications but does not retain
their Git update history. Upstream licenses are retained. Compiled plugin components
may need rebuilding for Linux.

## Install

In your Coder workspace, clone this repository, enter its directory, then run:

```sh
make install
exec zsh -l
```

`make` alone also runs installation. The template must already include Git and
Make so you can clone and run this command. On macOS, install Apple's Command Line
Tools (`xcode-select --install`) if Git/Make are missing. Install Homebrew from
https://brew.sh if additional tools are needed; the installer uses `brew install`
for missing Git, Vim, Zsh, tmux, and curl, supporting Intel and Apple Silicon paths.
On Ubuntu/Debian, it adds missing tools using apt (root or passwordless sudo required).
For a workspace without sudo, bake these tools into its template image first.
Development dependencies are selected in `tools.txt`. `make tools` installs them
without relinking settings. Supported profiles: `go`, `copilot`, `python`,
`powerline`, `vimpilot`, and `colima` (macOS only).

Go includes gopls, goimports, errcheck, Delve, gotags, gomodifytags, and impl.
Go tool versions use @latest on first installation; existing binaries are retained.
Copilot uses Node 22 when no suitable Node exists, plus Vim 9.0.0185 or newer.
Powerline uses an isolated Python environment. VimPilot uses its matching embedded
Python with the legacy openai 0.28.1 dependency; provide OPENAI_API_KEY separately.
Its existing model/API call is retained and not guaranteed to remain supported.
Colima and Docker CLI are installed only on macOS; no VM or daemon is started.
The remote Coder workspace is not given a Docker socket or daemon.

Dependencies require network access to the package managers, GitHub, Node, Go,
and PyPI. Packages may be upgraded when required by the configured plugins.

The installer backs up conflicting paths under `~/.dotfiles-backup.*` and links
this checkout into your home. Repeating installation leaves existing correct
links alone. Keep the checkout in place. It does not change your login shell;
`exec zsh -l` switches the current terminal, or `make shell` opens a child Zsh.
`make link` only links configuration and skips package installation.

Your copied Oh My Zsh installation, custom themes, and plugins are used directly.
Detection covers the profiles above; arbitrary plugin dependencies are not inferred.
Review macOS-specific commands and paths before using this configuration on Ubuntu.
Coder can also run `install.sh` through its dotfiles feature without Make.

No files are staged, committed, or pushed automatically.

## tmux keys

Prefix: Ctrl-a. Then h/j/k/l selects a pane; H/J/K/L resizes it.
`|` splits left/right, `-` splits top/bottom, `c` creates a window, and `r` reloads.
Ctrl-a then `[` enters copy mode: use Vim movement, `v` to select, `y` to copy.
Ctrl-a then `]` pastes the tmux buffer. Ctrl-a Ctrl-a sends a literal Ctrl-a.
Copy uses tmux's buffer, not necessarily your laptop clipboard over SSH.

## Repository layout

The new Make installer uses `home/` as its configuration source. Existing `vim/`,
`vimrc`, `zshrc`, `oh-my-zsh/`, and other legacy paths are retained for reference.
They are not installed by `make install`.

Clone over SSH: `git clone git@github.com:malnick/dotfiles.git`.
