#!/usr/bin/env bash
# Generated repositories carry a copy of this file. Never source the user's config.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
platform="$(uname -s)"
export PATH="$HOME/.local/bin:$HOME/.local/share/dotfiles/runtimes/go/bin:$PATH"
if [ "$platform" = Darwin ]; then
  for prefix in /opt/homebrew /usr/local; do
    if [ -x "$prefix/bin/brew" ]; then export PATH="$prefix/bin:$PATH"; break; fi
  done
fi
has() { grep -qx "$1" "$repo_dir/tools.txt"; }
packages() {
  if [ "$platform" = Darwin ]; then
    command -v brew >/dev/null || { echo 'Install Homebrew from https://brew.sh first.' >&2; exit 1; }
    brew install "$@"
  elif [ "$platform" = Linux ] && command -v apt-get >/dev/null; then
    root=()
    if [ "$(id -u)" -ne 0 ]; then
      command -v sudo >/dev/null && sudo -n true || { echo "Preinstall these packages in your template: $*" >&2; exit 1; }
      root=(sudo -n)
    fi
    if [ "${apt_updated:-0}" != 1 ]; then ${root[@]+"${root[@]}"} apt-get update; apt_updated=1; fi
    ${root[@]+"${root[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
  else
    echo "Unsupported package manager; install these packages manually: $*" >&2; exit 1
  fi
}
if has python || has powerline || has go || has copilot || has vimpilot; then
  if ! command -v python3 >/dev/null; then
    if [ "$platform" = Darwin ]; then packages python; else packages python3; fi
  fi
fi
if has go; then
  if [ "$platform" = Linux ] && ! command -v cc >/dev/null; then packages build-essential; fi
  # Bootstrap a current Go if the distribution's version cannot auto-fetch toolchains.
  if ! command -v go >/dev/null || ! go version | python3 -c 'import re,sys; m=re.search(r"go(\d+)\.(\d+)",sys.stdin.read()); sys.exit(not m or tuple(map(int,m.groups())) < (1,21))'; then
    python3 "$repo_dir/install-go.py"
  fi
  mkdir -p "$HOME/.local/bin"
  while read -r binary module; do
    if ! command -v "$binary" >/dev/null; then
      GOBIN="$HOME/.local/bin" GOTOOLCHAIN=auto go install "$module"
    fi
  done <<'TOOLS'
gopls golang.org/x/tools/gopls@latest
goimports golang.org/x/tools/cmd/goimports@latest
errcheck github.com/kisielk/errcheck@latest
dlv github.com/go-delve/delve/cmd/dlv@latest
gotags github.com/jstemmer/gotags@latest
gomodifytags github.com/fatih/gomodifytags@latest
impl github.com/josharian/impl@latest
revive github.com/mgechev/revive@latest
TOOLS
fi
if has copilot; then
  if ! command -v node >/dev/null || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
    export NVM_DIR="$HOME/.local/share/dotfiles/nvm"
    if [ ! -s "$NVM_DIR/nvm.sh" ]; then
      mkdir -p "$(dirname "$NVM_DIR")"
      git clone --depth 1 --branch v0.40.7 https://github.com/nvm-sh/nvm.git "$NVM_DIR"
    fi
    set +u
    . "$NVM_DIR/nvm.sh"
    nvm install 22
    set -u
  fi
  if ! vim -Nu NONE -n -es -c 'if !has("patch-9.0.0185") | cquit | endif' -c 'qa!'; then
    packages vim
    vim -Nu NONE -n -es -c 'if !has("patch-9.0.0185") | cquit | endif' -c 'qa!' || {
      echo 'Copilot requires Vim 9.0.0185+. Update Vim in your template and rerun.' >&2; exit 1;
    }
  fi
  echo 'Copilot runtime ready. Run :Copilot setup in Vim to authenticate.'
fi
if has powerline || has vimpilot; then
  if [ "$platform" = Linux ]; then packages python3-venv; fi
fi
if has powerline; then
  venv="$HOME/.local/share/dotfiles/powerline"
  if [ ! -x "$venv/bin/python" ]; then python3 -m venv "$venv"; fi
  "$venv/bin/python" -m pip install 'powerline-shell==0.7.0'
  mkdir -p "$HOME/.local/bin"
  if [ ! -e "$HOME/.local/bin/powerline-shell" ] && [ ! -L "$HOME/.local/bin/powerline-shell" ]; then
    ln -s "$venv/bin/powerline-shell" "$HOME/.local/bin/powerline-shell"
  fi
fi
if has vimpilot; then
  if ! vim --version | grep -q '+python3'; then
    if [ "$platform" = Darwin ]; then packages vim; else packages vim-nox; fi
  fi
  # Use the interpreter matching Vim's embedded Python, not an arbitrary python3.
  python_info="$(mktemp)"
  trap 'rm -f "$python_info"' EXIT
  export DOTFILES_PYTHON_INFO="$python_info"
  vim -Nu NONE -n -es -c 'python3 import os,sys; open(os.environ["DOTFILES_PYTHON_INFO"], "w").write(os.path.join(sys.prefix,"bin","python3"))' -c 'qa!'
  vim_python="$(cat "$python_info")"
  [ -x "$vim_python" ] || { echo 'Cannot locate the Python interpreter embedded in Vim.' >&2; exit 1; }
  venv="$HOME/.local/share/dotfiles/vimpilot"
  "$vim_python" -m venv "$venv"
  "$venv/bin/python" -m pip install 'openai==0.28.1'
  "$venv/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' > "$HOME/.local/share/dotfiles/vimpilot-site.txt"
  echo 'VimPilot legacy SDK installed. Set OPENAI_API_KEY separately; model/API access is not validated.'
fi
if has colima && [ "$platform" = Darwin ]; then
  for tool in colima docker; do command -v "$tool" >/dev/null || packages "$tool"; done
  echo 'Colima installed. Run colima start when you want to start its VM.'
fi
echo 'Configured development tools installed.'
