# Contributing Guidelines

Thanks for your interest in contributing to `conu`.

The following is a set of guidelines for contributing to `conu`.
Use your best judgement, and feel free to propose changes to this document in a pull request.


## Reporting Bugs
Before creating bug reports, please check a [list of known issues](https://github.com/user-cont/conu/issues) to see
if the problem has already been reported (or fixed in a master branch).

If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/user-cont/conu/issues/new).
Be sure to include a **descriptive title and a clear description**. Ideally, please provide:
 * version of conu you are using (`rpm -q python2-conu python3-conu` or `pip freeze | grep conu`)
 * version of container runtime you are using (`rpm -qa | grep docker`)
 * the command you executed, output and ideally please describe the image, container that you are trying to test

If possible, add a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

**Note:** If you find a **Closed** issue that seems like it is the same thing that you're experiencing, open a new issue and include a link to the original issue in the body of your new one. You can also comment on the closed issue to indicate that upstream should provide a new release with a fix.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.
When you are creating an enhancement issue, **use a clear and descriptive title**
and **provide a clear description of the suggested enhancement**
in as many details as possible.

## Guidelines for Developers

If you would like to contribute code to the `conu` project, this section is for you!

### Is this your first contribution?

Never contributed to an open-source project before?  No problem!  We're excited that you are considering `conu` for your first contribution!

Please take a few minutes to read GitHub's guide on [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/).  It's a quick read, and it's a great way to introduce yourself to how things work behind the scenes in open-source projects

### Dependencies

[Kebechet](https://github.com/thoth-station/kebechet) bot keeps our python dependencies fresh and up-to-date. If you want to change or add new dependency please edit [requirements.in](/requirements.in), **not** `requirements.txt`, because it is updated automatically based on `requirements.in`.

### Documentation

If you want to update documentation, find corresponding file in [docs](/docs) folder. If you want to try changes locally use:
```
make docs-in-container
```
and then documentation can be find in */docs/build/html*.

### Testing

For testing, we are using [pytest](https://docs.pytest.org/en/latest/) framework. Tests are stored in the [tests](/tests) directory. We recommend to run tests inside docker container using:
```
# if TEST_TARGET is empty whole test suite is executed
make test-in-container TEST_TARGET=<PATH>
```

Substitute `<PATH>` with path to specific file, for example:
```
make test-in-container TEST_TARGET=tests/integration/test_k8s.py
```

You may need to install some test dependencies, check [test-requirements](/test-requirements.sh) for more information.

### Makefile

Here are some important and useful directives of [Makefile](/Makefile):

Install conu locally:
```
make install
```

Uninstall conu from the system:
```
make uninstall
```

Build new conu docker image:
```
make container-image
```

Run test suite inside docker container:
```
make test-in-container
```

Build documentation locally:
```
make docs-in-container
```

Run whole CI build (recommended on fresh CentOS Virtual machine):
```
make centos-ci-test
```

Install test requirements:
```
make install-test-requirements
```

### How to contribute code to conu

1. Create a fork of the `conu` repository.
2. Create a new branch just for the bug/feature you are working on.

   - If you want to work on multiple bugs/features, you can use branches to keep them separate, so that you can submit a separate Pull Request for each one.

3. Once you have completed your work, create a Pull Request, ensuring that it meets the requirements listed below.

### Requirements for Pull Requests

* Please create Pull Requests against the `master` branch.
* Please make sure that your code complies with [PEP8](https://www.python.org/dev/peps/pep-0008/).
* One line should not contain more than 100 characters.
* Make sure that new code is covered by a test case (new or existing one).
* We don't like [spaghetti code](https://en.wikipedia.org/wiki/Spaghetti_code).
* The tests have to pass.

Thank you!
conu team.