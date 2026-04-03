#!/usr/bin/env python3
"""Tests for quick_validate.py"""

import unittest
import tempfile
from pathlib import Path

from quick_validate import validate_skill


class TestValidateSkill(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _write_skill_md(self, content):
        skill_md = Path(self.tmpdir) / "SKILL.md"
        skill_md.write_text(content)
        return self.tmpdir

    # --- Missing / malformed SKILL.md ---

    def test_missing_skill_md(self):
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("SKILL.md not found", msg)

    def test_no_frontmatter(self):
        self._write_skill_md("# Just a heading\nNo frontmatter here.")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("No YAML frontmatter found", msg)

    def test_invalid_frontmatter_format(self):
        self._write_skill_md("---\nname: foo\n")  # missing closing ---
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Invalid frontmatter format", msg)

    def test_frontmatter_not_a_dict(self):
        self._write_skill_md("---\n- item1\n- item2\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("must be a YAML dictionary", msg)

    def test_invalid_yaml(self):
        self._write_skill_md("---\nname: :\n  bad:: yaml\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Invalid YAML", msg)

    # --- Unexpected keys ---

    def test_unexpected_keys(self):
        self._write_skill_md(
            "---\nname: my-skill\ndescription: A skill\nfoo: bar\n---\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Unexpected key(s)", msg)
        self.assertIn("foo", msg)

    # --- Required fields ---

    def test_missing_name(self):
        self._write_skill_md("---\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Missing 'name'", msg)

    def test_missing_description(self):
        self._write_skill_md("---\nname: my-skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Missing 'description'", msg)

    # --- Name validation ---

    def test_name_not_string(self):
        self._write_skill_md("---\nname: 123\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Name must be a string", msg)

    def test_name_uppercase_rejected(self):
        self._write_skill_md("---\nname: MySkill\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("hyphen-case", msg)

    def test_name_with_spaces_rejected(self):
        self._write_skill_md("---\nname: my skill\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("hyphen-case", msg)

    def test_name_starts_with_hyphen(self):
        self._write_skill_md("---\nname: '-my-skill'\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("cannot start/end with hyphen", msg)

    def test_name_ends_with_hyphen(self):
        self._write_skill_md("---\nname: my-skill-\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("cannot start/end with hyphen", msg)

    def test_name_consecutive_hyphens(self):
        self._write_skill_md("---\nname: my--skill\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("consecutive hyphens", msg)

    def test_name_too_long(self):
        long_name = "a" * 65
        self._write_skill_md(f"---\nname: {long_name}\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("too long", msg)

    def test_name_at_max_length(self):
        max_name = "a" * 64
        self._write_skill_md(f"---\nname: {max_name}\ndescription: A skill\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertTrue(valid)

    # --- Description validation ---

    def test_description_not_string(self):
        self._write_skill_md("---\nname: my-skill\ndescription: 123\n---\n")
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("Description must be a string", msg)

    def test_description_with_angle_brackets(self):
        self._write_skill_md(
            "---\nname: my-skill\ndescription: Uses <html> tags\n---\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("angle brackets", msg)

    def test_description_too_long(self):
        long_desc = "a" * 1025
        self._write_skill_md(
            f"---\nname: my-skill\ndescription: {long_desc}\n---\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertFalse(valid)
        self.assertIn("too long", msg)

    # --- Valid skills ---

    def test_valid_minimal_skill(self):
        self._write_skill_md(
            "---\nname: my-skill\ndescription: A valid skill\n---\n# My Skill\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertTrue(valid)
        self.assertIn("valid", msg.lower())

    def test_valid_skill_with_all_allowed_keys(self):
        self._write_skill_md(
            "---\n"
            "name: my-skill\n"
            "description: A valid skill\n"
            "license: MIT\n"
            "allowed-tools:\n"
            "  - Bash\n"
            "metadata:\n"
            "  author: test\n"
            "---\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertTrue(valid)

    def test_valid_name_with_digits(self):
        self._write_skill_md(
            "---\nname: skill-v2\ndescription: Version 2\n---\n"
        )
        valid, msg = validate_skill(self.tmpdir)
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
