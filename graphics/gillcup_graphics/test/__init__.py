"""The test suite for setup.py"""

# Same as gillcup's

import gillcup.test


def test_suite():
    """Call the Gillcup test runner on gillcup_graphics"""
    return gillcup.test.test_suite(basefile=__file__)
