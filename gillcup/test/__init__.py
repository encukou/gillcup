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
import sys

import six

skip_lint = six.PY3 or hasattr(sys, 'pypy_version_info')
if not skip_lint:
    from pylint import lint

import pytest

skipIf = getattr(unittest, 'skipIf', None)
if skipIf is None:  # pragma: no cover
    def skipIf(condition, reason):  # pylint: disable=E0102
        """Replacement for unittest.skipIf for pythons that don't have it"""
        def _skip(func):
            if condition:
                print('skipping test: %s' % reason)
                return(reason)
            else:
                return func
        return _skip


def test_suite(basefile=__file__):  # pragma: no cover
    """Top-level test function"""
    test_dir = os.path.abspath(os.path.join(os.path.dirname(basefile), '..'))

    class PytestWrapper(unittest.TestCase):
        """TestCase that wraps pytest & pylint"""
        def test_wraper(self):
            """Run pytest"""
            errno = pytest.main([os.path.dirname(basefile), '-v'])
            assert not errno, 'pytest failed'

        @skipIf(skip_lint, 'pylint not supported on this python')
        def lint_wraper(self):
            """Run pylint"""
            rc_path = os.path.join(test_dir, '..', '.pylintrc')
            try:
                print([test_dir, '--rcfile', rc_path])
                print(basefile)
                errno = lint.Run([test_dir, '--rcfile', rc_path])
            except SystemExit:
                errno = sys.exc_info()[1].code
            assert not errno, 'pylint failed'

    return unittest.TestSuite([
            PytestWrapper('test_wraper'),
            PytestWrapper('lint_wraper'),
        ])
