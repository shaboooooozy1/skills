#!/usr/bin/env python3
"""
Tests for quick_validate.py - validate_skill function.
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

# Add the scripts directory to the path so we can import quick_validate
sys.path.insert(0, os.path.dirname(__file__))
from quick_validate import validate_skill


class TestValidateSkill(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_skill_md(self, content, skill_name="my-skill"):
        skill_dir = Path(self.tmpdir) / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    def _make_valid_skill(self, name="my-skill", description="Does something useful."):
        content = f"---\nname: {name}\ndescription: {description}\n---\n\n# Body"
        return self._write_skill_md(content, name)

    # ── missing / malformed file ────────────────────────────────────────────

    def test_missing_skill_md(self):
        skill_dir = Path(self.tmpdir) / "no-skill-md"
        skill_dir.mkdir()
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("SKILL.md", msg)

    def test_no_frontmatter(self):
        skill_dir = self._write_skill_md("# Just a heading\nNo frontmatter here.")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("frontmatter", msg.lower())

    def test_invalid_frontmatter_format(self):
        # Opening --- but no closing ---
        skill_dir = self._write_skill_md("---\nname: foo\ndescription: bar\n")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("frontmatter", msg.lower())

    def test_invalid_yaml_in_frontmatter(self):
        skill_dir = self._write_skill_md("---\n: : : bad yaml :::\n---\n")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)

    def test_frontmatter_not_a_dict(self):
        skill_dir = self._write_skill_md("---\n- item1\n- item2\n---\n")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("dictionary", msg.lower())

    # ── unexpected keys ─────────────────────────────────────────────────────

    def test_unexpected_key_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: my-skill\ndescription: Desc.\nauthor: Alice\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("author", msg)

    def test_allowed_keys_accepted(self):
        skill_dir = self._write_skill_md(
            "---\nname: my-skill\ndescription: Desc.\nlicense: MIT\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)

    # ── required fields ─────────────────────────────────────────────────────

    def test_missing_name(self):
        skill_dir = self._write_skill_md("---\ndescription: Desc.\n---\n")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("name", msg.lower())

    def test_missing_description(self):
        skill_dir = self._write_skill_md("---\nname: my-skill\n---\n")
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("description", msg.lower())

    # ── name validation ──────────────────────────────────────────────────────

    def test_name_not_a_string(self):
        skill_dir = self._write_skill_md(
            "---\nname: 42\ndescription: Desc.\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("string", msg.lower())

    def test_name_uppercase_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: MySkill\ndescription: Desc.\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("hyphen-case", msg.lower())

    def test_name_with_underscore_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: my_skill\ndescription: Desc.\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)

    def test_name_starting_with_hyphen_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: -my-skill\ndescription: Desc.\n---\n", "-my-skill"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)

    def test_name_ending_with_hyphen_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: my-skill-\ndescription: Desc.\n---\n", "my-skill-"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)

    def test_name_consecutive_hyphens_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: my--skill\ndescription: Desc.\n---\n", "my--skill"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)

    def test_name_too_long_rejected(self):
        long_name = "a" * 65
        skill_dir = self._write_skill_md(
            f"---\nname: {long_name}\ndescription: Desc.\n---\n", long_name
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("long", msg.lower())

    def test_name_max_length_accepted(self):
        max_name = "a" * 64
        skill_dir = self._write_skill_md(
            f"---\nname: {max_name}\ndescription: Desc.\n---\n", max_name
        )
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)

    def test_name_with_digits_accepted(self):
        skill_dir = self._make_valid_skill(name="skill123")
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)

    # ── description validation ───────────────────────────────────────────────

    def test_description_not_a_string(self):
        skill_dir = self._write_skill_md(
            "---\nname: my-skill\ndescription: 99\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("string", msg.lower())

    def test_description_with_angle_brackets_rejected(self):
        skill_dir = self._write_skill_md(
            "---\nname: my-skill\ndescription: Use <tool> to do things.\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("angle bracket", msg.lower())

    def test_description_too_long_rejected(self):
        long_desc = "x" * 1025
        skill_dir = self._write_skill_md(
            f"---\nname: my-skill\ndescription: {long_desc}\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertFalse(valid)
        self.assertIn("long", msg.lower())

    def test_description_max_length_accepted(self):
        max_desc = "x" * 1024
        skill_dir = self._write_skill_md(
            f"---\nname: my-skill\ndescription: {max_desc}\n---\n"
        )
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)

    # ── valid skill ──────────────────────────────────────────────────────────

    def test_valid_skill(self):
        skill_dir = self._make_valid_skill()
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)
        self.assertIn("valid", msg.lower())

    def test_valid_skill_with_all_allowed_fields(self):
        content = (
            "---\n"
            "name: full-skill\n"
            "description: A complete skill.\n"
            "license: Apache-2.0\n"
            "allowed-tools:\n"
            "  - bash\n"
            "metadata:\n"
            "  version: 1.0\n"
            "---\n\n# Full Skill\n"
        )
        skill_dir = self._write_skill_md(content, "full-skill")
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)

    def test_valid_skill_with_hyphenated_name(self):
        skill_dir = self._make_valid_skill(name="web-artifact-builder")
        valid, msg = validate_skill(skill_dir)
        self.assertTrue(valid, msg)


if __name__ == "__main__":
    unittest.main()
