"""Offline local-link, required-artifact and common AWS-key-pattern checks."""

import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    issues = []
    checked = 0
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            target = unquote(target.split("#")[0])
            checked += 1
            if not (path.parent / target).exists():
                issues.append(f"Missing link: {path.relative_to(ROOT)} -> {target}")
    for name in ["architecture", "cicd", "git-workflow"]:
        for suffix in ["png", "svg", "dot"]:
            path = ROOT / "docs" / f"{name}.{suffix}"
            if not path.is_file() or path.stat().st_size == 0:
                issues.append(f"Missing diagram: {path}")
    patterns = [
        re.compile(r"(?:AK" + r"IA|AS" + r"IA)[A-Z0-9]{16}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ]
    scanned = 0
    for base in [ROOT / "src", ROOT / "scripts", ROOT / "frontend", ROOT / ".github"]:
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                text = path.read_text(errors="replace")
                scanned += 1
                if any(pattern.search(text) for pattern in patterns):
                    issues.append(f"Credential-like pattern: {path.relative_to(ROOT)}")
    result = {
        "status": "FAIL" if issues else "PASS",
        "local_links_checked": checked,
        "source_files_scanned": scanned,
        "issues": issues,
        "scope": "Local links and common AWS ID/private-key patterns only; not a full secret audit",
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(issues))


if __name__ == "__main__":
    main()
