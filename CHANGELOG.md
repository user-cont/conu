# 0.7.1

## Breaking changes

* conu is now supported on python 3.6+ only.


# 0.7.0

## New features

* Parameter `project` is now optional in all OpenShift backend app deployment methods. Application is now deployed in currently used project of OpenShift cluster by default.
* You are now able to create new `Pod` using Kubernetes pod templates.
* Support for importing images into OpenShift registry using `oc` binary.
* Introducing `Podman` backend, thanks to @fasashen!
* Conu docker image now uses fedora 29 as a base image.


# 0.6.2

This is a bug-fix release to fix the RPM packaging in Fedora.

## Fixes

* Conu can now be built as an RPM.


# 0.6.1

This is a bug-fix release to resolve the issues with dependencies.

## Fixes

* Resolve an issue when enum34 was listed as a requirement on python 3.
* Conu can now be used in linux distributions because it no longer requires precise versions of its dependencies.


# 0.6.0

## Breaking changes

* We have split `new_app` method of origin backend to three specific methods:
    - `deploy_image` for deployment of an image.
    - `create_new_app_from_source` for deployment of applications using source-to-image from local or remote source.
    - `create_app_from_template` for deployment of applications using OpenShift templates.

## New features

* Troubleshooting and debugging of OpenShift backend is now easier because of new methods `get_logs` and `get_status`.

## Fixes

* Documentation is updated and now includes OpenShift and Kubernetes backends.
* Fixed race condition when starting docker containers via binary.
* Nspawn backend improvements:
    - Changed default image location to `/opt` to avoid issues with brtfs and using loopback device.
    - Do not use pull-raw and importing via machinectl.
    - Test suite improvements.


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
