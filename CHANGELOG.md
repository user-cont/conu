# 0.6.0

* Automatic update of dependency pytest from 3.9.1 to 3.9.2
* address codacy warnings
* various QoL changes to probes:
* test_container_create_failed: enable debug logs
* test_cleanup_containers: mark comment with FIXME
* dkr,run_container: ensure that cid file is populated
* make,test: print full stack trace
* Automatic update of dependency requests from 2.19.1 to 2.20.0
* add labels to release-conf.yaml
* Automatic update of dependency docker from 3.5.0 to 3.5.1
* remove commented out lines
* Automatic update of dependency pytest from 3.8.2 to 3.9.1
* use logger.debug for debugging
* better UX for importin K8s and OpenShift backend
* curl has to follow symlinks and raise error, instead of downloading some error page
* specify string format arguments as logging function parameters
* update tests, docs and examples according to new openshift functionality
* all_pods_are_ready in openshift backend
* split oc new-app to independent methods
* add logs and status to origin backend
* move hardcoded NAME and NAMESPACE setup from origin backend
* add port option to request service
* create method for start-build
* add option to delete all objects in clean_project method
* use random string generator from conu.utils
* create new registry module
* add token to login_to_registry
* fix suggestion in PR
* improved vagrant file to cover all requirements for all pythons
* make nspawn backend already working there were several changes what caused troubles  * another test image location  * do not use pull-raw and importing via machinectl, because nobody uses it and causes troubles,    after dicsussion with systemd devels it is better to do it in own way  * imrpove tesing of output added chars decode from stdout
* req.sh: reorder for clarity, update comment, remove make
* Automatic update of dependency pytest from 3.8.1 to 3.8.2
* skip origin and k8s tests if there is no OpenShift installed or running
* minor fixes
* fix name of packege in dnf install
* Update CONTRIBUTING.md
* add Dockerfile to build docs in container
* minor fixes in documentation
* update README.md
* update documentation
* wait until API tokens are generated in new namespace, remove time.sleep from all kubernetes tests
* use Probe for oc start-build command
* Automatic update of dependency pytest from 3.8.0 to 3.8.1
* Update release-conf.yaml
* move get_token to utils, make login to registry static
* Automatic update of dependency pytest from 3.7.4 to 3.8.0
* remove pyxattr, make it optional
* req.sh: remove workaround for F27 pyxattr rename
* change order of commands in test-requirements.sh
* update CHANGELOG.md, turn off firewall CI
* get_internal_registry() method in origin backend
* install origin from github
* comments in openshift template example
* increase timeout in openshift tests
* CI using openshift cluster, examples and test updated
* fix client.py

# 0.5.0

## New Features

* Docker image now have method `run_via_api()`
* We have introduced OpenShift `origin` and Kubernetes `k8s` backends.
* Support for three k8s primitives - `Pod`, `Service`, `Deployment`
* CentOS CI, thanks to @jpopelka
* Docker backend now has `push()` and `login()` methods
* Origin backend has `oc_new_app()` method
* Automatic updates of dependencies using [kebechet bot](https://github.com/thoth-station/kebechet), thanks to @fridex
* Codacy hook, thanks to @lachmanfrantisek
* Examples for origin and k8s backends

## Fixes
* [Use Popen in run_cmd and pipe outputs to logger](https://github.com/user-cont/conu/pull/263), thanks to @SkullTech


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
