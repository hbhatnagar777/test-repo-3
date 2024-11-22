# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Contains all WebConsole APIs using browser session, for advanced operations directly call
the core APIs from the `Core` package
"""

from AutomationUtils import config
from Web.API.Core import cvsessions
from Web.API.Core.WebConsole import (
    customreports, apps, store
)
from Web.WebConsole.Store import storeapp

_CONSTANTS = config.get_config()
_STORE_CONF = storeapp.get_store_config()


def Reports(
        machine, port=443, protocol="https",
        username=_CONSTANTS.ADMIN_USERNAME,
        password=_CONSTANTS.ADMIN_PASSWORD,
        proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
        proxy_port=_CONSTANTS.HttpProxy.PORT):
    """Builds the webconsole api with default values"""
    session = cvsessions.WebConsole(
        machine,
        port=port,
        protocol=protocol,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    session.login(username, password)
    return customreports.Reports(session)


def Apps(machine, port=443, protocol="https",
         username=_CONSTANTS.ADMIN_USERNAME,
         password=_CONSTANTS.ADMIN_PASSWORD,
         proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
         proxy_port=_CONSTANTS.HttpProxy.PORT) -> apps.Apps:
    """Builds the webconsole api with default values"""
    session = cvsessions.WebConsole(
        machine,
        port=port,
        protocol=protocol,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    session.login(username, password)
    return apps.Apps(session)


def Store(
        machine, port=443, protocol="https",
        wc_uname=_CONSTANTS.ADMIN_USERNAME,
        wc_pass=_CONSTANTS.ADMIN_PASSWORD,
        store_uname=_STORE_CONF.PREMIUM_USERNAME,
        store_pass=_STORE_CONF.PREMIUM_PASSWORD,
        proxy_machine=_CONSTANTS.HttpProxy.MACHINE_NAME,
        proxy_port=_CONSTANTS.HttpProxy.PORT) -> store.Store:
    """Builds the webconsole api with default values"""
    session = cvsessions.Store(
        machine,
        port=port,
        protocol=protocol,
        proxy_machine=proxy_machine,
        proxy_port=proxy_port
    )
    session.login(wc_uname, wc_pass, store_uname, store_pass)
    return store.Store(session)
