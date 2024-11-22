# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by activity control test cases"""

ACTIVITY_MAP = {
    'backup': {
        'disable': 'disable_backup',
        'enable': 'enable_backup'
    },
    'restore': {
        'disable': 'disable_restore',
        'enable': 'enable_restore'
    },
    'data_aging': {
        'disable': 'disable_data_aging',
        'enable': 'enable_data_aging'
    }

}
''' Mapping for various activity types with corresponding activity operations.'''
