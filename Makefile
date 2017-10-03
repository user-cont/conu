.PHONY: check clean install source help

check:
	PYTHONPATH=${PWD} pytest-2 -vv
	PYTHONPATH=${PWD} pytest-3 -vv

# run in travis
ci-check:
	PYTHONPATH=${PWD} pytest -m "not requires_atomic_cli" -vv

clean:
	@python setup.py clean
	git clean -fd

install: clean
	@python setup.py install

source: clean
	@python setup.py sdist


help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo " help                    show this text"
	@echo " clean                   remove python bytecode and temp files"
	@echo " install                 install program on current system"
	@echo " source                  create source tarball"
	@echo " check                   run test suite using python 2 and 3"

