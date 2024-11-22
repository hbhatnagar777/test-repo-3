# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for Teer Icon identification from Command Center
"""
from selenium.webdriver.remote.webelement import WebElement

ICON_MAP = {
    '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 '
    '0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c'
    '.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"></path>': 'globe',

    '<path d="M13.34 6.77a.6.6 0 0 0-.6.6v7.09H3.26V7.37a.6.6 0 0 0-1.2 0v7.68a.6.6 0 0 0 .6.6h10.68a.6.6 0 0 0 '
    '.6-.6V7.37a.6.6 0 0 0-.6-.6Z"></path><path d="M15.77 6.41 8.33.48a.59.59 0 0 0-.75 0L.22 6.41a.64.64 0 0 '
    '0-.22.4.66.66 0 0 0 .13.45.6.6 0 0 0 .87.08l7-5.63 7 5.64a.64.64 0 0 0 .37.13.6.6 0 0 0 .37-1.07Z"></path>':
        'home',

    '<path d="M5 1v23h15V1H5zm8 19h-2v-2h2v2zm5-11H7V8h11v1zm0-2H7V6h11v1zm0-2H7V4h11v1z"></path>': 'workload'
}


# todo: store the hash as key instead of full innerhtml


def get_icons_mapping():
    """
    function to store and retrieve icon mapping cache
    """
    # returning hardcoded for now
    # todo: read from https://git.commvault.com/eng/ui/teer/-/tree/master/src/icons/src/svg once copied locally
    return ICON_MAP


def get_icon_name(svg_elem: WebElement):
    """
    function to identify icon name from svg element

    Args:
        svg_elem    (WebElement)    -   the selenium webelement <svg>
    Returns:
        name    (str)               -   name of the icon
    """
    return get_icons_mapping().get(
        svg_elem.get_attribute('innerHTML').strip(),
        'unknown icon'
    )
