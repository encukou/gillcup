
import sys

from setuptools import setup, find_packages

setup_args = dict(
    name='gillcup',
    version='0.2.0-beta',  # XXX: Duplicated in __init__.py
    packages=find_packages(),

    description="""An animation framework for Python""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    url='http://pypi.python.org/pypi/gillcup/',
    install_requires=['six>=1.1'],
    classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.1',
            'Programming Language :: Python :: 3.2',
            'Topic :: Software Development :: Libraries',
        ],

    tests_require=['pytest>=2.2', 'pytest-pep8'],
    package_data={'': ['.pylintrc']},
    test_suite='gillcup.test.test_suite',
)

if sys.version_info < (3, 0):
    setup_args['tests_require'].append('pylint')

if __name__ == '__main__':
    setup(**setup_args)
