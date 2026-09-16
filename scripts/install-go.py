#!/usr/bin/env python3
"""Install an official Go archive into the user's private runtime directory."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import urllib.request


def main():
    system = {"Darwin": "darwin", "Linux": "linux"}[platform.system()]
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64", "AMD64": "amd64"}[platform.machine()]
    with urllib.request.urlopen("https://go.dev/dl/?mode=json", timeout=60) as response:
        releases = json.load(response)
    release = next(item for item in releases if item["stable"])
    archive = next(item for item in release["files"] if item["os"] == system and item["arch"] == arch and item["kind"] == "archive")
    parent = Path.home() / ".local/share/dotfiles/runtimes"
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / "go"
    if target.exists() or target.is_symlink():
        raise SystemExit("Existing managed Go runtime is unusable; move it aside and rerun: " + str(target))
    with tempfile.TemporaryDirectory(dir=parent) as temporary:
        temporary = Path(temporary)
        download = temporary / "go.tar.gz"
        digest = hashlib.sha256()
        with urllib.request.urlopen("https://go.dev/dl/" + archive["filename"], timeout=60) as response, download.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != archive["sha256"]:
            raise SystemExit("Go archive checksum mismatch")
        subprocess.run(["tar", "-xzf", str(download), "-C", str(temporary)], check=True)
        os.rename(temporary / "go", target)
    print("Installed", release["version"], "in", target)


if __name__ == "__main__":
    main()
