def check_docker_command_works():
    """
    Verify that dockerd and docker binary works fine. This is performed by calling `docker
    version`, which also checks server API version.

    :return: bool, True if all is good, otherwise ConuException or CommandDoesNotExistException
              is thrown
    """
    try:
        out = subprocess.check_output(["docker", "version"],
                                      stderr=subprocess.STDOUT,
                                      universal_newlines=True)
    except OSError:
        logger.info("docker binary is not available")
        raise CommandDoesNotExistException(
            "docker command doesn't seem to be available on your system. "
            "Please install and configure docker."
        )
    except subprocess.CalledProcessError as ex:
        logger.error("exception: %s", ex)
        logger.error("rc: %s, output: %r", ex.returncode, ex.output)
        raise ConuException(
            "`docker version` call failed, it seems that your docker daemon is misconfigured or "
            "this user can't communicate with dockerd."
        )
    else:
        logger.info("docker environment info: %r", out)
    return True