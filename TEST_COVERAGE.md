# Test Coverage Documentation

This document provides an overview of the test coverage for the skills repository, including which components are tested, how to run tests, and areas identified for future improvement.

## Test Infrastructure

### Test Runner

The repository includes a centralized test runner (`run_tests.py`) that discovers and executes all unit tests.

**Usage:**
```bash
# Run all tests
python3 run_tests.py

# Run with verbose output
python3 run_tests.py --verbose

# Run tests matching a specific pattern
python3 run_tests.py --pattern "test_quick_*"
```

### Test Framework

All tests use Python's built-in `unittest` framework, ensuring no external dependencies are required for running tests.

## Current Test Coverage

### 1. Skill Creator Scripts (skills/skill-creator/scripts/)

#### test_quick_validate.py (21 tests)
Tests for `quick_validate.py` - the skill validation script.

**Coverage areas:**
- Valid skill validation (minimal and with optional fields)
- Missing SKILL.md detection
- Frontmatter format validation
- YAML parsing errors
- Required field validation (name, description)
- Type checking (name and description must be strings)
- Naming convention enforcement (hyphen-case)
- Name validation (leading/trailing hyphens, consecutive hyphens, special characters)
- Field length limits (name: 64 chars, description: 1024 chars)
- Invalid character detection (angle brackets in description)
- Unexpected frontmatter properties
- Non-dictionary frontmatter

**Key test cases:**
- `test_valid_minimal_skill` - Ensures valid minimal skills pass
- `test_name_too_long` - Validates 64 character limit
- `test_description_with_angle_brackets` - Catches invalid characters
- `test_unexpected_frontmatter_keys` - Enforces allowed properties

#### test_package_skill.py (10 tests)
Tests for `package_skill.py` - the skill packaging script.

**Coverage areas:**
- Valid skill packaging into .skill (zip) files
- Nonexistent path handling
- File vs directory validation
- Missing SKILL.md detection
- Integration with validation
- Nested directory structure preservation
- Output directory creation
- Default output location handling
- Filename generation from skill name
- Multiple file type inclusion

**Key test cases:**
- `test_package_valid_skill` - End-to-end packaging workflow
- `test_package_with_nested_directories` - Preserves directory structure
- `test_package_creates_output_directory` - Creates parent directories as needed
- `test_package_invalid_skill_md` - Prevents packaging invalid skills

#### test_init_skill.py (15 tests)
Tests for `init_skill.py` - the skill initialization script.

**Coverage areas:**
- Title case name conversion
- Successful skill directory creation
- SKILL.md template generation with proper frontmatter
- Scripts directory creation with executable example
- References directory creation with placeholder docs
- Assets directory creation with example files
- Executable permission setting on scripts
- Existing directory conflict detection
- Nested path creation
- Name format preservation (numbers, hyphens)
- TODO marker inclusion in templates
- Placeholder content in example files

**Key test cases:**
- `test_init_skill_success` - Complete initialization workflow
- `test_init_skill_example_script_executable` - Verifies script permissions
- `test_init_skill_existing_directory` - Prevents overwriting
- `test_init_skill_template_has_todos` - Ensures templates are helpful

### 2. Slack GIF Creator (skills/slack-gif-creator/core/)

#### test_validators.py (15 tests)
Tests for `validators.py` - GIF validation for Slack.

**Coverage areas:**
- Emoji GIF optimal dimensions (128x128)
- Emoji GIF acceptable range (64-128, square)
- Emoji GIF size limits (too small, too large)
- Emoji GIF shape validation (must be square)
- Message GIF dimensions (320-640, aspect ratio ≤2:1)
- Message GIF aspect ratio validation
- Frame count calculation
- Duration and FPS calculation
- File size reporting (KB and MB)
- Nonexistent file handling
- Corrupted GIF handling
- Convenience function `is_slack_ready()`
- Results dictionary structure validation

**Key test cases:**
- `test_validate_emoji_optimal_dimensions` - 128x128 validation
- `test_validate_message_gif_aspect_ratio_too_high` - Aspect ratio limits
- `test_validate_calculates_duration` - Frame timing calculations
- `test_validate_nonexistent_file` - Graceful error handling

**Note:** Tests mock PIL/Pillow since it may not be available in all environments.

### 3. PDF Scripts (skills/pdf/scripts/)

#### check_bounding_boxes_test.py (10 tests)
Tests for `check_bounding_boxes.py` - PDF form field validation.

**Coverage areas:**
- No bounding box intersections (valid case)
- Label-entry intersection detection (same field)
- Cross-field intersection detection
- Different page isolation (no false positives)
- Entry box height validation against font size
- Adequate entry box height validation
- Default font size handling
- Missing entry_text handling
- Multiple error limiting (prevents excessive output)
- Edge-touching boxes (should not intersect)

**Key test cases:**
- `test_no_intersections` - Valid form field layout
- `test_label_entry_intersection_same_field` - Catches overlaps
- `test_entry_height_too_small` - Font size vs box height
- `test_multiple_errors_limit` - Output management

## Test Summary

| Component | Test File | Tests | Status |
|-----------|-----------|-------|--------|
| quick_validate.py | test_quick_validate.py | 21 | ✅ All passing |
| package_skill.py | test_package_skill.py | 10 | ✅ All passing |
| init_skill.py | test_init_skill.py | 15 | ✅ All passing |
| validators.py (slack-gif) | test_validators.py | 15 | ✅ All passing |
| check_bounding_boxes.py | check_bounding_boxes_test.py | 10 | ✅ All passing |
| **TOTAL** | | **61** | **✅ All passing** |

## Areas Without Test Coverage

The following components currently lack automated tests and represent opportunities for improving test coverage:

### High Priority

1. **PDF Scripts** (skills/pdf/scripts/)
   - `fill_pdf_form_with_annotations.py` - Form filling logic
   - `fill_fillable_fields.py` - Field population
   - `extract_form_field_info.py` - Form field extraction
   - `convert_pdf_to_images.py` - PDF to image conversion
   - `check_fillable_fields.py` - Fillable field detection
   - `create_validation_image.py` - Validation image generation

2. **DOCX Scripts** (skills/docx/scripts/)
   - `document.py` - Document manipulation
   - `utilities.py` - Helper functions
   - OOXML validation scripts in `skills/docx/ooxml/scripts/`

3. **PPTX Scripts** (skills/pptx/scripts/)
   - `thumbnail.py` - Thumbnail generation
   - `replace.py` - Content replacement
   - `inventory.py` - Slide inventory
   - `rearrange.py` - Slide reordering

4. **Slack GIF Creator Core** (skills/slack-gif-creator/core/)
   - `easing.py` - Animation easing functions
   - `frame_composer.py` - Frame composition
   - `gif_builder.py` - GIF building logic

### Medium Priority

5. **MCP Builder Scripts** (skills/mcp-builder/scripts/)
   - `connections.py` - Connection management
   - `evaluation.py` - Evaluation logic

6. **Combined Chatbot Scripts** (skills/combined-chatbot/scripts/)
   - `init_chatbot.py` - Chatbot initialization

7. **XLSX Scripts** (skills/xlsx/)
   - `recalc.py` - Spreadsheet recalculation

8. **Webapp Testing Examples** (skills/webapp-testing/examples/)
   - Example scripts (though these may be intentionally untested as demonstrations)

### Lower Priority

9. **Web Artifacts Builder** - JavaScript/React components
10. **Other Skills** - Many skills contain primarily documentation and may not require unit tests

## Recommendations for Future Testing

### 1. Integration Tests
While unit tests cover individual functions well, integration tests would verify:
- End-to-end skill packaging and installation
- Multi-script workflows (e.g., PDF form filling + validation)
- Cross-skill interactions

### 2. Test Data
Create a `test_data/` directory with:
- Sample PDF files for PDF script testing
- Sample DOCX/PPTX files for document testing
- Sample GIF files for validator testing
- Sample skill directories for validation testing

### 3. Continuous Integration
Consider setting up CI to:
- Run tests on every commit
- Generate coverage reports
- Enforce minimum coverage thresholds
- Test across multiple Python versions

### 4. Mock External Dependencies
Many scripts depend on external tools (LibreOffice, Pillow, pypdf). Tests should:
- Mock these dependencies where possible
- Skip tests gracefully when dependencies unavailable
- Document required dependencies for each test suite

### 5. Property-Based Testing
Consider using hypothesis or similar for:
- Fuzzing skill validation with random inputs
- Testing boundary conditions in validators
- Generating random but valid SKILL.md files

## Running Tests

### Run All Tests
```bash
python3 run_tests.py
```

### Run Specific Test Suite
```bash
python3 -m unittest skills/skill-creator/scripts/test_quick_validate.py
```

### Run Single Test
```bash
python3 -m unittest test_quick_validate.TestQuickValidate.test_valid_minimal_skill
```

### Verbose Output
```bash
python3 run_tests.py --verbose
```

## Test Development Guidelines

When adding new tests to this repository:

1. **Use unittest framework** - Maintain consistency with existing tests
2. **Name tests descriptively** - Use `test_<what_is_being_tested>`
3. **One assertion per concept** - Tests should verify one thing clearly
4. **Include docstrings** - Explain what each test validates
5. **Mock external dependencies** - Tests should run without external services
6. **Clean up after tests** - Use `tempfile.TemporaryDirectory()` for file operations
7. **Test error cases** - Validate error handling, not just happy paths
8. **Keep tests fast** - Unit tests should complete in milliseconds

## Coverage Metrics

Current coverage by component type:
- **Skill infrastructure**: ✅ Well covered (46 tests across 3 scripts)
- **Validators**: ✅ Well covered (25 tests across 2 validators)
- **Document manipulation**: ⚠️ No coverage (0 tests)
- **GIF creation**: ⚠️ Partial coverage (validators only, not builders)
- **PDF manipulation**: ⚠️ Minimal coverage (1 validator, 5+ scripts untested)
- **Web/Browser testing**: ⚠️ No coverage (examples untested)

## Conclusion

The skills repository now has a solid foundation of 61 unit tests covering critical validation and infrastructure code. The test runner makes it easy to execute all tests and identify failures. However, significant opportunities remain to improve coverage, particularly for document manipulation, PDF processing, and GIF creation logic.

Priority should be given to testing components that:
1. Handle user input or external files
2. Perform complex transformations
3. Have potential security implications
4. Are frequently modified or extended
