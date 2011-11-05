
from setuptools import setup, find_packages

setup(
    name='gillcup',
    version='0.2',
    packages=find_packages(),

    description="""An animation framework for Python""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    install_requires=[],
    use_2to3=True,

    tests_require=["pytest"],
    test_suite='gillcup.test.run',
)
