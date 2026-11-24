import ast
from pathlib import Path
import unittest


SOURCE_DIR = Path(__file__).resolve().parents[1] / "src"
FORBIDDEN_CALLS = {"dict", "set", "hash"}


class SourceRuleTests(unittest.TestCase):
    def test_source_does_not_use_builtin_hash_containers_or_hash(self):
        violations = []
        for path in sorted(SOURCE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Dict, ast.DictComp, ast.Set, ast.SetComp)):
                    violations.append(f"{path.name}:{node.lineno}: built-in container literal")
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in FORBIDDEN_CALLS
                ):
                    violations.append(f"{path.name}:{node.lineno}: {node.func.id}()")

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
