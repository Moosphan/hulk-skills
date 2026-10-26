import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("skill_packages", ROOT / "tooling/build-skill-packages.py")
PACKAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGES)


class CleanVoicePackageTests(unittest.TestCase):
    def test_each_platform_archive_runs_and_installs_independently(self):
        original_dist = PACKAGES.DIST_DIR
        try:
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                workspace = Path(temporary)
                PACKAGES.DIST_DIR = workspace / "dist"
                for platform, host in [("claude-code", "claude"), ("codex", "codex")]:
                    package = PACKAGES.build_package(ROOT / "skills/clean-voice", platform, "test")
                    extracted = workspace / platform
                    with zipfile.ZipFile(ROOT / package["archive"]) as archive:
                        self.assertIn("clean-voice/LICENSE", archive.namelist())
                        self.assertIn("clean-voice/clean_voice/requirements/denoise.txt", archive.namelist())
                        archive.extractall(extracted)
                    skill = extracted / "clean-voice"
                    invocation = subprocess.run([sys.executable, str(skill / "scripts/voice.py"), "--version"], capture_output=True, text=True)
                    self.assertEqual(invocation.returncode, 0, invocation.stderr)
                    self.assertEqual(invocation.stdout.strip(), "0.1.0")
                    install = subprocess.run([sys.executable, str(skill / "scripts/install.py"), "--target", host, "--destination", str(workspace / "installed" / host)], capture_output=True, text=True)
                    self.assertEqual(install.returncode, 0, install.stderr)
        finally:
            PACKAGES.DIST_DIR = original_dist


if __name__ == "__main__":
    unittest.main()
