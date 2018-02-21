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

from six.moves.urllib.parse import urlunsplit


class HttpClient:
    """
    Utility class for easier http connection.
    """

    def __init__(self, host, port, session):
        self.host = host
        self.port = port
        self.session = session

    def _get_url(self, path):
        return urlunsplit(
            ("http", "%s:%s" % (self.host, self.port), path, "", "")
        )

    def get(self, path, *kwargs):
        url = self._get_url(path)
        return self.session.get(url, *kwargs)

    def post(self, path, *kwargs):
        url = self._get_url(path)
        return self.session.post(url, *kwargs)
