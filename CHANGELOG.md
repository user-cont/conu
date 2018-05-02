# 0.3.0

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
