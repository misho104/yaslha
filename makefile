.PHONY: clean relax

relax:
	@echo This make file is only for cleaning and testing.
	@echo Use setup.py to install. \(\"python ./setup.py install\"\)

clean:
	python setup.py clean
	rm -rf yaslha.egg-info htmlcov .coverage yaslha/__pycache__ yaslha/tests/__pycache__ build dist

.PHONY: test unittest typetest formattest
test: unittest typetest formattest

unittest:
	@echo "# Performing the tests..."
	nosetests --config="" --cover-package=yaslha --with-coverage
	@echo

typetest:
	@echo "# Checking typing by mypy..."
	mypy --strict yaslha/*.py
	@echo

formattest:
	@echo "# Checking PEP format..."
	flake8 --max-line-length=120 .
	@echo


