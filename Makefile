.PHONY: install-dependencies exec-test check container build-test-container test

CONU_REPOSITORY := docker.io/modularitycontainers/conu
TEST_IMAGE_NAME := conu-tests
DOC_EXAMPLE_PATH := "docs/source/examples"

install-dependencies:
	./requirements.sh

# FIXME: run both, fail if any failed -- I am not good makefile hacker
exec-test:
	cat pytest.ini
	@# use it like this: `make exec-test TEST_TARGET="tests/unit/"`
	PYTHONPATH=$(CURDIR) pytest-2 $(TEST_TARGET)
	PYTHONPATH=$(CURDIR) pytest-3 $(TEST_TARGET)

check: test

# jenkins doesn't seem to cope well with the docker's networing magic:
#   dnf and `docker pull` malfunctions -- timeouts, network errors
container:
	docker build --network host --tag=$(CONU_REPOSITORY) .

build-test-container:
	docker build --network host --tag=$(TEST_IMAGE_NAME) -f ./Dockerfile.tests .

test: build-test-container test-in-container test-doc-examples

test-in-container:
	@# use it like this: `make test-in-container TEST_TARGET=tests/integration/test_utils.py`
	docker run --net=host --rm -v /dev:/dev:ro -v /var/lib/docker:/var/lib/docker:ro --security-opt label=disable --cap-add SYS_ADMIN -ti -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/src -v ${PWD}/pytest-container.ini:/src/pytest.ini $(TEST_IMAGE_NAME) make exec-test TEST_TARGET=$(TEST_TARGET)

test-doc-examples:
	for file in $$(ls $(DOC_EXAMPLE_PATH)) ; do \
		echo "Checking example file $$file" ; \
		PYTHONPATH=$(CURDIR) python2 $(DOC_EXAMPLE_PATH)/$$file || exit ; \
		PYTHONPATH=$(CURDIR) python3 $(DOC_EXAMPLE_PATH)/$$file || exit ; \
	done

check-pypi-release:
	PYTHONPATH=$(CURDIR) pytest -m "release_pypi" ./tests/release/test_release.py

check-copr-release:
	PYTHONPATH=$(CURDIR) pytest -m "release_copr" ./tests/release/test_release.py

sdist:
	./setup.py sdist -d .

rpm: sdist
	rpmbuild ./*.spec -bb --define "_sourcedir ${PWD}" --define "_specdir ${PWD}" --define "_builddir ${PWD}" --define "_srcrpmdir ${PWD}" --define "_rpmdir ${PWD}"

srpm: sdist
	rpmbuild ./*.spec -bs --define "_sourcedir ${PWD}" --define "_specdir ${PWD}" --define "_builddir ${PWD}" --define "_srcrpmdir ${PWD}" --define "_rpmdir ${PWD}"

rpm-in-mock-f27: srpm
	mock --rebuild -r fedora-27-x86_64 ./*.src.rpm

rpm-in-mock-el7: srpm
	mock --rebuild -r epel-7-x86_64 ./*.src.rpm

install-conu-in-centos-container: rpm-in-mock-el7
	docker run -v "/var/lib/mock/epel-7-x86_64/result:/conu" -ti centos:7 bash -c " \
		yum install -y /conu/python2-conu-*.el7.centos.noarch.rpm && \
		python2 -c 'import conu; print conu.version'"
