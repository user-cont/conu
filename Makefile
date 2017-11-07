.PHONY: install-dependencies test ci-test clean install source container

install-dependencies:
	./requirements.sh

test:
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

container:
	docker build --tag=modularitycontainers/conu .
