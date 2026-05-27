#!/usr/bin/env python3
"""
Unit tests for init_skill.py

Tests skill initialization including:
- Successful skill creation
- Directory structure creation
- SKILL.md template generation
- Error handling for existing directories
- Title case conversion
"""

import unittest
import tempfile
from pathlib import Path
from init_skill import init_skill, title_case_skill_name


class TestInitSkill(unittest.TestCase):
    """Test suite for init_skill.py"""

    def test_title_case_skill_name(self):
        """Test converting hyphenated names to title case"""
        self.assertEqual(title_case_skill_name("test-skill"), "Test Skill")
        self.assertEqual(title_case_skill_name("my-api-helper"), "My Api Helper")
        self.assertEqual(title_case_skill_name("single"), "Single")
        self.assertEqual(title_case_skill_name("a-b-c-d"), "A B C D")

    def test_init_skill_success(self):
        """Test successful skill initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertEqual(result.name, "test-skill")

    def test_init_skill_creates_skill_md(self):
        """Test that SKILL.md is created with proper content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("my-test-skill", temp_dir)

            skill_md = result / "SKILL.md"
            self.assertTrue(skill_md.exists())

            content = skill_md.read_text()
            self.assertIn("name: my-test-skill", content)
            self.assertIn("# My Test Skill", content)
            self.assertIn("description:", content)
            self.assertIn("---", content)

    def test_init_skill_creates_scripts_directory(self):
        """Test that scripts directory is created with example script"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            scripts_dir = result / "scripts"
            self.assertTrue(scripts_dir.exists())
            self.assertTrue(scripts_dir.is_dir())

            example_script = scripts_dir / "example.py"
            self.assertTrue(example_script.exists())
            self.assertIn("test-skill", example_script.read_text())

    def test_init_skill_creates_references_directory(self):
        """Test that references directory is created with example reference"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            references_dir = result / "references"
            self.assertTrue(references_dir.exists())
            self.assertTrue(references_dir.is_dir())

            api_reference = references_dir / "api_reference.md"
            self.assertTrue(api_reference.exists())
            self.assertIn("Test Skill", api_reference.read_text())

    def test_init_skill_creates_assets_directory(self):
        """Test that assets directory is created with example asset"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            assets_dir = result / "assets"
            self.assertTrue(assets_dir.exists())
            self.assertTrue(assets_dir.is_dir())

            example_asset = assets_dir / "example_asset.txt"
            self.assertTrue(example_asset.exists())

    def test_init_skill_example_script_executable(self):
        """Test that example script has executable permissions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            example_script = result / "scripts" / "example.py"
            import stat
            mode = example_script.stat().st_mode
            # Check if owner has execute permission
            self.assertTrue(mode & stat.S_IXUSR)

    def test_init_skill_existing_directory(self):
        """Test that init fails when directory already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory first
            existing = Path(temp_dir) / "test-skill"
            existing.mkdir()

            result = init_skill("test-skill", temp_dir)
            self.assertIsNone(result)

    def test_init_skill_nested_path(self):
        """Test creating skill in nested path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "directory"
            result = init_skill("test-skill", nested_path)

            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertTrue(nested_path.exists())

    def test_init_skill_with_numbers(self):
        """Test creating skill with numbers in name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill-v2", temp_dir)

            self.assertIsNotNone(result)
            skill_md = result / "SKILL.md"
            content = skill_md.read_text()
            self.assertIn("name: test-skill-v2", content)
            self.assertIn("# Test Skill V2", content)

    def test_init_skill_single_word(self):
        """Test creating skill with single word name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("validator", temp_dir)

            self.assertIsNotNone(result)
            skill_md = result / "SKILL.md"
            content = skill_md.read_text()
            self.assertIn("name: validator", content)
            self.assertIn("# Validator", content)

    def test_init_skill_preserves_name_format(self):
        """Test that skill name is preserved exactly as provided"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("my-custom-skill-123", temp_dir)

            self.assertIsNotNone(result)
            skill_md = result / "SKILL.md"
            content = skill_md.read_text()
            # Check exact match in frontmatter
            self.assertIn("name: my-custom-skill-123\n", content)

    def test_init_skill_directory_name_matches(self):
        """Test that directory name matches skill name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_name = "my-skill"
            result = init_skill(skill_name, temp_dir)

            self.assertEqual(result.name, skill_name)

    def test_init_skill_template_has_todos(self):
        """Test that generated SKILL.md contains TODO markers"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            skill_md = result / "SKILL.md"
            content = skill_md.read_text()
            self.assertIn("[TODO:", content)

    def test_init_skill_example_files_have_placeholders(self):
        """Test that example files contain helpful placeholders"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = init_skill("test-skill", temp_dir)

            # Check script placeholder
            script_content = (result / "scripts" / "example.py").read_text()
            self.assertIn("placeholder", script_content.lower())
            self.assertIn("test-skill", script_content)

            # Check reference placeholder
            ref_content = (result / "references" / "api_reference.md").read_text()
            self.assertIn("placeholder", ref_content.lower())

            # Check asset placeholder
            asset_content = (result / "assets" / "example_asset.txt").read_text()
            self.assertIn("placeholder", asset_content.lower())


if __name__ == '__main__':
    unittest.main()
