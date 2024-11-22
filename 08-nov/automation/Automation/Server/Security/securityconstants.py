# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by Security related operations."""

AUTH_MAP = {
    'disable': {
        'message': 'Disabling',
        'post_message': 'Disabled',
        'module': 'disable_auth_code',
    },
    'enable': {
        'message': 'Enabling',
        'post_message': 'Enabled',
        'module': 'enable_auth_code',
    }
}

''' Mapping for various module calls and message strings for corresponding auth code operations.'''

BLACKLIST_USER_GROUP = "Auto_BlackListedUserGroup"
''' Blacklist user group name '''

SQLiteDB = "tableforsecurity.sqlite"
