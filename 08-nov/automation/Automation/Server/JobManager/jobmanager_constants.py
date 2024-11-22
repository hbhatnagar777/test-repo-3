# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by JobManager test cases"""
import enum

JOB_MAP = {
    'suspend': {
        'status': 'suspended',
        'message': 'Suspending',
        'post_message': 'Suspended',
        'module': 'pause',
        'module_all': 'suspend_all_jobs',
    },
    'resume': {
        'status': 'running',
        'message': 'Resuming',
        'post_message': 'Resumed',
        'module': 'resume',
        'module_all': 'resume_all_jobs',
    },
    'kill': {
        'status': 'killed',
        'message': 'Killing',
        'post_message': 'Killed',
        'module': 'kill',
        'module_all': 'kill_all_jobs'
    }
}

''' Mapping for various module calls and message strings for corresponding job operations.'''

JOB_STATUS = {
    'client': {
        'backup': 'Data Management activity on Client [{0}] is disabled',
        'restore': 'Data Recovery activity on Client [{0}] is disabled',
    },
    'ida': {
        'backup': 'Backup activity for [{0}] on Client [{1}] is disabled',
        'restore': 'Restore activity for [{0}] on Client [{1}] is disabled',
    },
    'subclient': {
        'backup': 'Backup activity for subclient [{0}] on Client [{1}] and iDataAgent [{2}] is disabled'
    }
}

''' Mapping for various entities with corresponding operations.'''


class JobOpCode(enum.Enum):
    CONTENT_INDEXING_OPCODE = '113'
