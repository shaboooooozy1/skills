#!/usr/bin/env python3
"""
Tests for init_skill.py - title_case_skill_name and init_skill functions.
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from init_skill import title_case_skill_name, init_skill


class TestTitleCaseSkillName(unittest.TestCase):

    def test_single_word(self):
        self.assertEqual(title_case_skill_name("pdf"), "Pdf")

    def test_hyphenated_words(self):
        self.assertEqual(title_case_skill_name("web-artifacts-builder"), "Web Artifacts Builder")

    def test_two_words(self):
        self.assertEqual(title_case_skill_name("skill-creator"), "Skill Creator")

    def test_already_lowercase(self):
        self.assertEqual(title_case_skill_name("my-skill"), "My Skill")

    def test_with_digits(self):
        self.assertEqual(title_case_skill_name("skill123"), "Skill123")

    def test_three_words(self):
        self.assertEqual(title_case_skill_name("my-cool-skill"), "My Cool Skill")


class TestInitSkill(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_creates_skill_directory(self):
        result = init_skill("test-skill", self.tmpdir)
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertTrue(result.is_dir())

    def test_creates_skill_md(self):
        result = init_skill("test-skill", self.tmpdir)
        skill_md = result / "SKILL.md"
        self.assertTrue(skill_md.exists())

    def test_skill_md_contains_name(self):
        result = init_skill("my-skill", self.tmpdir)
        content = (result / "SKILL.md").read_text()
        self.assertIn("my-skill", content)

    def test_skill_md_contains_title(self):
        result = init_skill("my-skill", self.tmpdir)
        content = (result / "SKILL.md").read_text()
        self.assertIn("My Skill", content)

    def test_creates_scripts_directory(self):
        result = init_skill("test-skill", self.tmpdir)
        self.assertTrue((result / "scripts").is_dir())

    def test_creates_references_directory(self):
        result = init_skill("test-skill", self.tmpdir)
        self.assertTrue((result / "references").is_dir())

    def test_creates_assets_directory(self):
        result = init_skill("test-skill", self.tmpdir)
        self.assertTrue((result / "assets").is_dir())

    def test_creates_example_script(self):
        result = init_skill("test-skill", self.tmpdir)
        example_script = result / "scripts" / "example.py"
        self.assertTrue(example_script.exists())

    def test_example_script_is_executable(self):
        result = init_skill("test-skill", self.tmpdir)
        example_script = result / "scripts" / "example.py"
        self.assertTrue(os.access(example_script, os.X_OK))

    def test_creates_example_reference(self):
        result = init_skill("test-skill", self.tmpdir)
        ref = result / "references" / "api_reference.md"
        self.assertTrue(ref.exists())

    def test_creates_example_asset(self):
        result = init_skill("test-skill", self.tmpdir)
        asset = result / "assets" / "example_asset.txt"
        self.assertTrue(asset.exists())

    def test_returns_none_if_directory_exists(self):
        # Create the directory ahead of time
        existing = Path(self.tmpdir) / "existing-skill"
        existing.mkdir()
        result = init_skill("existing-skill", self.tmpdir)
        self.assertIsNone(result)

    def test_skill_directory_name_matches_skill_name(self):
        result = init_skill("cool-skill", self.tmpdir)
        self.assertEqual(result.name, "cool-skill")

    def test_example_script_contains_skill_name(self):
        result = init_skill("data-analyzer", self.tmpdir)
        script_content = (result / "scripts" / "example.py").read_text()
        self.assertIn("data-analyzer", script_content)


if __name__ == "__main__":
    unittest.main()
