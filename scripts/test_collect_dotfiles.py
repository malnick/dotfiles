"""Run with: python3 -m unittest discover -s scripts -p 'test_*.py'.

Package managers are mocked: these tests never install system packages.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import runpy


COLLECTOR = Path(__file__).with_name("collect-dotfiles.py")


class DotfilesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / ".zshrc").write_text("export EDITOR=vim\n")
        (self.source / ".vim").mkdir()
        (self.source / ".vim/vimrc").write_text("set number\n")
        (self.source / ".vimrc").symlink_to(self.source / ".vim/vimrc")
        (self.source / ".vim/cache").mkdir()
        (self.source / ".vim/cache/junk").touch()
        (self.source / ".vim/loop").symlink_to(self.source / ".vim")
        (self.source / ".oh-my-zsh/.git").mkdir(parents=True)
        (self.source / ".oh-my-zsh/oh-my-zsh.sh").write_text("# fixture\n")
        self.repo = self.root / "dotfiles repo"
        subprocess.run(["python3", str(COLLECTOR), str(self.repo), "--home", str(self.source)],
                       check=True, capture_output=True)
        self.home = self.root / "target"
        self.home.mkdir()
        (self.home / ".zshrc").write_text("original\n")
        self.log = self.root / "packages.log"
        mockbin = self.root / "bin"
        mockbin.mkdir()
        apt = mockbin / "apt-get"
        apt.write_text('#!/bin/sh\nprintf "apt %s\\n" "$*" >> "$TEST_LOG"\n')
        apt.chmod(0o700)
        hooks = self.root / "hooks.sh"
        hooks.write_text('''
uname() { printf '%s\\n' "$TEST_PLATFORM"; }
id() { printf '%s\\n' "${TEST_UID:-1000}"; }
command() {
  if [ "$1" = -v ]; then
    case "$2" in
      tmux) return 1 ;;
      git|vim|zsh|curl|sudo|apt-get) return 0 ;;
      brew) [ "${TEST_NO_BREW:-0}" != 1 ]; return $? ;;
    esac
  fi
  builtin command "$@"
}
brew() { printf 'brew %s\\n' "$*" >> "$TEST_LOG"; }
sudo() { shift; "$@"; }
''')
        self.env = dict(os.environ, HOME=str(self.home), BASH_ENV=str(hooks),
                        TEST_LOG=str(self.log), TEST_PLATFORM="Linux",
                        PATH=str(mockbin) + os.pathsep + os.environ["PATH"])

    def run_make(self, target="install", check=True):
        return subprocess.run(["make", target], cwd=self.repo, env=self.env,
                              check=check, capture_output=True, text=True)

    def test_copy_and_repeatable_links(self):
        self.assertEqual((self.repo / "home/.vimrc").read_text(), "set number\n")
        for rel in (".vim/cache", ".vim/loop", ".oh-my-zsh/.git"):
            self.assertFalse((self.repo / "home" / rel).exists())
        self.run_make("link")
        self.run_make("link")
        backups = list(self.home.glob(".dotfiles-backup.*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / ".zshrc").read_text(), "original\n")
        self.assertTrue((self.home / ".zshrc").is_symlink())
        self.assertFalse(self.log.exists())
        self.assertEqual((self.source / ".zshrc").read_text(), "export EDITOR=vim\n")

    def test_ubuntu_installs_missing_packages(self):
        self.run_make()
        self.assertEqual(self.log.read_text(), "apt update\napt install -y tmux ca-certificates\n")
        self.assertTrue((self.home / ".zshrc").is_symlink())

    def test_macos_installs_missing_packages(self):
        self.env["TEST_PLATFORM"] = "Darwin"
        self.run_make()
        self.assertEqual(self.log.read_text(), "brew install tmux\n")
        self.assertTrue((self.home / ".zshrc").is_symlink())

    def test_ubuntu_root_install(self):
        self.env["TEST_UID"] = "0"
        self.run_make()
        self.assertIn("apt install -y tmux", self.log.read_text())

    def test_go_profile_installs_tools_in_user_directory(self):
        (self.repo / "tools.txt").write_text("go\n")
        with Path(self.env["BASH_ENV"]).open("a") as output:
            output.write('''
command() {
  if [ "$1" = -v ]; then
    case "$2" in
      go|cc) return 0 ;;
      gopls|goimports|errcheck|dlv|gotags|gomodifytags|impl|revive) return 1 ;;
    esac
  fi
  builtin command "$@"
}
go() {
  if [ "$1" = version ]; then echo 'go version go1.24.0 linux/amd64';
  else printf '%s %s\\n' "$GOBIN" "$*" >> "$TEST_LOG"; fi
}
''')
        self.run_make("tools")
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 8)
        self.assertTrue(all(str(self.home / ".local/bin") in line for line in lines))

    def test_missing_brew_fails_before_linking(self):
        self.env.update(TEST_PLATFORM="Darwin", TEST_NO_BREW="1")
        result = self.run_make(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Install Homebrew", result.stderr)
        self.assertEqual((self.home / ".zshrc").read_text(), "original\n")

    def test_refuses_existing_destination(self):
        result = subprocess.run(["python3", str(COLLECTOR), str(self.repo)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_sanitizes_credentials_and_generates_tool_profiles(self):
        namespace = runpy.run_path(str(COLLECTOR))
        original = 'export GITHUB_TOKEN="example-sensitive-value"\nexport EDITOR=vim\n'
        sanitized = namespace["sanitize"](original)
        self.assertNotIn("example-sensitive-value", sanitized)
        self.assertIn("export EDITOR=vim", sanitized)
        home = self.repo / "home"
        (home / ".zshrc").write_text('powerline-shell\nexport DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"\n')
        (home / ".zprofile").write_text('eval "$(/opt/homebrew/bin/brew shellenv)"\n')
        for plugin in ("bundle/vim-go", "bundle/vim-copilot", "vim-pilot"):
            (home / ".vim" / plugin).mkdir(parents=True)
        selected = [".zshrc", ".zprofile", ".vimrc"]
        namespace["customize"](self.repo, selected)
        self.assertEqual(set((self.repo / "tools.txt").read_text().split()),
                         {"go", "copilot", "vimpilot", "powerline", "colima"})
        self.assertIn('"$OSTYPE" == darwin*', (home / ".zshrc").read_text())
        self.assertIn('[ -x /opt/homebrew/bin/brew ]', (home / ".zprofile").read_text())
        self.assertIn("set -g prefix C-a", (home / ".tmux.conf").read_text())
        self.assertIn("bind -T copy-mode-vi y", (home / ".tmux.conf").read_text())
        for script in ("install.sh", "install-dev-tools.sh"):
            subprocess.run(["bash", "-n", str(self.repo / script)], check=True)

    def test_mac_colima_profile_does_not_run_on_ubuntu(self):
        (self.repo / "tools.txt").write_text("colima\n")
        self.run_make("tools")
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
