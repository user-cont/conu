def transport_param(index, repository, tag, path=None):
    """
    Parses info into skopeo parameter
    :param index: index in transports list, kinda temporary
    :param repository: docker repository
    :param tag: docker repo tag
    :param path: required for dir and docker-archive transports
    :return: string. skopeo parameter specifying image
    """
    transports = ["containers-storage:",
                  "dir:",
                  "docker://",
                  "docker-archive",
                  "docker-daemon:",
                  "oci:",
                  "ostree:"]

    if not 0 <= index < len(transports):
        raise ValueError("Invalid source transport index: " + str(index))
    command = transports[index]
    if index in [1, 3, 5] and path is None:
        raise ValueError(transports[index] + " path is required to be specified")
    if index == 1:
        return command + path
    if index == 3:
        command += path
        if repository is None:
            return command
        command+=":"
    if index in [0, 2, 3, 4]:
        return command + repository + ":" + tag
    if index == 5:
        return command + path + ":" + tag
    raise NotImplementedError(transports[index] + "transport is not implemented yet")
