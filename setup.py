
from setuptools import setup, find_packages

setup(
    name='gillcup',
    version='0.1',
    packages=find_packages(),

    description=u"""A simple animation framework.
    """,
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    install_requires=[
            "pyglet>=1.1.4",
        ],
)
