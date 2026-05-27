#!/usr/bin/env python3
"""
Unit tests for package_skill.py

Tests packaging of skills into .skill files including:
- Valid skill packaging
- Error handling for missing directories/files
- Validation integration
- Output file creation
"""

import unittest
import tempfile
import zipfile
from pathlib import Path
from package_skill import package_skill


class TestPackageSkill(unittest.TestCase):
    """Test suite for package_skill.py"""

    def create_valid_skill(self, base_dir, skill_name="test-skill"):
        """Helper to create a valid skill directory"""
        skill_path = Path(base_dir) / skill_name
        skill_path.mkdir()

        # Create valid SKILL.md
        skill_md = skill_path / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: A test skill for packaging
---

# Test Skill

This is a test skill.
""")

        # Create some additional files to package
        scripts_dir = skill_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "example.py").write_text("print('hello')")

        assets_dir = skill_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "template.txt").write_text("template content")

        return skill_path

    def test_package_valid_skill(self):
        """Test packaging a valid skill"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir)
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result = package_skill(skill_path, output_dir)

            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertEqual(result.name, "test-skill.skill")

            # Verify it's a valid zip file
            self.assertTrue(zipfile.is_zipfile(result))

            # Verify contents
            with zipfile.ZipFile(result, 'r') as zipf:
                names = zipf.namelist()
                self.assertIn("test-skill/SKILL.md", names)
                self.assertIn("test-skill/scripts/example.py", names)
                self.assertIn("test-skill/assets/template.txt", names)

    def test_package_nonexistent_path(self):
        """Test packaging fails with nonexistent path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent = Path(temp_dir) / "nonexistent"
            result = package_skill(nonexistent)
            self.assertIsNone(result)

    def test_package_file_not_directory(self):
        """Test packaging fails when path is a file, not directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "file.txt"
            file_path.write_text("not a directory")
            result = package_skill(file_path)
            self.assertIsNone(result)

    def test_package_missing_skill_md(self):
        """Test packaging fails when SKILL.md is missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = Path(temp_dir) / "test-skill"
            skill_path.mkdir()
            result = package_skill(skill_path)
            self.assertIsNone(result)

    def test_package_invalid_skill_md(self):
        """Test packaging fails when SKILL.md is invalid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = Path(temp_dir) / "test-skill"
            skill_path.mkdir()

            # Create invalid SKILL.md (missing frontmatter)
            skill_md = skill_path / "SKILL.md"
            skill_md.write_text("# Test Skill\n\nNo frontmatter here!")

            result = package_skill(skill_path)
            self.assertIsNone(result)

    def test_package_with_nested_directories(self):
        """Test packaging preserves nested directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir)

            # Add nested directories
            nested = skill_path / "references" / "docs" / "api"
            nested.mkdir(parents=True)
            (nested / "endpoints.md").write_text("API endpoints")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result = package_skill(skill_path, output_dir)

            self.assertIsNotNone(result)

            # Verify nested structure is preserved
            with zipfile.ZipFile(result, 'r') as zipf:
                names = zipf.namelist()
                self.assertIn("test-skill/references/docs/api/endpoints.md", names)

    def test_package_default_output_location(self):
        """Test packaging with default output location (current directory)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir)

            # Change to temp directory so output goes there
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = package_skill(skill_path)

                self.assertIsNotNone(result)
                self.assertTrue(result.exists())
                self.assertEqual(result.parent, Path(temp_dir))
            finally:
                os.chdir(original_cwd)

    def test_package_creates_output_directory(self):
        """Test packaging creates output directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir)
            output_dir = Path(temp_dir) / "new" / "output" / "dir"

            self.assertFalse(output_dir.exists())

            result = package_skill(skill_path, output_dir)

            self.assertIsNotNone(result)
            self.assertTrue(output_dir.exists())
            self.assertTrue(result.exists())

    def test_package_skill_name_in_filename(self):
        """Test that skill name is correctly used in output filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir, "my-custom-skill")
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result = package_skill(skill_path, output_dir)

            self.assertIsNotNone(result)
            self.assertEqual(result.name, "my-custom-skill.skill")

    def test_package_includes_all_file_types(self):
        """Test that packaging includes various file types"""
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_path = self.create_valid_skill(temp_dir)

            # Add various file types
            (skill_path / "LICENSE.txt").write_text("Apache 2.0")
            (skill_path / "assets" / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            references_dir = skill_path / "references"
            references_dir.mkdir(exist_ok=True)
            (references_dir / "docs.md").write_text("# Documentation")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            result = package_skill(skill_path, output_dir)

            self.assertIsNotNone(result)

            with zipfile.ZipFile(result, 'r') as zipf:
                names = zipf.namelist()
                self.assertIn("test-skill/LICENSE.txt", names)
                self.assertIn("test-skill/assets/image.png", names)
                self.assertIn("test-skill/references/docs.md", names)


if __name__ == '__main__':
    unittest.main()
