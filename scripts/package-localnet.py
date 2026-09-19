#!/usr/bin/env python3
"""Package the committed LocalNet configuration and all of its bind mounts."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile


def run(*args, cwd):
    return subprocess.check_output(args, cwd=cwd)


def compose(root):
    return json.loads(run(
        "docker", "compose", "--project-name", "cn-localnet", "-f",
        str(root / "infra/compose.yaml"), "config", "--format", "json", cwd=root,
    ))


def relocate(value, old, new):
    if isinstance(value, str):
        return value.replace(str(old), str(new))
    if isinstance(value, list):
        return [relocate(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: relocate(item, old, new) for key, item in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Bundle version, for example v0.1.0")
    parser.add_argument("--ref", default="HEAD", help="Git commit or tag to package")
    parser.add_argument("--output", type=Path, default=Path(".release"))
    args = parser.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", args.version):
        parser.error("version must have the form v0.1.0 or v0.1.0-rc.1")

    root = Path(__file__).resolve().parent.parent
    commit = run("git", "rev-parse", f"{args.ref}^{{commit}}", cwd=root).decode().strip()
    source_archive = run("git", "archive", commit, cwd=root)
    with tempfile.TemporaryDirectory(prefix="cn-localnet-package-") as temporary:
        snapshot = (Path(temporary) / "source").resolve()
        snapshot.mkdir()
        with tarfile.open(fileobj=io.BytesIO(source_archive)) as archive:
            archive.extractall(snapshot, filter="data")
        config = compose(snapshot)
        selected = {p for p in (snapshot / "infra").rglob("*") if p.is_file()}
        selected.update(snapshot / name for name in ("LICENSE", "terms.md"))
        for service in config["services"].values():
            for mount in service.get("volumes", []):
                if mount["type"] != "bind":
                    continue
                path = Path(mount["source"])
                if not path.exists() or not path.resolve().is_relative_to(snapshot):
                    raise ValueError(f"Missing or external bind mount: {path}")
                selected.update(
                    p for p in (path.rglob("*") if path.is_dir() else [path]) if p.is_file()
                )

        files = {}
        for path in sorted(selected):
            if path.is_symlink():
                raise ValueError(f"Symlinks are not supported in the bundle: {path}")
            relative = path.relative_to(snapshot).as_posix()
            files[relative] = (path.read_bytes(), path.stat().st_mode & 0o777)
        manifest = {
            "version": args.version,
            "source_repository": "https://github.com/raynaudoe/cn-quickstart",
            "source_commit": commit,
            "images": sorted({service["image"] for service in config["services"].values()}),
            "files": {
                path: {"sha256": hashlib.sha256(data).hexdigest(), "mode": oct(mode)}
                for path, (data, mode) in files.items()
            },
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        files["manifest.json"] = (manifest_bytes, 0o644)
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for path, (data, mode) in sorted(files.items()):
                    info = tarfile.TarInfo(path)
                    info.size, info.mode = len(data), mode
                    archive.addfile(info, io.BytesIO(data))
        bundle = buffer.getvalue()

        extracted = (Path(temporary) / "extracted").resolve()
        extracted.mkdir()
        with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as archive:
            archive.extractall(extracted, filter="data")
        if relocate(compose(extracted), extracted, snapshot) != config:
            raise ValueError("The packaged Compose configuration differs from the source")
        for path, (data, mode) in files.items():
            actual = extracted / path
            if actual.read_bytes() != data or actual.stat().st_mode & 0o777 != mode:
                raise ValueError(f"The package did not preserve {path}")

    args.output.mkdir(parents=True, exist_ok=True)
    archive_name = f"cn-localnet-{args.version}.tar.gz"
    manifest_name = f"cn-localnet-{args.version}.manifest.json"
    artifacts = {archive_name: bundle, manifest_name: manifest_bytes}
    for name, data in artifacts.items():
        (args.output / name).write_bytes(data)
    (args.output / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in artifacts.items()
    ))
    print(f"Verified {len(files)} files from {commit}; bundle: {len(bundle)} bytes")
    print(args.output / archive_name)


if __name__ == "__main__":
    main()
