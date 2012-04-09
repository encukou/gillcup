
from setuptools import setup, find_packages

setup(
    name='gillcup_graphics',
    version='0.1.0-alpha.0',
    packages=find_packages(),

    description="""Pyglet graphics for Gillcup""",
    author='Petr Viktorin',
    author_email='encukou@gmail.com',
    install_requires=['gillcup>=0.2', 'pyglet>=1.1.4'],
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

    tests_require=['pytest', 'numby>=1.6'],
    test_suite='gillcup_graphics.test.run',
)
