#!/usr/bin/env python3
"""
Unit tests for quick_validate.py

Tests validation of skill SKILL.md files including:
- Frontmatter presence and format
- Required fields (name, description)
- Naming conventions
- Field length limits
- Invalid characters
"""

import unittest
import tempfile
from pathlib import Path
from quick_validate import validate_skill


class TestQuickValidate(unittest.TestCase):
    """Test suite for quick_validate.py"""

    def create_skill(self, skill_md_content):
        """Helper to create a temporary skill directory with SKILL.md"""
        temp_dir = tempfile.mkdtemp()
        skill_path = Path(temp_dir) / "test-skill"
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text(skill_md_content)
        return skill_path

    def test_valid_minimal_skill(self):
        """Test validation of a minimal valid skill"""
        content = """---
name: test-skill
description: A test skill for validation
---

# Test Skill

This is a test skill.
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertTrue(valid)
        self.assertEqual(message, "Skill is valid!")

    def test_missing_skill_md(self):
        """Test validation fails when SKILL.md is missing"""
        temp_dir = tempfile.mkdtemp()
        skill_path = Path(temp_dir) / "test-skill"
        skill_path.mkdir()
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertEqual(message, "SKILL.md not found")

    def test_no_frontmatter(self):
        """Test validation fails when no frontmatter is present"""
        content = """# Test Skill

This is a test skill without frontmatter.
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertEqual(message, "No YAML frontmatter found")

    def test_invalid_frontmatter_format(self):
        """Test validation fails with invalid frontmatter format"""
        content = """---
name: test-skill
description: Missing closing delimiter

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertEqual(message, "Invalid frontmatter format")

    def test_invalid_yaml(self):
        """Test validation fails with invalid YAML syntax"""
        content = """---
name: test-skill
description: [unclosed bracket
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Invalid YAML in frontmatter", message)

    def test_missing_name(self):
        """Test validation fails when name is missing"""
        content = """---
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertEqual(message, "Missing 'name' in frontmatter")

    def test_missing_description(self):
        """Test validation fails when description is missing"""
        content = """---
name: test-skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertEqual(message, "Missing 'description' in frontmatter")

    def test_name_not_string(self):
        """Test validation fails when name is not a string"""
        content = """---
name: 123
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Name must be a string", message)

    def test_description_not_string(self):
        """Test validation fails when description is not a string"""
        content = """---
name: test-skill
description: ["not", "a", "string"]
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Description must be a string", message)

    def test_invalid_name_uppercase(self):
        """Test validation fails with uppercase in name"""
        content = """---
name: Test-Skill
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("should be hyphen-case", message)

    def test_invalid_name_special_chars(self):
        """Test validation fails with special characters in name"""
        content = """---
name: test_skill
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("should be hyphen-case", message)

    def test_invalid_name_leading_hyphen(self):
        """Test validation fails with leading hyphen"""
        content = """---
name: -test-skill
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("cannot start/end with hyphen", message)

    def test_invalid_name_trailing_hyphen(self):
        """Test validation fails with trailing hyphen"""
        content = """---
name: test-skill-
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("cannot start/end with hyphen", message)

    def test_invalid_name_consecutive_hyphens(self):
        """Test validation fails with consecutive hyphens"""
        content = """---
name: test--skill
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("consecutive hyphens", message)

    def test_name_too_long(self):
        """Test validation fails when name exceeds 64 characters"""
        long_name = "a" * 65
        content = f"""---
name: {long_name}
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Name is too long", message)
        self.assertIn("65 characters", message)
        self.assertIn("Maximum is 64", message)

    def test_description_with_angle_brackets(self):
        """Test validation fails when description contains angle brackets"""
        content = """---
name: test-skill
description: A test skill with <angle> brackets
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("cannot contain angle brackets", message)

    def test_description_too_long(self):
        """Test validation fails when description exceeds 1024 characters"""
        long_desc = "a" * 1025
        content = f"""---
name: test-skill
description: {long_desc}
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Description is too long", message)
        self.assertIn("1025 characters", message)
        self.assertIn("Maximum is 1024", message)

    def test_unexpected_frontmatter_keys(self):
        """Test validation fails with unexpected frontmatter properties"""
        content = """---
name: test-skill
description: A test skill
unexpected_key: some value
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("Unexpected key", message)
        self.assertIn("unexpected_key", message)

    def test_valid_with_optional_fields(self):
        """Test validation passes with optional fields"""
        content = """---
name: test-skill
description: A test skill
license: Apache-2.0
allowed-tools:
  - read
  - write
metadata:
  version: 1.0.0
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertTrue(valid)
        self.assertEqual(message, "Skill is valid!")

    def test_valid_name_with_numbers(self):
        """Test validation passes with numbers in name"""
        content = """---
name: test-skill-123
description: A test skill
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertTrue(valid)

    def test_frontmatter_not_dict(self):
        """Test validation fails when frontmatter is not a dictionary"""
        content = """---
- name
- description
---

# Test Skill
"""
        skill_path = self.create_skill(content)
        valid, message = validate_skill(skill_path)
        self.assertFalse(valid)
        self.assertIn("must be a YAML dictionary", message)


if __name__ == '__main__':
    unittest.main()
