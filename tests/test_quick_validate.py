"""
Tests for skill-creator/scripts/quick_validate.py
"""

import pytest
from pathlib import Path

from quick_validate import validate_skill


def make_skill(tmp_path, content, skill_name="my-skill"):
    """Helper: write a SKILL.md and return the skill directory path."""
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


VALID_SKILL_MD = """---
name: my-skill
description: A test skill that does things.
---

# My Skill

Some content here.
"""


class TestValidateSkill:
    # ---- happy-path ----

    def test_valid_skill_returns_true(self, tmp_path):
        skill_dir = make_skill(tmp_path, VALID_SKILL_MD)
        valid, msg = validate_skill(skill_dir)
        assert valid is True
        assert "valid" in msg.lower()

    def test_valid_skill_with_optional_license(self, tmp_path):
        content = """---
name: my-skill
description: A test skill.
license: Apache-2.0
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is True

    def test_valid_skill_with_allowed_tools(self, tmp_path):
        content = """---
name: my-skill
description: A test skill.
allowed-tools:
  - bash
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is True

    def test_valid_skill_with_metadata(self, tmp_path):
        content = """---
name: my-skill
description: A test skill.
metadata:
  author: someone
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is True

    # ---- missing SKILL.md ----

    def test_missing_skill_md(self, tmp_path):
        skill_dir = tmp_path / "no-skill"
        skill_dir.mkdir()
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "SKILL.md" in msg

    # ---- frontmatter issues ----

    def test_no_frontmatter(self, tmp_path):
        skill_dir = make_skill(tmp_path, "# Just a heading\nNo frontmatter here.\n")
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_invalid_frontmatter_format(self, tmp_path):
        # Dashes present but no closing ---
        skill_dir = make_skill(tmp_path, "---\nname: my-skill\n")
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_missing_name_field(self, tmp_path):
        content = """---
description: A skill without a name.
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "name" in msg.lower()

    def test_missing_description_field(self, tmp_path):
        content = """---
name: my-skill
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "description" in msg.lower()

    def test_unexpected_frontmatter_key(self, tmp_path):
        content = """---
name: my-skill
description: A skill.
unknown-key: value
---
"""
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "unknown-key" in msg

    # ---- name validation ----

    def test_name_with_uppercase_rejected(self, tmp_path):
        content = "---\nname: My-Skill\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_name_with_leading_hyphen_rejected(self, tmp_path):
        content = "---\nname: -my-skill\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_name_with_trailing_hyphen_rejected(self, tmp_path):
        content = "---\nname: my-skill-\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_name_with_consecutive_hyphens_rejected(self, tmp_path):
        content = "---\nname: my--skill\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_name_too_long_rejected(self, tmp_path):
        long_name = "a" * 65
        content = f"---\nname: {long_name}\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content, skill_name="long-name")
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "long" in msg.lower()

    def test_name_exactly_64_chars_accepted(self, tmp_path):
        name = "a" * 64
        content = f"---\nname: {name}\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content, skill_name="exact-len")
        valid, msg = validate_skill(skill_dir)
        assert valid is True

    def test_name_with_digits_accepted(self, tmp_path):
        content = "---\nname: m365-email\ndescription: A skill.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is True

    # ---- description validation ----

    def test_description_with_angle_brackets_rejected(self, tmp_path):
        content = "---\nname: my-skill\ndescription: A <bad> description.\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False
        assert "angle" in msg.lower() or "<" in msg

    def test_description_too_long_rejected(self, tmp_path):
        long_desc = "a" * 1025
        content = f"---\nname: my-skill\ndescription: {long_desc}\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is False

    def test_description_exactly_1024_chars_accepted(self, tmp_path):
        desc = "a" * 1024
        content = f"---\nname: my-skill\ndescription: {desc}\n---\n"
        skill_dir = make_skill(tmp_path, content)
        valid, msg = validate_skill(skill_dir)
        assert valid is True
