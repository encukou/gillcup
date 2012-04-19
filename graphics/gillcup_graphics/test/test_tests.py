"""Test the rendering test suite itself
"""

from __future__ import division

import pytest

from gillcup_graphics import Rectangle

# pylint: disable=W0611
from gillcup_graphics.test.testlayer import pytest_funcarg__layer
from gillcup_graphics.test.test_transformation import (
        almost_equal, sequences_almost_equal, matrix_almost_equal)


@pytest.mark.raises
def test_no_reference(layer):
    """No reference rendering available"""
    Rectangle(layer)


@pytest.mark.raises
def test_different_reference(layer):
    """The reference rendering is vastly different"""
    Rectangle(layer)


def test_similar_reference(layer):
    """The reference rendering is good enough"""
    Rectangle(layer)


class TestClassBasedTest(object):
    def test_in_class(self, layer):
        """Test works from within a class"""
        Rectangle(layer)


def test_almost_equal():
    """Test the almost_equal helper"""
    assert almost_equal(1, 1)
    assert almost_equal(1, 1.0000001)
    assert not almost_equal(1, 1.1)
    assert not almost_equal(1, 2)


def test_sequences_almost_equal():
    """Test the sequences_almost_equal helper"""
    assert sequences_almost_equal([1], [1])
    assert sequences_almost_equal([1], [1.0000001])
    assert sequences_almost_equal([1, 2], [1, 2])
    assert sequences_almost_equal([2, 2], [2, 2.0000001])
    assert not sequences_almost_equal([1], [1.1])
    assert not sequences_almost_equal([1], [1, 1])


def test_matrix_almost_equal():
    """Test the matrix_almost_equal helper"""
    assert matrix_almost_equal([1], 1)
    assert matrix_almost_equal([1], 1.0000001)
    assert matrix_almost_equal([1, 2], 1, 2)
    assert matrix_almost_equal([2, 2], 2, 2.0000001)
    assert not matrix_almost_equal([1], 1.1)
    assert not matrix_almost_equal([1], 1, 1)
