from pathlib import Path
import subprocess
import sys


def test_smoke_command_generates_output():
    root = Path(__file__).resolve().parents[1]
    out = root / "output" / "sample_output.md"
    if out.exists():
        out.unlink()
    result = subprocess.run(
        [sys.executable, "scripts/run.py", "--input", "data/sample_input.txt", "--output", "output/sample_output.md"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert "# Action Draft" in out.read_text()
