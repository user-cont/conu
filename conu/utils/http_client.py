# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
#
from requests import Session
from six.moves.urllib.parse import urlunsplit


def get_url(path, host, port, method="http"):
    """
    make url from path, host and port

    :param method: str
    :param path: str, path within the request, e.g. "/api/version"
    :param host: str
    :param port: str or int
    :return: str
    """
    return urlunsplit(
        (method, "%s:%s" % (host, port), path, "", "")
    )


class HttpClient(Session):
    """
    Utility class for easier http connection.
    """

    def __init__(self, host, port, session):
        super(HttpClient, self).__init__()
        self.host = host
        self.port = port
        self.session = session

    def prepare_request(self, request):
        request.url = get_url(path=request.url,
                              host=self.host,
                              port=self.port)
        return super(HttpClient, self).prepare_request(request)
