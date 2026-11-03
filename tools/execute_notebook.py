"""Execute every cell in a fresh kernel using this script's Python."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

root = Path(__file__).resolve().parents[1]
path = root / 'z5615327_assignment1.ipynb'
notebook = nbformat.read(path, as_version=4)
manager = KernelManager(kernel_name='python3')
manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
NotebookClient(notebook, km=manager, timeout=120,
               resources={'metadata': {'path': str(root)}}).execute()
nbformat.validate(notebook)
nbformat.write(notebook, path)
count = sum(c.cell_type == 'code' for c in notebook.cells)
print(f'Executed {count} code cells in a fresh kernel; notebook saved.')
