"""Fallback runner when pytest is not installed:  python run_tests_offline.py   (prefer `pytest`)."""
import glob, importlib, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ok = bad = 0
for f in sorted(glob.glob("tests/test_*.py")):
    mod = importlib.import_module(f[:-3].replace(os.sep, "."))
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        try:
            getattr(mod, name)(); ok += 1; print(f"PASS {f}::{name}")
        except Exception:
            bad += 1; print(f"FAIL {f}::{name}"); traceback.print_exc()
print(f"\n{ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
