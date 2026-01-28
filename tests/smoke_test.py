"""Smoke tests to verify core modules import and compile.
Run with: python -m pytest tests/smoke_test.py or python tests/smoke_test.py
"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / 'app.py', ROOT / 'engine.py', ROOT / 'database.py']

if __name__ == '__main__':
    print('Compiling core modules...')
    failed = False
    for f in FILES:
        try:
            py_compile.compile(str(f), doraise=True)
            print(f'OK: {f.name}')
        except py_compile.PyCompileError as e:
            print(f'COMPILE ERROR: {f.name}: {e}')
            failed = True
    if failed:
        sys.exit(2)
    print('All core modules compiled successfully.')
