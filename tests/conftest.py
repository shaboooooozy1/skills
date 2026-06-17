import sys
import os

# Ensure skill script directories are importable
SKILL_DIRS = [
    os.path.join(os.path.dirname(__file__), "..", "skills", "skill-creator", "scripts"),
    os.path.join(os.path.dirname(__file__), "..", "skills", "slack-gif-creator", "core"),
    os.path.join(os.path.dirname(__file__), "..", "skills", "pdf", "scripts"),
    os.path.join(os.path.dirname(__file__), "..", "skills", "docx", "scripts"),
]

for d in SKILL_DIRS:
    abs_d = os.path.abspath(d)
    if abs_d not in sys.path:
        sys.path.insert(0, abs_d)
