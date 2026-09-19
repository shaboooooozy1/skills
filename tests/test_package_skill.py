"""
Tests for skill-creator/scripts/package_skill.py
"""

import pytest
import zipfile
from pathlib import Path

from package_skill import package_skill


VALID_SKILL_MD = """---
name: my-skill
description: A test skill for packaging.
---

# My Skill

Content here.
"""


def make_valid_skill(tmp_path, skill_name="my-skill"):
    """Create a minimal valid skill directory and return its path."""
    skill_dir = tmp_path / skill_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(VALID_SKILL_MD.replace("my-skill", skill_name))
    return skill_dir


class TestPackageSkill:
    def test_creates_skill_file(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path)
        output_dir = tmp_path / "output"
        result = package_skill(skill_dir, output_dir)

        assert result is not None
        assert result.exists()
        assert result.suffix == ".skill"

    def test_skill_file_is_valid_zip(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path)
        output_dir = tmp_path / "output"
        result = package_skill(skill_dir, output_dir)

        assert zipfile.is_zipfile(result)

    def test_skill_file_contains_skill_md(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path)
        output_dir = tmp_path / "output"
        result = package_skill(skill_dir, output_dir)

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert any("SKILL.md" in n for n in names)

    def test_skill_file_named_after_skill(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path, "cool-tool")
        output_dir = tmp_path / "output"
        result = package_skill(skill_dir, output_dir)

        assert result.name == "cool-tool.skill"

    def test_default_output_dir_is_cwd(self, tmp_path, monkeypatch):
        skill_dir = make_valid_skill(tmp_path)
        monkeypatch.chdir(tmp_path)
        result = package_skill(skill_dir)

        assert result is not None
        assert result.parent == tmp_path

    def test_nonexistent_skill_path_returns_none(self, tmp_path):
        result = package_skill(tmp_path / "does-not-exist")
        assert result is None

    def test_path_is_file_not_dir_returns_none(self, tmp_path):
        f = tmp_path / "notadir.txt"
        f.write_text("hello")
        result = package_skill(f)
        assert result is None

    def test_missing_skill_md_returns_none(self, tmp_path):
        skill_dir = tmp_path / "no-md"
        skill_dir.mkdir()
        result = package_skill(skill_dir)
        assert result is None

    def test_invalid_skill_validation_returns_none(self, tmp_path):
        # SKILL.md with unknown key fails validation
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: bad-skill\ndescription: ok\nextra: bad\n---\n")
        result = package_skill(skill_dir)
        assert result is None

    def test_additional_files_included_in_zip(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path)
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "helper.py").write_text("# helper")
        output_dir = tmp_path / "output"
        result = package_skill(skill_dir, output_dir)

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
        assert any("helper.py" in n for n in names)

    def test_output_dir_created_if_missing(self, tmp_path):
        skill_dir = make_valid_skill(tmp_path)
        output_dir = tmp_path / "new" / "nested" / "output"
        assert not output_dir.exists()
        result = package_skill(skill_dir, output_dir)
        assert result is not None
        assert output_dir.exists()
