import unittest
import tempfile
from pathlib import Path

from init_skill import init_skill, title_case_skill_name


class TestTitleCaseSkillName(unittest.TestCase):

    def test_single_word(self):
        self.assertEqual(title_case_skill_name("pdf"), "Pdf")

    def test_hyphenated_name(self):
        self.assertEqual(title_case_skill_name("my-skill"), "My Skill")

    def test_multiple_hyphens(self):
        self.assertEqual(
            title_case_skill_name("web-artifacts-builder"), "Web Artifacts Builder"
        )

    def test_digits_in_name(self):
        self.assertEqual(title_case_skill_name("skill2go"), "Skill2go")

    def test_already_lowercase(self):
        self.assertEqual(title_case_skill_name("docx"), "Docx")


class TestInitSkill(unittest.TestCase):

    # ------------------------------------------------------------------ happy path

    def test_creates_skill_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertIsNotNone(result)
            self.assertTrue(result.is_dir())

    def test_creates_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            skill_md = result / "SKILL.md"
            self.assertTrue(skill_md.exists())

    def test_skill_md_contains_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            content = (result / "SKILL.md").read_text()
            self.assertIn("my-skill", content)

    def test_skill_md_contains_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            content = (result / "SKILL.md").read_text()
            self.assertIn("My Skill", content)

    def test_skill_md_has_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            content = (result / "SKILL.md").read_text()
            self.assertTrue(content.startswith("---"))

    def test_creates_scripts_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "scripts").is_dir())

    def test_creates_example_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "scripts" / "example.py").exists())

    def test_example_script_is_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            script = result / "scripts" / "example.py"
            # Check executable bit is set
            self.assertTrue(script.stat().st_mode & 0o111)

    def test_creates_references_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "references").is_dir())

    def test_creates_api_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "references" / "api_reference.md").exists())

    def test_creates_assets_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "assets").is_dir())

    def test_creates_example_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertTrue((result / "assets" / "example_asset.txt").exists())

    def test_skill_dir_name_matches_skill_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("my-skill", tmp)
            self.assertEqual(result.name, "my-skill")

    def test_nested_path_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "a" / "b"
            result = init_skill("my-skill", nested)
            self.assertIsNotNone(result)
            self.assertTrue(result.is_dir())

    # ------------------------------------------------------------------ error cases

    def test_returns_none_if_directory_already_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create it once
            init_skill("my-skill", tmp)
            # Try again — should fail
            result = init_skill("my-skill", tmp)
            self.assertIsNone(result)

    def test_example_script_contains_skill_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("cool-tool", tmp)
            content = (result / "scripts" / "example.py").read_text()
            self.assertIn("cool-tool", content)

    def test_api_reference_contains_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init_skill("cool-tool", tmp)
            content = (result / "references" / "api_reference.md").read_text()
            self.assertIn("Cool Tool", content)


if __name__ == "__main__":
    unittest.main()
