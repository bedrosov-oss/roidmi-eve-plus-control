from pathlib import Path
import ast, hashlib, json, re, zipfile, datetime

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
DIST = ROOT / "dist"
RELEASES = ROOT / "releases"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

source = (APP / "roidmi_control.py").read_text(encoding="utf-8")
ast.parse(source)
m = re.search(r'CURRENT_VERSION\s*=\s*"([^"]+)"', source)
if not m or m.group(1) != VERSION:
    raise SystemExit("VERSION mismatch")

for forbidden in [
    APP / "AUTO_CONFIG.json",
    APP / "CLOUD_SESSION.json",
    APP / "PRIVATE_NOTIFY_CONFIG.json",
    APP / "ROOM_PROFILES.json",
    APP / "USER_PROFILE.json",
]:
    if forbidden.exists():
        raise SystemExit(f"Sensitive file present: {forbidden}")

DIST.mkdir(exist_ok=True)
RELEASES.mkdir(exist_ok=True)
out = DIST / "ROIDMI_EVE_Plus_Control_Windows_latest.zip"

skip_dirs = {".venv", "__pycache__", "backups", "map_history", "updates", "logs"}
skip_names = {
    "AUTO_CONFIG.json", "CLOUD_SESSION.json", "PRIVATE_NOTIFY_CONFIG.json",
    "ROOM_PROFILES.json", "USER_PROFILE.json", "history.sqlite3"
}

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(APP.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(APP)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if p.name in skip_names:
            continue
        z.write(p, arcname=rel)

sha = hashlib.sha256(out.read_bytes()).hexdigest()
manifest = {
    "version": VERSION,
    "url": (
        "https://raw.githubusercontent.com/bedrosov-oss/"
        "roidmi-eve-plus-control/main/dist/"
        "ROIDMI_EVE_Plus_Control_Windows_latest.zip"
    ),
    "sha256": sha,
    "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "notes": f"ROIDMI EVE Plus Control v{VERSION}",
}
(RELEASES / "latest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8"
)
print(out)
print(sha)
