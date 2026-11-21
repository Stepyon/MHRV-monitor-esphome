"""Turn GitHub-generated release notes into short ESPHome OTA release summaries.

The complete notes remain available through the manifest's release_url.
We deliberately keep the on-device manifest small for ESP8266 memory usage.
"""

import re

MAX_RELEASE_SUMMARY_LENGTH = 700
MAX_RELEASE_ITEMS = 6


def summarize_release_notes(markdown: str, version: str) -> str:
    """Extract meaningful changelog bullets for Home Assistant's update dialog."""
    items: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.lower().startswith(("## new contributors", "**full changelog**", "## full changelog")):
            break
        if not line.startswith(("* ", "- ")):
            continue
        item = line[2:].strip()
        if not item or item.lower().startswith(("full changelog", "new contributors")):
            continue

        # GitHub automatically generates entries like:
        # * Better polling by @author in https://github.com/owner/repo/pull/6
        item = re.sub(
            r"\s+by\s+@[\w-]+\s+in\s+https?://github\.com/[^\s]+/pull/(\d+)",
            r" (#\1)",
            item,
            flags=re.IGNORECASE,
        )
        # Strip Markdown link formatting, preserving the human-readable title.
        item = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", item)
        item = re.sub(r"\s+by\s+@[\w-]+$", "", item)
        item = re.sub(r"\s+in\s+https?://\S+$", "", item)
        if len(item) > 170:
            item = item[:167].rstrip() + "..."
        items.append(f"- {item}")
        if len(items) >= MAX_RELEASE_ITEMS:
            break

    heading = f"What's new in v{version}:"
    if not items:
        return f"MHRV Monitor firmware v{version}. See the linked GitHub release for changes."

    summary = heading
    for item in items:
        candidate = summary + "\n" + item
        if len(candidate) > MAX_RELEASE_SUMMARY_LENGTH:
            break
        summary = candidate
    return summary
