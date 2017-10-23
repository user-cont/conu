.PHONY: install-dependencies test ci-test clean install source

install-dependencies:
	./requirements.sh

deps:
	dnf -q -y install python2-pytest python3-pytest python2-docker python3-docker

test: deps install
	PYTHONPATH=${PWD} pytest-2 -vv
	PYTHONPATH=${PWD} pytest-3 -vv

# run in travis
ci-test:
	PYTHONPATH=${PWD} pytest -m "not requires_atomic_cli" -vv

clean:
	@python setup.py clean
	git clean -fd

install: clean
	@python setup.py install

source: clean
	@python setup.py sdist
