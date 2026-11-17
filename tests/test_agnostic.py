from __future__ import annotations

from pathlib import Path
import hashlib
import unittest


REPO = Path(__file__).resolve().parents[1]
TESTS = REPO / "tests"


class AgnosticSurfaceTests(unittest.TestCase):
    def test_guard_docs_tests_and_examples_contain_no_project_specific_terms(self):
        pattern_file = TESTS / "fixtures" / "forbidden.sha256"
        patterns = []
        for line in pattern_file.read_text(encoding="utf-8").splitlines():
            length, digest = line.split()
            patterns.append((int(length), digest))
        targets = [
            REPO / "guardia",
            REPO / "docs" / "GUARDIA_OPERATIVA.md",
            TESTS / "test_guardia.py",
            TESTS / "test_agnostic.py",
            TESTS / "fixtures",
        ]
        files = []
        for target in targets:
            if target.is_file():
                files.append(target)
            elif target.is_dir():
                files.extend(p for p in target.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        for path in files:
            if path.resolve() == pattern_file.resolve():
                continue
            try:
                content = path.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue
            for length, expected in patterns:
                for start in range(0, max(0, len(content) - length + 1)):
                    candidate = content[start:start + length]
                    if hashlib.sha256(candidate.encode("utf-8")).hexdigest() == expected:
                        self.fail(f"non-agnostic content detected in {path.relative_to(REPO)}")


if __name__ == "__main__":
    unittest.main()
