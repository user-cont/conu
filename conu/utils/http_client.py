# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
