"""Test utilities
"""

import os.path


def resource_path(name):
    """Return the path to a testing image"""
    return os.path.join(
        os.path.dirname(__file__), 'images', 'resource', name)
