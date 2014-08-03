
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        super().finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup_args = dict(
    name='gillcup',
    version='0.3.0-beta',
    packages=find_packages(),

    description="""An animation framework for Python""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    url='http://pypi.python.org/pypi/gillcup/',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries',
    ],

    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)


if __name__ == '__main__':
    setup(**setup_args)
