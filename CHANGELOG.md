# 0.5.0

* return logs in pod get_logs() method
* docs for new methods in Pod class
* remove logs exception, update pod example
* pod example
* pod logs and change test image to nginx
* pod readiness
* Allow release-bot to make PRs based on issues
* Automatic update of dependency pytest from 3.7.3 to 3.7.4
* Automatic update of dependency pytest from 3.7.2 to 3.7.3
* [README.md] Add build status badge
* pytest.mark.xfail test_cleanup_containers()
* Automatic update of dependency pytest from 3.7.1 to 3.7.2
* Make test_run_cmd faster.
* Flip the order of operands in assert statements
* Add integration test for run_cmd
* Properly handle commands returning non-zero exit codes
* [Makefile] centos-ci-test depends on container-image
* Use Popen in run_cmd and pipe outputs to logger
* req.sh: document the need for gcc and -devel
* Automatic update of dependency docker from 3.4.1 to 3.5.0
* install gcc & py-dev since we pin reqs
* docstring to login, project parameter in new_app is now required
* api key
* add api_client
* code cleaning
* change app name back bacause of unsupported chars
* rename login_registry to login_to_registry, fix doctrings
* Add missing docstrings
* add __init__.py to origin backend
* add OpenShift example to README.md
* add some logs and clean just app objects
* remove leftovers
* add spec to service constructor
* clean project
* openshift examples
* tests for openshift backend
* http request to service
* oc new-app
* openshift login and push to registry
* openshift backend class
* docker login
* docker push
* Adjust setup.py to work properly with Kebechet
* Initial dependency lock
* [DockerImage:pull()] decode JSON data into dicts
* test for cleanup
* move cleanup value check to constructor of container Backend
* move cleanup value check to constructor of K8sBackend
* rename property namespaces to managed_namespaces in k8s backend
* Use Kebechet for dependency management
* k8s cleanup policy enum and cleanup methods
* docstrings fixed
* remove trailing new line
* add logging for namespace creation/deletion
* add Kubernetes example
* template support for deployment
* get global API instance in service.py
* add missing docstrings
* Makefile test-in-container now use minikube, kubernetes version compatible with python client, remove pytest xfail from k8s tests
* minikube test-requirements for vm
* Empty commit to ressurect CI #2
* Empty commit to ressurect CI
* tests: dont configure logging, it's not needed
* do only one instance of a handler on particular loggger
* tests: use conu.tests logger
* white space
* more defensive parsing of port mappings
* docker,metadata: utilize inspect_to_container_metadata
* docker,networks,metadata: parse those networks properly!
* k8s,deployment: utilize get_apps_api
* fix
* singleton client
* k8s backend
* [.bandit] Ignore E0401 - Unable to import 'xyz'
* REVERT THIS ! (this is just for testing)
* [requirements.sh] move 'docker start' & 'oc cluster up' into test-requirements.sh
* Don't do oc cluster up if it's already running
* Update config files from kwaciaren
* uniform processing of docker inspect metadata
* tests: set up logging in conftest
* graceful_get: log as debug
* add digests to image metadata; better inspect -> metadata logic
* pep8: line length
* Use 'with' to create docker_backend fixture
* Comment pytest requirements
* code cleaning
* service and deployment, new Makefile target for local testing with minikube
* pod update
* service ip
* db deployment test
* service and deployment update
* first work on deployment and service
* fix test_run_with_volumes_metadata_check
* vagrantfile: start docker before running tests
* code cleaning
* add Vagrant files to gitignore
* remove unused kubedir creation
* Openshift cluster for tests
* refactor of try-catch blocks
* move run_in_pod to DockerImage class
* new value in PodPhase, fix port pasrsing, documentation
* initial implementation of Pod
* rename to k8s
* kick-off of running images in Kubernetes
* add & fixup a way to test in VM
* Make probe more quiet for INFO logging level
* Use bandit/pylintrc file from kwaciaren
* name of image inside Makefile
* documentation about healthcheck
* parse just known options
* deletion of container
* run_via_api now using Low-level API
* run_via_api, DockerParameters inherit from Container metadata
* better port parsing
* docker run parameters
* missing NotImplementedError
* get_metadata for DockerImage

# 0.4.0

## Breaking changes

* We have changed behavior of `.get_metadata` method. It now returns an
  instance of `Metadata` class. Method `.inspect` is meant to return raw data
  of the selected backend.

## New Features

* Introduction of a new class to hold [container and image
  metadata](https://github.com/user-cont/conu/blob/d19accbbc82b7a04090fc6339f4974c73f2987d6/conu/apidefs/metadata.py#L4).
  In coming weeks, we'll be working on integrating this class into the library.
  Our main intent is to make the Metadata class generic across all backends.
  * Thanks to Rado Pitonak
    ([#210](https://github.com/user-cont/conu/pulls/210),
    [#204](https://github.com/user-cont/conu/pulls/204),
    [#207](https://github.com/user-cont/conu/pulls/207))
* conu now has an API to access image layers ([#207](https://github.com/user-cont/conu/pulls/203))
* We've added [Contribution guide](https://github.com/user-cont/conu/blob/master/CONTRIBUTING.md), thanks to Rado Pitonak ([#208](https://github.com/user-cont/conu/pulls/208)).

## Fixes

* Provide docker container filesystem using `docker export` instead of `atomic
  mount` — conu no longer requires
  [atomic](https://github.com/projectatomic/atomic). This also means that root
  privileges are no longer required.
* Don't depend on `enum34` for python 3, thanks to Rado Pitonak ([#214](https://github.com/user-cont/conu/pulls/214))


# 0.3.1

## New Features

* Introduced fixtures and helper functions to simplify container testing.
* Support was added for another backend - nspawn.
* It is possible to decide cleanup policy when initializing backend.
* Methods for listing containers and images were added to both supported backends.
* Image mounting is possible also without superuser privileges.
* To represent and work with docker volumes, there is a new class `Volume`.
* `run_via_binary` accepts commands in form of list of strings
  to make running images more intuitively.
* It is possible to build image from Dockerfile using `DockerImage.build()`.
* There is a new method to check GPG signatures of RPMs in images.
* Documentation is updated, there is also asciinema demo in README.md.


# 0.2.0

Please note, that our API is still not marked stable yet.

## Breaking changes

* We have changed how `logs()` method works. It now returns iterator always. On
  top of it, we have implemented more convenience methods to return logs as
  bytes and unicode.

* Backend class can (and should) be used as a context manager. This was done
  for the sake of creating a temporary directory meant for the backend
  instance. The context manager ensures the temporary directory will be removed.

## New Features

* We added support for docker-py version 1 so it can work in CentOS.
* conu will check whether required binaries are present and if not,
  `CommandDoesNotExistException` will be raised.
* Our documentation was improved and contains now more examples and the python
  interface should be explained in more detail.
* When creating docker containers, conu now utilizes option `--cidfile`.
* `execute()` method can be blocking and non-blocking.
* Backend provides a new methos `cleanup_containers()` to cleanup containers
  created during the session.


# 0.1.0

* Initial release.
