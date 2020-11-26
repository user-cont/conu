# -*- coding: utf-8 -*-
#
# Copyright Contributors to the Conu project.
# SPDX-License-Identifier: MIT
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
