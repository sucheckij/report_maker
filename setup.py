# "devpi upload" complains about missing setup.py
# even though "python -m build" works fine with setup.cfg and pyproject.toml.
# That's why I added this otherwise redundant file.

from setuptools import setup
setup()
