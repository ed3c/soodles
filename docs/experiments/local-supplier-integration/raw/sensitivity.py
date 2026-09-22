"""One planted child-credential regression; no subject file is modified."""
import os
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
import issue_atom

issue_atom.clean_child_env = lambda: dict(os.environ)
sys.argv = [str(Path(__file__).with_name("observer.py")), sys.argv[1]]
runpy.run_path(sys.argv[0], run_name="__main__")
