
from setuptools import setup, find_packages

setup(
    name='gillcup',
    version='0.2.0-alpha.0',  # XXX: Duplicated in __init__.py
    packages=find_packages(),

    description="""An animation framework for Python""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    install_requires=[],
    use_2to3=True,
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

    tests_require=["pytest"],
    test_suite='gillcup.test.run',
)
