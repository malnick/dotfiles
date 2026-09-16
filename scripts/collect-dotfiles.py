#!/usr/bin/env python3
"""Copy selected shell/editor settings to a NEW local Git repository.

Usage: python3 collect-dotfiles.py ~/dotfiles
Requires Python 3 and Git. Does not stage, commit, or publish any files.
"""

import argparse
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys


TARGETS = (
    ".vimrc", ".gvimrc", ".vim", ".config/vim",
    ".zshrc", ".zshenv", ".zprofile", ".zlogin", ".zlogout",
    ".p10k.zsh", ".config/zsh", ".oh-my-zsh",
    ".tmux.conf", ".tmux.conf.local", ".tmux", ".config/tmux",
)
SKIP_NAMES = {
    ".git", ".DS_Store", ".netrc", ".env", ".ssh", ".gnupg",
    ".zsh_history", ".bash_history", ".viminfo", ".lesshst", ".netrwhist",
    "cache", ".cache", "__pycache__", "node_modules",
    "undo", "undodir", "swap", "backup", "backups", "sessions",
    "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
}

INSTALLER = '''#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
platform="$(uname -s)"
# Find Homebrew in either standard macOS prefix, including fresh SSH sessions.
if [ "$platform" = Darwin ]; then
  for brew_prefix in /opt/homebrew /usr/local; do
    if [ -x "$brew_prefix/bin/brew" ]; then
      export PATH="$brew_prefix/bin:$PATH"
      break
    fi
  done
fi
case "${1:-}" in
  ""|--links-only) ;;
  *) printf 'Usage: %s [--links-only]\\n' "$0" >&2; exit 2 ;;
esac
if [ "${1:-}" != --links-only ]; then
  missing=()
  for tool in git vim zsh tmux curl; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      missing+=("$tool")
    fi
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    if [ "$platform" = Darwin ]; then
      if ! command -v brew >/dev/null 2>&1; then
        printf 'Install Homebrew from https://brew.sh, then rerun make install. Missing tools: %s\\n' "${missing[*]}" >&2
        exit 1
      fi
      brew install "${missing[@]}"
    elif [ "$platform" = Linux ] && command -v apt-get >/dev/null 2>&1; then
      as_root=()
      if [ "$(id -u)" -ne 0 ]; then
        if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true; then
          printf 'Installing tools requires root or passwordless sudo. Ask your template admin to preinstall: %s\\n' "${missing[*]}" >&2
          exit 1
        fi
        as_root=(sudo -n)
      fi
      ${as_root[@]+"${as_root[@]}"} apt-get update
      ${as_root[@]+"${as_root[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}" ca-certificates
    else
      printf 'Install these tools with your package manager, then rerun: %s\\n' "${missing[*]}" >&2
      exit 1
    fi
  fi
fi
if [ "${1:-}" != --links-only ]; then
  bash "$repo_dir/install-dev-tools.sh"
fi
# Validate all entries before changing the home directory.
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  case "$rel" in
    /*|..|../*|*/../*|*/..)
      printf 'Unsafe manifest path: %s\\n' "$rel" >&2; exit 1 ;;
  esac
  if [ ! -e "$repo_dir/home/$rel" ]; then
    printf 'Missing configuration: %s\\n' "$rel" >&2; exit 1
  fi
done < "$repo_dir/manifest.txt"
backup_dir=""
while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  source_path="$repo_dir/home/$rel"
  target_path="$HOME/$rel"
  if [ -L "$target_path" ] && [ "$(readlink "$target_path")" = "$source_path" ]; then
    continue
  fi
  if [ -e "$target_path" ] || [ -L "$target_path" ]; then
    if [ -z "$backup_dir" ]; then
      backup_dir="$(mktemp -d "$HOME/.dotfiles-backup.XXXXXXXX")"
    fi
    mkdir -p "$backup_dir/$(dirname "$rel")"
    mv "$target_path" "$backup_dir/$rel"
  fi
  mkdir -p "$(dirname "$target_path")"
  ln -s "$source_path" "$target_path"
  printf 'Linked %s\\n' "$rel"
done < "$repo_dir/manifest.txt"
if [ -n "$backup_dir" ]; then
  printf 'Previous configuration saved in %s\\n' "$backup_dir"
fi
printf 'Installed. Run exec zsh -l to enter your configured shell.\\n'
'''

MAKEFILE = '''.PHONY: install link shell tools
.DEFAULT_GOAL := install

install:
	@bash ./install.sh

link:
	@bash ./install.sh --links-only

shell:
	@zsh -l

tools:
	@bash ./install-dev-tools.sh
'''

TMUX = '''# Ctrl-a prefix; Ctrl-a Ctrl-a sends a literal Ctrl-a.
unbind C-b
set -g prefix C-a
bind C-a send-prefix
set -g mode-keys vi
set -g status-keys vi
set -sg escape-time 10
set -g history-limit 50000
set -g mouse on
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5
bind '|' split-window -h -c '#{pane_current_path}'
bind '-' split-window -v -c '#{pane_current_path}'
bind c new-window -c '#{pane_current_path}'
bind -T copy-mode-vi v send-keys -X begin-selection
bind -T copy-mode-vi y send-keys -X copy-selection-and-cancel
bind -T copy-mode-vi Escape send-keys -X cancel
bind r source-file ~/.tmux.conf \\; display-message 'tmux config reloaded'
'''

SHELL_ENV = '''# Managed dotfiles tool paths (macOS and Ubuntu).
export PATH="$HOME/.local/bin:$HOME/.local/share/dotfiles/runtimes/go/bin:$PATH"
if [ -s "$HOME/.local/share/dotfiles/nvm/nvm.sh" ]; then
  export NVM_DIR="$HOME/.local/share/dotfiles/nvm"
  . "$NVM_DIR/nvm.sh"
fi
'''


def sanitize(text):
    # Remove direct credential assignments without printing or writing their values.
    pattern = r'(?im)^\s*(?:export\s+)?[A-Z_][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*\s*=.*$'
    return re.sub(pattern, '# Credential assignment omitted; inject it separately.', text)


def customize(destination, selected):
    home = destination / "home"
    features = set()
    zsh = home / ".zshrc"
    if zsh.exists():
        content = zsh.read_text()
        if "powerline-shell" in content: features.add("powerline")
        if ".colima/" in content:
            features.add("colima")
            content = re.sub(r'(?m)^export DOCKER_HOST=.*\.colima/.*$',
                             'if [[ "$OSTYPE" == darwin* ]]; then\n  export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"\nfi', content)
        zsh.write_text(SHELL_ENV + "\n" + content)
    profile = home / ".zprofile"
    if profile.exists():
        content = profile.read_text()
        content = content.replace('eval "$(/opt/homebrew/bin/brew shellenv)"',
            'if [ -x /opt/homebrew/bin/brew ]; then\n  eval "$(/opt/homebrew/bin/brew shellenv)"\nelif [ -x /usr/local/bin/brew ]; then\n  eval "$(/usr/local/bin/brew shellenv)"\nfi')
        content = re.sub(r'(?m)^PATH="(/Library/Frameworks/Python.framework/Versions/[^"\n]+)"$',
                         r'if [ "$(uname -s)" = Darwin ]; then\n  PATH="\1"\nfi', content)
        profile.write_text(content)
        if "Python.framework" in content: features.add("python")
    if (home / ".vim/bundle/vim-go").exists(): features.add("go")
    if (home / ".vim/bundle/vim-copilot").exists(): features.add("copilot")
    if (home / ".vim/vim-pilot").exists():
        features.add("vimpilot")
        vimrc = home / ".vimrc"
        content = vimrc.read_text() if vimrc.exists() else ""
        vimrc.write_text('''" Load the isolated legacy VimPilot Python dependency when installed.
if has('python3') && filereadable(expand('~/.local/share/dotfiles/vimpilot-site.txt'))
python3 << EOF
import os, site
with open(os.path.expanduser('~/.local/share/dotfiles/vimpilot-site.txt')) as f:
    site.addsitedir(f.read().strip())
EOF
endif
''' + content)
        if ".vimrc" not in selected: selected.append(".vimrc")
    tmux = home / ".tmux.conf"
    tmux.parent.mkdir(parents=True, exist_ok=True)
    existing = tmux.read_text() if tmux.exists() else ""
    tmux.write_text(existing + "\n" + TMUX)
    if ".tmux.conf" not in selected: selected.append(".tmux.conf")
    (destination / "tools.txt").write_text("".join(item + "\n" for item in sorted(features)))
    for name in ("install-dev-tools.sh", "install-go.py"):
        shutil.copy2(Path(__file__).with_name(name), destination / name)


def excluded(name):
    return (
        name in SKIP_NAMES
        or name.startswith((".zcompdump", ".env."))
        or name.endswith((".zwc", ".swp", ".swo", ".pyc", ".log", ".pem", ".key", "~"))
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New directory to create (must not exist)")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Source home directory")
    args = parser.parse_args()
    source_home = args.home.expanduser().resolve()
    destination = args.destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        parser.error("Destination already exists; choose a new directory. Nothing was changed.")
    if not source_home.is_dir():
        parser.error("Source home is not a directory.")
    if shutil.which("git") is None:
        parser.error("Git is required.")
    # Prevent the output from recursively becoming part of an input tree.
    for rel in TARGETS:
        root = (source_home / rel).resolve()
        if root == destination.resolve() or root in destination.resolve().parents:
            parser.error("Destination must be outside all selected configuration directories.")
    os.umask(0o077)
    destination.mkdir(parents=True)
    notices = []

    def copy(source, target, ancestors):
        if excluded(source.name):
            return False
        real = source.resolve()
        # Materialize symlinks to make the result portable, but do not follow
        # links outside the source home or links back into an ancestor.
        if source_home != real and source_home not in real.parents:
            notices.append("Skipped external symlink: " + str(source.relative_to(source_home)))
            return False
        if real in ancestors:
            notices.append("Skipped symlink cycle: " + str(source.relative_to(source_home)))
            return False
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            for child in sorted(source.iterdir()):
                copy(child, target / child.name, ancestors | {real})
            return True
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                content = source.read_text()
            except (UnicodeError, ValueError):
                shutil.copy2(source, target)
            else:
                target.write_text(sanitize(content))
                shutil.copymode(source, target)
            return True
        notices.append("Skipped missing link or special file: " + str(source.relative_to(source_home)))
        return False

    selected = []
    for rel in TARGETS:
        source = source_home / rel
        if source.exists() or source.is_symlink():
            if copy(source, destination / "home" / rel, set()):
                selected.append(rel)
    customize(destination, selected)
    (destination / "manifest.txt").write_text("".join(rel + "\n" for rel in selected))
    (destination / "install.sh").write_text(INSTALLER)
    (destination / "install.sh").chmod(0o700)
    (destination / "Makefile").write_text(MAKEFILE)
    (destination / ".gitignore").write_text(
        ".DS_Store\n*.swp\n*.swo\n*~\n.zcompdump*\n*.zwc\n"
        ".zsh_history\n.viminfo\n.cache/\ncache/\n.env\n.env.*\n*.pem\n*.key\n"
    )
    (destination / "README.md").write_text('''# Personal dotfiles

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
''')
    subprocess.run(["git", "init", "--quiet", str(destination)], check=True)
    print("Created local repository:", destination)
    print("Copied:", ", ".join(selected) if selected else "No matching configuration found")
    for notice in notices:
        print(notice)
    print("Review the copied files for secrets and machine-specific paths before staging.")
    print("Nothing was committed or uploaded. Original configuration was not changed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print("Collection failed (output may be partial): " + str(error), file=sys.stderr)
        sys.exit(1)
