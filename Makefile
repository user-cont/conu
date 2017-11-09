.PHONY: install-dependencies exec-test check container build-test-container test

CONU_REPOSITORY := docker.io/modularitycontainers/conu
TEST_IMAGE_NAME := conu-tests
TEST_TARGET := "./tests"

install-dependencies:
	./requirements.sh

# FIXME: run both, fail if any failed -- I am not good makefile hacker
exec-test:
	PYTHONPATH=$(CURDIR) pytest-2 -vv $(TEST_TARGET)
	PYTHONPATH=$(CURDIR) pytest-3 -vv $(TEST_TARGET)

check: test

# jenkins doesn't seem to cope well with the docker's networing magic:
#   dnf and `docker pull` malfunctions -- timeouts, network errors
container:
	docker build --network host --tag=$(CONU_REPOSITORY) .

build-test-container: container
	docker build --network host --tag=$(TEST_IMAGE_NAME) -f ./Dockerfile.tests .

test: build-test-container test-in-container

test-in-container:
	docker run --net=host --rm -v /dev:/dev:ro -v /var/lib/docker:/var/lib/docker:ro --security-opt label=disable --cap-add SYS_ADMIN -ti -v /var/run/docker.sock:/var/run/docker.sock -v ${PWD}:/src $(TEST_IMAGE_NAME) make exec-test TEST_TARGET=$(TEST_TARGET)
