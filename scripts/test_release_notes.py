"""Tests for compact ESPHome OTA changelog summaries."""

import unittest

from release_notes import summarize_release_notes


class ReleaseNotesTests(unittest.TestCase):
    def test_github_pull_request_entry(self):
        original = (
            "## What's Changed\n"
            "* Synchronize MVHR efficiency readings by @stepyon "
            "in https://github.com/Stepyon/MHRV-monitor-esphome/pull/6\n"
            "\n**Full Changelog**: https://github.com/example/compare/v1...v2\n"
        )
        self.assertEqual(
            summarize_release_notes(original, "0.3.0"),
            "What's new in v0.3.0:\n- Synchronize MVHR efficiency readings (#6)",
        )

    def test_contributor_section_not_included(self):
        original = (
            "## What's Changed\n"
            "* Improve OTA documentation by @author in https://github.com/o/r/pull/7\n"
            "## New Contributors\n"
            "* @author made their first contribution in https://github.com/o/r/pull/7\n"
        )
        text = summarize_release_notes(original, "1.0.0")
        self.assertIn("Improve OTA documentation (#7)", text)
        self.assertNotIn("first contribution", text)

    def test_fallback_without_changes(self):
        self.assertIn(
            "See the linked GitHub release",
            summarize_release_notes("## No changes", "0.5.0"),
        )

    def test_removes_markdown_link_without_losing_title(self):
        text = summarize_release_notes(
            "* [Fix sensor mapping](https://github.com/o/r/pull/8)", "0.4.0"
        )
        self.assertIn("- Fix sensor mapping", text)
        self.assertNotIn("https://", text)

    def test_limits_summary_length_and_number_of_entries(self):
        notes = "\n".join(f"* Detailed fix {i} " + ("x" * 210) for i in range(12))
        text = summarize_release_notes(notes, "3.0.0")
        self.assertLessEqual(len(text), 700)
        self.assertLessEqual(text.count("\n- "), 6)


if __name__ == "__main__":
    unittest.main()
