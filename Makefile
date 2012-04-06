
.PHONY: install-tools pytest pylint tox docs

all: pytest pylint tox docs
	coverage report

install-tools:
	pip install pytest pytest-cov pytest-pep8 tox

pytest: install-tools
	py.test gillcup -v --pep8 --cov gillcup --cov-report=term --cov-report=html && echo ok

pylint: install-tools
	pylint gillcup --rcfile .pylintrc

docs:
	cd docs && $(MAKE) html

tox: pytest
	tox
