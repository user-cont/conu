# conu
__CON__ -tainers __U__ -tils

It provides low level __API__ for docker image/container testing.
It is based on bash commands because primary target is to __test it
as customers will__ use it.
That's why it does not use python docker bindings.
It provides python classes for:
- __docker__ module
  - __Image__ - image handling
  - __Container__ - docker container handling
- __utils__ module
  - __Volume__ - it is mktemd utility on steroids
  - __Probe__ - provides, simple port/file checks and waiting for this events

# Installation

## Prerequisites
- system packages providing binaries: `docker`, `setfacl`, `chmod`, `chcon`
```
$ dnf -y install acl coreutils docker
```
- python modules inside: No specific requirements now

## From source Code
- Commands in git directory:
```
$ sudo make install
```

## COPR repo
- Enable copr repo
```
dnf -y copr enable __MISSING__
```
- Install package
```
dnf -y install conu
```

# How to use it

 - self test examples
  - docker [seltest](/conu/docker/selftest.py)
  - utils [selftest](/conu/utils/selftest.py)
 - real life examples
  - collection postgres [examples](/examples/scl_postgres)  ( usage: `dnf -y install avocado; make`)