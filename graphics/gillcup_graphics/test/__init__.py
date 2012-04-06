"""Provide a run() function that wraps the pytest runner in a unittest suite.

The goal is to:
- have `setup.py test` work
- have `tox` work, even with Distribute's use_2to3 option
- have `py.test` work
- not include a binary blob in the repository (which pytest actually recommends
    at http://pytest.org/latest/goodpractises.html)

These requirements are, alas, rather difficult to juggle. I would appreciate
a better solution than the following hack.
"""

import unittest
import os

import pytest


def run():
    class PytestWrapper(unittest.TestCase):
        def test_wraper(self):
            errno = pytest.main([os.path.dirname(__file__)])
            assert not errno, 'pytest failed'
    return unittest.TestSuite([PytestWrapper('test_wraper')])

if __name__ == '__main__':
    run()
