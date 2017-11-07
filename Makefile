.PHONY: install-dependencies exec-test check container build-test-container test

CONU_REPOSITORY := docker.io/modularitycontainers/conu
TEST_IMAGE_NAME := conu-tests

install-dependencies:
	./requirements.sh

# FIXME: run both, fail if any failed -- I am not good makefile hacker
exec-test:
	PYTHONPATH=$(CURDIR) pytest-2 -vv
	PYTHONPATH=$(CURDIR) pytest-3 -vv

check: test

container:
	docker build --tag=$(CONU_REPOSITORY) .

build-test-container: container
	docker build --tag=$(TEST_IMAGE_NAME) -f ./Dockerfile.tests .

test: build-test-container
	docker run --rm -v /dev:/dev:ro -v /var/lib/docker:/var/lib/docker:ro --security-opt label=disable --cap-add SYS_ADMIN -ti -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/src $(TEST_IMAGE_NAME) make exec-test
