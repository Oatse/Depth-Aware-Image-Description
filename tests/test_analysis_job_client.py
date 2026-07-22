from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_job_client_behavior() -> None:
    result = subprocess.run(
        ["node", "--test", str(ROOT / "tests" / "analysis_job_client.test.cjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
