"""
tools/download_tectonic.py
Download the Tectonic LaTeX engine binary for this platform.
Run from the repo root:  python tools/download_tectonic.py
"""
import sys
import platform
import urllib.request
import zipfile
import os

VERSION = "0.17.0"
OUT_DIR = os.path.join("tools", "bin")
OUT_BIN = os.path.join(OUT_DIR, "tectonic.exe" if sys.platform == "win32" else "tectonic")

ASSETS = {
    ("win32",   "amd64"): f"tectonic-{VERSION}-x86_64-pc-windows-msvc.zip",
    ("darwin",  "arm64"): f"tectonic-{VERSION}-aarch64-apple-darwin.tar.gz",
    ("darwin",  "x86_64"): f"tectonic-{VERSION}-x86_64-apple-darwin.tar.gz",
    ("linux",   "x86_64"): f"tectonic-{VERSION}-x86_64-unknown-linux-musl.tar.gz",
}

BASE_URL = (
    f"https://github.com/tectonic-typesetting/tectonic/releases/download/"
    f"tectonic%40{VERSION}/"
)


def main():
    plat = sys.platform
    arch = platform.machine().lower()
    if arch == "amd64":
        arch = "amd64"  # windows reports amd64

    key = (plat, arch)
    if key not in ASSETS:
        sys.exit(f"No Tectonic binary for platform {plat}/{arch}. Install manually.")

    asset = ASSETS[key]
    url = BASE_URL + asset
    archive = os.path.join(OUT_DIR, asset)

    os.makedirs(OUT_DIR, exist_ok=True)

    if os.path.exists(OUT_BIN):
        print(f"Tectonic already present at {OUT_BIN}")
        return

    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, archive)

    print(f"Extracting to {OUT_DIR}/ ...")
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            z.extractall(OUT_DIR)
    else:
        import tarfile
        with tarfile.open(archive) as t:
            t.extractall(OUT_DIR)

    os.remove(archive)

    if not sys.platform == "win32":
        os.chmod(OUT_BIN, 0o755)

    print(f"Tectonic ready: {OUT_BIN}")


if __name__ == "__main__":
    main()
