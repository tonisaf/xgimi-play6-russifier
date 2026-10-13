"""Restore ignored binary build inputs from a checksum-verified matching release."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE_HASHES = {
    "1.13.0": "3f5c4a9cfdc79403d9b746ce0a2de0d0c7965450a96319c6921bb519227fbd68",
    "1.14.0": "d9b43e6cd304b7115185d1fa1634a6d680b8c5dd375a92b09c91ce27d20820bf",
    "1.15.0": "844260cf930dfba694323c937c9a6a944e91d40c49feefe3ddc0e64c3f76dea0",
}

def main():
    archive = Path(sys.argv[1])
    manifest = json.loads((ROOT / "russifier/manifest.json").read_text(encoding="utf-8"))
    expected=RELEASE_HASHES.get(manifest['version'])
    if expected is None or hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
        raise SystemExit("Release ZIP SHA256 mismatch or release version is not registered")
    with zipfile.ZipFile(archive) as source:
        prefix = "Beam-Russifier-Play6/"
        archived_manifest=json.loads(source.read(prefix+'manifest.json'))
        if archived_manifest['version']!=manifest['version'] or archived_manifest['files']!=manifest['files']:
            raise SystemExit("Archive does not match the current manifest")
        inputs = []
        for name in source.namelist():
            if not name.startswith(prefix):
                continue
            relative = Path(name[len(prefix):])
            if relative.is_absolute() or ".." in relative.parts:
                raise SystemExit("Invalid ZIP member")
            if relative.parts[0] in ("runtime", "tools", "boot-helper") or (relative.parts[0] == "payload" and relative.suffix == ".apk"):
                inputs.append((relative, source.read(name)))
        for relative, data in inputs:
            if relative.parts[0] == "payload":
                if hashlib.sha256(data).hexdigest() != manifest["files"][relative.name]:
                    raise SystemExit("Payload hash mismatch: " + relative.name)
        for relative, data in inputs:
            target = ROOT / "russifier" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(data).digest():
                continue
            target.write_bytes(data)
    print("Restored", len(inputs), "verified release inputs")

if __name__ == "__main__":
    main()
