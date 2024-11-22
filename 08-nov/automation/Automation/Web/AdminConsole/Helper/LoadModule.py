# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils import logger


def load_module(module, path):
    """Loads the module from the given path."""

    log = logger.get_log()

    import importlib.util
    try:
        # find_module returns the file, path and description
        spec = importlib.machinery.PathFinder().find_spec(module, [path])
        return spec.loader.load_module()

    except Exception as exp:
        log.exception("Exception in load_module {0}".format(str(exp)))
        raise Exception(exp)
