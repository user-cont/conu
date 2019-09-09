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

"""
utility functions for related to buildah
"""
import logging

from conu import ConuException
from conu.utils import graceful_get

logger = logging.getLogger(__name__)


def buildah_common_inspect_to_metadata(metadata_object, inspect_data):
    """
    :param metadata_object: instance of conu.Metadata object
    :param inspect_data: dict with the inspect metadata
    """
    ociv1 = inspect_data.get("OCIv1")
    if not ociv1:
        raise ConuException("inspect metadata are invalid: don't have OCIv1 section")
    raw_env_vars = graceful_get(ociv1, "config", "Env") or []
    if raw_env_vars:
        metadata_object.env_variables = {}
        for env_variable in raw_env_vars:
            splits = env_variable.split("=", 1)
            name = splits[0]
            value = splits[1] if len(splits) > 1 else None
            if value is not None:
                metadata_object.env_variables.update({name: value})

    metadata_object.labels = graceful_get(ociv1, "config", "Labels", default={})
    metadata_object.command = graceful_get(ociv1, 'config', 'Cmd')
    metadata_object.creation_timestamp = graceful_get(ociv1, "created")
