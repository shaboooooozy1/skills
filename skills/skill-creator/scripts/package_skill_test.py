import unittest
import tempfile
import zipfile
from pathlib import Path

from package_skill import package_skill


VALID_SKILL_MD = "---\nname: my-skill\ndescription: Does something useful.\n---\n\n# My Skill\n"


def _make_valid_skill(parent_dir, skill_name="my-skill"):
    """Create a minimal valid skill directory and return its path."""
    skill_dir = Path(parent_dir) / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD)
    return skill_dir


class TestPackageSkill(unittest.TestCase):

    # ------------------------------------------------------------------ error cases

    def test_nonexistent_skill_path(self):
        result = package_skill("/nonexistent/path/to/skill")
        self.assertIsNone(result)

    def test_path_is_not_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "not-a-dir.txt"
            file_path.write_text("hello")
            result = package_skill(str(file_path))
            self.assertIsNone(result)

    def test_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "my-skill"
            skill_dir.mkdir()
            # No SKILL.md
            result = package_skill(str(skill_dir))
            self.assertIsNone(result)

    def test_invalid_skill_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "my-skill"
            skill_dir.mkdir()
            # SKILL.md with invalid frontmatter (missing description)
            (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
            result = package_skill(str(skill_dir))
            self.assertIsNone(result)

    # ------------------------------------------------------------------ happy path

    def test_returns_path_to_skill_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            result = package_skill(str(skill_dir), tmp)
            self.assertIsNotNone(result)
            self.assertEqual(result.suffix, ".skill")

    def test_skill_file_is_a_valid_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            result = package_skill(str(skill_dir), tmp)
            self.assertTrue(zipfile.is_zipfile(str(result)))

    def test_skill_file_contains_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            result = package_skill(str(skill_dir), tmp)
            with zipfile.ZipFile(str(result)) as zf:
                names = zf.namelist()
            self.assertTrue(any("SKILL.md" in n for n in names))

    def test_skill_filename_matches_skill_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp, skill_name="cool-tool")
            result = package_skill(str(skill_dir), tmp)
            self.assertEqual(result.stem, "cool-tool")

    def test_custom_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            output_dir = Path(tmp) / "dist"
            result = package_skill(str(skill_dir), str(output_dir))
            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertEqual(result.parent.resolve(), output_dir.resolve())

    def test_output_directory_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            output_dir = Path(tmp) / "new" / "nested" / "dir"
            result = package_skill(str(skill_dir), str(output_dir))
            self.assertIsNotNone(result)
            self.assertTrue(output_dir.exists())

    def test_default_output_in_cwd(self):
        """When no output_dir given, .skill file lands in current working directory."""
        import os
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                result = package_skill(str(skill_dir))
                self.assertIsNotNone(result)
                self.assertEqual(result.parent.resolve(), Path(tmp).resolve())
            finally:
                os.chdir(original_cwd)
                # Clean up the generated .skill file
                if result and result.exists():
                    result.unlink()

    def test_skill_file_contains_all_files(self):
        """All files in the skill directory are included in the package."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _make_valid_skill(tmp)
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "helper.py").write_text("# helper\n")
            result = package_skill(str(skill_dir), tmp)
            with zipfile.ZipFile(str(result)) as zf:
                names = zf.namelist()
            self.assertTrue(any("helper.py" in n for n in names))


if __name__ == "__main__":
    unittest.main()
