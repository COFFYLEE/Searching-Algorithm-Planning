# COMP9414 Assignment 1 — z5615327

Main file: `z5615327_assignment1.ipynb` (English written answers, code and executed outputs).
The submission ZIP contains this notebook and `z5615327_results.json`.
The supplied `data/` is unchanged and is not included in the ZIP.

## Run the notebook

Create a project environment (once):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

In VS Code, use the notebook's kernel selector: **Select Another Kernel →
Python Environments → .venv**. If it is not listed, select the interpreter at
`<project directory>/.venv/bin/python`. An already-open notebook may still use
its previous kernel until you switch it explicitly.

Use Python 3.11+ with Jupyter and Matplotlib. Open the notebook from this directory
and choose **Restart Kernel and Run All Cells**. The final evaluation cell runs
all 24 required cases and rewrites `z5615327_results.json`.

Input paths are centralised in the first code cell's `INPUT_FILES` mapping.
All solver functions are defined inside the notebook; `tools/` is not a runtime
dependency and should not be included in the submission ZIP.

## Development verification

`tools/build_notebook.py` assembles the notebook from the written content and
solver cell sources. Running it clears existing executed outputs.
`tools/execute_notebook.py` then executes it in a new kernel using its own Python.
These development commands additionally need `nbformat`, `nbclient` and `ipykernel`.
The project requirements include these dependencies. Run verification with
`.venv/bin/python tools/verify.py`; to rerun and save all notebook outputs, use
`.venv/bin/python tools/execute_notebook.py` (save your editor changes first).
`tools/verify.py` runs standard-library checks against the actual notebook code.

Before submission, review and understand the implementation and written answers,
and check Moodle for the deadline and discussion booking. The specification
allows AI for learning/debugging and requires individual work and understanding
of all submitted content; this draft was prepared with AI assistance.
