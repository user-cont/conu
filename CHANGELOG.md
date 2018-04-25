# 0.3.0

TBD


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
