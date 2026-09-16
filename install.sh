#!/usr/bin/env bash
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
  *) printf 'Usage: %s [--links-only]\n' "$0" >&2; exit 2 ;;
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
        printf 'Install Homebrew from https://brew.sh, then rerun make install. Missing tools: %s\n' "${missing[*]}" >&2
        exit 1
      fi
      brew install "${missing[@]}"
    elif [ "$platform" = Linux ] && command -v apt-get >/dev/null 2>&1; then
      as_root=()
      if [ "$(id -u)" -ne 0 ]; then
        if ! command -v sudo >/dev/null 2>&1 || ! sudo -n true; then
          printf 'Installing tools requires root or passwordless sudo. Ask your template admin to preinstall: %s\n' "${missing[*]}" >&2
          exit 1
        fi
        as_root=(sudo -n)
      fi
      ${as_root[@]+"${as_root[@]}"} apt-get update
      ${as_root[@]+"${as_root[@]}"} env DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}" ca-certificates
    else
      printf 'Install these tools with your package manager, then rerun: %s\n' "${missing[*]}" >&2
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
      printf 'Unsafe manifest path: %s\n' "$rel" >&2; exit 1 ;;
  esac
  if [ ! -e "$repo_dir/home/$rel" ]; then
    printf 'Missing configuration: %s\n' "$rel" >&2; exit 1
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
  printf 'Linked %s\n' "$rel"
done < "$repo_dir/manifest.txt"
if [ -n "$backup_dir" ]; then
  printf 'Previous configuration saved in %s\n' "$backup_dir"
fi
printf 'Installed. Run exec zsh -l to enter your configured shell.\n'
