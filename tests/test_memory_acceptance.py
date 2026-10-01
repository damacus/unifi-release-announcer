"""Exercise the memory acceptance CLI on ordinary Docker hosts without RTK."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/memory_acceptance.py"


class MemoryAcceptanceTest(unittest.TestCase):
    def run_gate(self, root: Path):
        env = dict(os.environ, PATH=str(root))
        return subprocess.run(
            [sys.executable, str(SCRIPT), "candidate", str(root / "evidence"), "--hours", "0.000001"],
            env=env, capture_output=True, text=True, timeout=5,
        )

    def test_docker_only_host_samples_but_short_run_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / "docker"
            docker.write_text("#!" + sys.executable + "\n" + """
import json
import sys
if sys.argv[1] == "inspect":
    print("sha256:synthetic" if "{{.Image}}" in sys.argv else json.dumps({"Running": True}))
elif sys.argv[1] == "stats":
    print("2.5MiB / 100MiB")
elif sys.argv[1] == "logs":
    print(json.dumps({"timestamp": "2026-10-01T00:00:00Z", "fields": {
        "phase": "idle", "message": "poll completed", "success": True
    }}))
else:
    sys.exit(2)
""")
            docker.chmod(0o700)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            summary = json.loads((root / "evidence/summary.json").read_text())
            self.assertEqual(summary["failures"], [])
            self.assertEqual(summary["samples"], 1)
            self.assertEqual(summary["peak_bytes"], 2621440)
            self.assertFalse(summary["passed_24h_gate"])

    def test_missing_docker_records_failure_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.run_gate(root)
            self.assertEqual(result.returncode, 1, result.stderr)
            summary = json.loads((root / "evidence/summary.json").read_text())
            self.assertEqual(summary["samples"], 0)
            self.assertIn("docker", summary["failures"][0])
            self.assertFalse(summary["passed_24h_gate"])


if __name__ == "__main__":
    unittest.main()
