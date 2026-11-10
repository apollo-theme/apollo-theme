import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_palette import sync  # noqa: E402

DARK = b'{"x":1}\n'
LIGHT = b'{"y":1}\n'


def git(*args: str, cwd: Path) -> str:
    command = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def make_palette_repo(base: Path) -> Path:
    repo = base / "apollo-palette"
    (repo / "palette").mkdir(parents=True)
    (repo / "palette" / "apollo.json").write_bytes(DARK)
    (repo / "palette" / "apollo-light.json").write_bytes(LIGHT)
    git("init", "-q", cwd=repo)
    git("add", "palette", cwd=repo)
    git("commit", "-q", "-m", "palette", cwd=repo)
    git("tag", "t1", cwd=repo)
    return repo


class SyncPaletteTests(unittest.TestCase):
    def test_sync_copies_pins_and_regenerates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = make_palette_repo(base)
            root = base / "root"
            (root / "palette").mkdir(parents=True)
            for slug in ("a", "b"):
                (root / slug / "palette").mkdir(parents=True)
                (root / slug / "scripts").mkdir()
                (root / slug / "scripts" / "generate.py").write_text('open("ran", "w").write("1")\n', encoding="utf-8")

            sha = sync(repo, "t1", root, ("a", "b"))

            self.assertEqual(git("rev-parse", "t1", cwd=repo), sha)
            for target in (root, root / "a", root / "b"):
                with self.subTest(target=target.name):
                    self.assertEqual(DARK, (target / "palette" / "apollo.json").read_bytes())
                    self.assertEqual(LIGHT, (target / "palette" / "apollo-light.json").read_bytes())
            pin = json.loads((root / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
            self.assertEqual("https://github.com/apollo-theme/apollo-palette", pin["repository"])
            self.assertEqual(sha, pin["commit"])
            self.assertEqual(
                {"apollo.json": hashlib.sha256(DARK).hexdigest(), "apollo-light.json": hashlib.sha256(LIGHT).hexdigest()},
                pin["sha256"],
            )
            self.assertTrue((root / "a" / "ran").exists())
            self.assertTrue((root / "b" / "ran").exists())

    def test_cli_rejects_unknown_ref(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = make_palette_repo(Path(directory))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "sync_palette.py"), str(repo), "nope"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("unknown ref nope", result.stderr)


if __name__ == "__main__":
    unittest.main()
