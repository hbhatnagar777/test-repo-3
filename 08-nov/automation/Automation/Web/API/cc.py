# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Contains all CommandCenter APIs using browser session, for advanced operations directly call
the core APIs from the `Core` package
"""

from AutomationUtils import config
from Web.API.Core import cvsessions
from Web.API.Core.CommandCenter import (
    reports, apps
)

_CONSTANTS = config.get_config()


def Reports(
        machine, port=443, protocol="https",
        username=_CONSTANTS.ADMIN_USERNAME,
        password=_CONSTANTS.ADMIN_PASSWORD,
        proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
        proxy_port=_CONSTANTS.HttpProxy.PORT):
    """Builds the CommandCenter Reports api with default values"""
    session = cvsessions.CommandCenter(
        machine,
        port=port,
        protocol=protocol,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    session.login(username, password)
    return reports.Reports(session)


def Apps(machine, port=443, protocol="https",
         username=_CONSTANTS.ADMIN_USERNAME,
         password=_CONSTANTS.ADMIN_PASSWORD,
         proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
         proxy_port=_CONSTANTS.HttpProxy.PORT) -> apps.Apps:
    """Builds the CommandCenter Apps api with default values"""
    session = cvsessions.CommandCenter(
        machine,
        port=port,
        protocol=protocol,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    session.login(username, password)
    return apps.Apps(session)
