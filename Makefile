.PHONY: install-requirements install-test-requirements exec-test check container build-test-container test docs open-docs

CONU_REPOSITORY := docker.io/usercont/conu:dev
TEST_IMAGE_NAME := conu-tests
DOCS_IMAGE_NAME := conu-docs
DOC_EXAMPLE_PATH := "docs/source/examples"
VERSION := 0.4.0

install-requirements:
	./requirements.sh

install-test-requirements:
	./test-requirements.sh

# FIXME: run both, fail if any failed -- I am not good makefile hacker
exec-test:
	cat pytest.ini
	@# use it like this: `make exec-test TEST_TARGET="tests/unit/"`
	PYTHONPATH=$(CURDIR) pytest-2 $(TEST_TARGET)
	PYTHONPATH=$(CURDIR) pytest-3 $(TEST_TARGET)

check: test

build-docs-container:
	docker build --network host --tag=$(DOCS_IMAGE_NAME) -f ./Dockerfile.docs .

docs-in-container: build-docs-container
	docker run --net=host --rm -v $(CURDIR):/src -ti $(DOCS_IMAGE_NAME) bash -c "pip3 install . && make docs"

docs:
	make -C docs/ html

docs/build/html/index.html: docs

open-docs: docs/build/html/index.html
	xdg-open docs/build/html/index.html

# jenkins doesn't seem to cope well with the docker's networing magic:
#   dnf and `docker pull` malfunctions -- timeouts, network errors
container-image:
	docker build --network host --tag=$(CONU_REPOSITORY) .

container:
	docker run --rm -ti -v /run/docker.sock:/run/docker.sock $(CONU_REPOSITORY) bash

build-test-container:
	docker build --network host --tag=$(TEST_IMAGE_NAME) -f ./Dockerfile.tests .

# You have to run 'sudo make install-test-requirements' prior to this.
test: build-test-container test-in-container test-doc-examples

centos-ci-test: install-test-requirements container-image build-test-container test-in-container

test-in-container:
	@# use it like this: `make test-in-container TEST_TARGET=tests/integration/test_utils.py`
	$(eval kubedir := $(shell mktemp -d /tmp/tmp.conu-kube-XXXXX))
	sed -e s#"${HOME}"#/root#g ${HOME}/.kube/config > $(kubedir)/config
	docker run --net=host --rm -v /dev:/dev:ro -v /var/lib/docker:/var/lib/docker:ro --security-opt label=disable --cap-add SYS_ADMIN -ti -v /var/run/docker.sock:/var/run/docker.sock -v $(CURDIR):/src -v $(CURDIR)/pytest-container.ini:/src/pytest.ini -v $(kubedir):/root/.kube $(TEST_IMAGE_NAME) make exec-test TEST_TARGET=$(TEST_TARGET)

test-in-vm:
	vagrant up --provision

test-doc-examples: install
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
	rpmbuild ./*.spec -bb --define "_sourcedir $(CURDIR)" --define "_specdir $(CURDIR)" --define "_builddir $(CURDIR)" --define "_srcrpmdir $(CURDIR)" --define "_rpmdir $(CURDIR)"

srpm: sdist
	rpmbuild ./*.spec -bs --define "_sourcedir $(CURDIR)" --define "_specdir $(CURDIR)" --define "_builddir $(CURDIR)" --define "_srcrpmdir $(CURDIR)" --define "_rpmdir $(CURDIR)"

rpm-in-mock-f28: srpm
	mock --rebuild -r fedora-28-x86_64 ./*.src.rpm

rpm-in-mock-el7: srpm
	mock --rebuild -r epel-7-x86_64 ./*.src.rpm

install-conu-rpm-in-centos-container: rpm-in-mock-el7
	docker run -v "/var/lib/mock/epel-7-x86_64/result:/conu" -ti centos:7 bash -c " \
		yum install -y /conu/python2-conu-*.el7.centos.noarch.rpm && \
		python2 -c 'import conu; print conu.version'"

encrypt-password-in-travis-yml:
	docker run -ti --rm -v $(CURDIR):/src -w /src docker.io/tianon/travis-cli travis encrypt --add deploy.password -r fedora-modularity/conu $(THE_PASSWORD)

clean:
	git clean -dfx

install: clean install-requirements
	pip install --user .

uninstall:
	pip uninstall .
	rm /usr/lib/python*/site-packages/conu\* -rf

test-nspawn-vagrant:
	vagrant up
	vagrant destroy
