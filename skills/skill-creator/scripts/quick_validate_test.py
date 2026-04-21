import unittest
import tempfile
from pathlib import Path

from quick_validate import validate_skill


class TestValidateSkill(unittest.TestCase):

    def _make_skill(self, tmp_dir, content):
        """Write SKILL.md with given content and return the skill directory path."""
        skill_dir = Path(tmp_dir) / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
        return skill_dir

    # ------------------------------------------------------------------ happy path

    def test_valid_minimal_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill\ndescription: Does something useful.\n---\n\n# My Skill\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertTrue(valid, msg)

    def test_valid_skill_with_all_allowed_properties(self):
        content = (
            "---\n"
            "name: my-skill\n"
            "description: Does something useful.\n"
            "license: Apache-2.0\n"
            "allowed-tools:\n"
            "  - bash\n"
            "metadata:\n"
            "  author: Test\n"
            "---\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(tmp, content)
            valid, msg = validate_skill(skill_dir)
            self.assertTrue(valid, msg)

    def test_valid_name_with_digits(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: skill2go\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertTrue(valid, msg)

    # ------------------------------------------------------------------ missing files

    def test_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "my-skill"
            skill_dir.mkdir()
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("SKILL.md", msg)

    # ------------------------------------------------------------------ frontmatter format

    def test_no_frontmatter_delimiter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(tmp, "name: my-skill\n")
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("frontmatter", msg.lower())

    def test_invalid_frontmatter_no_closing_delimiter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(tmp, "---\nname: my-skill\n")
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)

    def test_invalid_yaml_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: [unclosed bracket\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("YAML", msg)

    def test_frontmatter_not_a_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(tmp, "---\n- item1\n- item2\n---\n")
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("dictionary", msg)

    # ------------------------------------------------------------------ required fields

    def test_missing_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("name", msg)

    def test_missing_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("description", msg)

    # ------------------------------------------------------------------ unexpected keys

    def test_unexpected_frontmatter_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp,
                "---\nname: my-skill\ndescription: A skill.\nunknown-key: value\n---\n",
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("unknown-key", msg)

    # ------------------------------------------------------------------ name validation

    def test_name_with_uppercase(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: My-Skill\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("hyphen-case", msg)

    def test_name_with_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my skill\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)

    def test_name_starts_with_hyphen(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: -my-skill\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("hyphen", msg.lower())

    def test_name_ends_with_hyphen(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill-\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)

    def test_name_consecutive_hyphens(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my--skill\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)

    def test_name_too_long(self):
        long_name = "a" * 65
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, f"---\nname: {long_name}\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("64", msg)

    def test_name_exactly_max_length(self):
        max_name = "a" * 64
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, f"---\nname: {max_name}\ndescription: A skill.\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertTrue(valid, msg)

    def test_name_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: 123\ndescription: A skill.\n---\n"
            )
            # 123 parses as an integer in YAML
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("string", msg)

    # ------------------------------------------------------------------ description validation

    def test_description_with_left_angle_bracket(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill\ndescription: 'A <skill>.'\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("angle bracket", msg)

    def test_description_with_right_angle_bracket(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill\ndescription: 'A skill>.'\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)

    def test_description_too_long(self):
        long_desc = "a" * 1025
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, f"---\nname: my-skill\ndescription: {long_desc}\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("1024", msg)

    def test_description_exactly_max_length(self):
        max_desc = "a" * 1024
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, f"---\nname: my-skill\ndescription: {max_desc}\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertTrue(valid, msg)

    def test_description_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self._make_skill(
                tmp, "---\nname: my-skill\ndescription: 42\n---\n"
            )
            valid, msg = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("string", msg)


if __name__ == "__main__":
    unittest.main()
