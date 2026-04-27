#!/usr/bin/env python3
"""
Tests for package_skill.py - package_skill function.
"""

import sys
import os
import unittest
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from package_skill import package_skill


def _make_valid_skill(base_dir, skill_name="my-skill"):
    """Create a minimal valid skill directory."""
    skill_dir = Path(base_dir) / skill_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: A test skill.\n---\n\n# Body\n"
    )
    return skill_dir


class TestPackageSkill(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.output_dir = Path(self.tmpdir) / "dist"
        self.output_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_nonexistent_path_returns_none(self):
        result = package_skill("/nonexistent/path/to/skill", str(self.output_dir))
        self.assertIsNone(result)

    def test_file_path_not_directory_returns_none(self):
        file_path = Path(self.tmpdir) / "not_a_dir.txt"
        file_path.write_text("hello")
        result = package_skill(str(file_path), str(self.output_dir))
        self.assertIsNone(result)

    def test_missing_skill_md_returns_none(self):
        skill_dir = Path(self.tmpdir) / "no-skill-md"
        skill_dir.mkdir()
        result = package_skill(str(skill_dir), str(self.output_dir))
        self.assertIsNone(result)

    def test_invalid_skill_validation_returns_none(self):
        # SKILL.md exists but has no valid frontmatter
        skill_dir = Path(self.tmpdir) / "invalid-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter here\n")
        result = package_skill(str(skill_dir), str(self.output_dir))
        self.assertIsNone(result)

    def test_valid_skill_creates_skill_file(self):
        skill_dir = _make_valid_skill(self.tmpdir, "good-skill")
        result = package_skill(str(skill_dir), str(self.output_dir))
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertEqual(result.suffix, ".skill")

    def test_output_filename_matches_skill_name(self):
        skill_dir = _make_valid_skill(self.tmpdir, "named-skill")
        result = package_skill(str(skill_dir), str(self.output_dir))
        self.assertEqual(result.stem, "named-skill")

    def test_output_is_valid_zip(self):
        skill_dir = _make_valid_skill(self.tmpdir, "zip-skill")
        result = package_skill(str(skill_dir), str(self.output_dir))
        self.assertTrue(zipfile.is_zipfile(result))

    def test_output_zip_contains_skill_md(self):
        skill_dir = _make_valid_skill(self.tmpdir, "content-skill")
        result = package_skill(str(skill_dir), str(self.output_dir))
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("SKILL.md" in n for n in names))

    def test_default_output_dir_is_cwd(self):
        skill_dir = _make_valid_skill(self.tmpdir, "cwd-skill")
        original_cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            result = package_skill(str(skill_dir))
            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
        finally:
            os.chdir(original_cwd)
            if result and result.exists():
                result.unlink()

    def test_skill_with_extra_files_all_included(self):
        skill_dir = _make_valid_skill(self.tmpdir, "extra-skill")
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "helper.py").write_text("# helper")
        result = package_skill(str(skill_dir), str(self.output_dir))
        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("helper.py" in n for n in names))


if __name__ == "__main__":
    unittest.main()
