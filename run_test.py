"""Run test and capture output to UTF-8 file."""
import subprocess
r = subprocess.run(
    ["python", "test_all.py"],
    capture_output=True, text=True, cwd=r"e:\Backend"
)
with open(r"e:\Backend\test_out.txt", "w", encoding="utf-8") as f:
    f.write(r.stdout)
    if r.stderr:
        f.write("\n--- STDERR ---\n")
        f.write(r.stderr)
    f.write(f"\n--- EXIT CODE: {r.returncode} ---\n")
print(f"Done, exit={r.returncode}")
