"""
Tests for skill-creator/scripts/init_skill.py
"""

import os
import pytest
from pathlib import Path

from init_skill import title_case_skill_name, init_skill


class TestTitleCaseSkillName:
    def test_single_word(self):
        assert title_case_skill_name("pdf") == "Pdf"

    def test_hyphenated_two_words(self):
        assert title_case_skill_name("skill-creator") == "Skill Creator"

    def test_hyphenated_three_words(self):
        assert title_case_skill_name("web-artifacts-builder") == "Web Artifacts Builder"

    def test_already_lowercase(self):
        assert title_case_skill_name("mcp-builder") == "Mcp Builder"

    def test_with_digits(self):
        assert title_case_skill_name("m365-email") == "M365 Email"

    def test_empty_string(self):
        # Each word in empty split is empty string; capitalize() of "" is ""
        assert title_case_skill_name("") == ""


class TestInitSkill:
    def test_creates_expected_structure(self, tmp_path):
        result = init_skill("my-skill", tmp_path)
        skill_dir = tmp_path / "my-skill"

        assert result == skill_dir
        assert skill_dir.is_dir()
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "scripts" / "example.py").is_file()
        assert (skill_dir / "references" / "api_reference.md").is_file()
        assert (skill_dir / "assets" / "example_asset.txt").is_file()

    def test_skill_md_contains_skill_name(self, tmp_path):
        init_skill("my-skill", tmp_path)
        content = (tmp_path / "my-skill" / "SKILL.md").read_text()
        assert "my-skill" in content

    def test_skill_md_contains_title(self, tmp_path):
        init_skill("my-skill", tmp_path)
        content = (tmp_path / "my-skill" / "SKILL.md").read_text()
        assert "My Skill" in content

    def test_skill_md_has_yaml_frontmatter(self, tmp_path):
        init_skill("my-skill", tmp_path)
        content = (tmp_path / "my-skill" / "SKILL.md").read_text()
        assert content.startswith("---")

    def test_example_script_contains_skill_name(self, tmp_path):
        init_skill("cool-tool", tmp_path)
        content = (tmp_path / "cool-tool" / "scripts" / "example.py").read_text()
        assert "cool-tool" in content

    def test_example_script_is_executable(self, tmp_path):
        init_skill("my-skill", tmp_path)
        script = tmp_path / "my-skill" / "scripts" / "example.py"
        assert os.access(script, os.X_OK)

    def test_returns_none_if_directory_exists(self, tmp_path):
        # Create it once
        init_skill("my-skill", tmp_path)
        # Try to create again
        result = init_skill("my-skill", tmp_path)
        assert result is None

    def test_creates_nested_path(self, tmp_path):
        nested = tmp_path / "a" / "b"
        result = init_skill("nested-skill", nested)
        assert result is not None
        assert (nested / "nested-skill").is_dir()

    def test_returns_path_object(self, tmp_path):
        result = init_skill("my-skill", tmp_path)
        assert isinstance(result, Path)

    def test_reference_doc_contains_title(self, tmp_path):
        init_skill("my-skill", tmp_path)
        content = (tmp_path / "my-skill" / "references" / "api_reference.md").read_text()
        assert "My Skill" in content
