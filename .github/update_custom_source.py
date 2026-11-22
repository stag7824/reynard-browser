"""Build a SideStore/AltStore source listing the custom Reynard releases of this fork.

Usage: update_custom_source.py <releases.jsonl> <output.json>
The releases file holds one GitHub release object per line (gh api --paginate --jq '.[]').
"""

import json
import os
import sys
from pathlib import Path

TAG_PREFIX = "custom-"
ASSET_NAME = "Reynard.ipa"


def parse_tag(tag: str) -> tuple[str, str] | None:
    # Tags look like custom-<version>-<sha7>; the app's CFBundleVersion is that sha.
    if not tag.startswith(TAG_PREFIX):
        return None
    version, _, build = tag[len(TAG_PREFIX):].rpartition("-")
    if not version or not build:
        return None
    return version, build


def main() -> None:
    releases_path, output_path = Path(sys.argv[1]), Path(sys.argv[2])
    repo = os.environ.get("REPO", "")
    template = json.loads(Path(__file__).with_name("source.json").read_text(encoding="utf-8"))

    releases = [json.loads(line) for line in releases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    releases.sort(key=lambda release: release.get("created_at", ""), reverse=True)

    versions = []
    for release in releases:
        if release.get("draft"):
            continue
        parsed = parse_tag(release.get("tag_name", ""))
        if parsed is None:
            continue
        version, build = parsed
        for asset in release.get("assets", []):
            if asset.get("name") != ASSET_NAME:
                continue
            versions.append(
                {
                    "version": version,
                    "buildVersion": build,
                    "date": release["created_at"],
                    "localizedDescription": (release.get("body") or "").replace("`", ""),
                    "downloadURL": asset["browser_download_url"],
                    "size": asset["size"],
                }
            )

    owner = repo.split("/")[0] if repo else "custom"
    template["name"] = "Reynard Browser (Custom Builds)"
    template["identifier"] = f"io.github.{owner}.reynard-custom"
    template["website"] = f"https://github.com/{repo}" if repo else template.get("website")
    template["subtitle"] = "Custom Reynard builds with a customizable toolbar"

    app = template["apps"][0]
    app["name"] = "Reynard (Custom)"
    app["versions"] = versions

    output = json.dumps(template, indent=2)
    json.loads(output)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {len(versions)} version(s) to {output_path}")


if __name__ == "__main__":
    main()
