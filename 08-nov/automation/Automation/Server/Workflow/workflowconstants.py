# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by Workflow test cases"""

import os

import AutomationUtils.constants as AC


WORKFLOWS = os.path.join(AC.AUTOMATION_DIRECTORY, 'Server', 'Workflow', 'Workflows')
"""str:     Path for the location of the Workflows"""

ACTIVITIES = os.path.join(AC.AUTOMATION_DIRECTORY, 'Server', 'Workflow', 'Activities')
"""str:     Path for the location of the Workflow custom activities"""

WORKFLOW_DEPENDENCY_MAP = {
    'common_workflows':["wf_email", "wf_pause"],

    'wf_acquire_lock_parent': {'Child': ["wf_acquire_lock_child"],},
    'wf_drive': {'Child': ["wf_log_event"],},
    'wf_library_operations': {'Child': ["wf_log_event", "wf_qcommands_create"],},
    'wf_job_control': {'Child': ["wf_log_event", "wf_qcommands_create"],},
    'wf_modify': {'Child': ["wf_log_event", "wf_qcommands_create"],'Activities': ["ListGlobalFilters"],},
    'wf_media': {'Child': ["wf_log_event"],},
    'wf_qcommand_operations': {'Child': ["wf_qcommands_create"],},
    'wf_qcommands_create': {'Activities': ["CreateBackupset"],},
    'wf_replication': {'Child': ["wf_log_event"],},
    'wf_respond_to_caller_parent': {'Child': ["wf_respond_to_caller_child"],},
    'wf_result_sets': {'Child': ["wf_log_event"],},
    'wf_user_administration': {
        'Child': ["wf_log_event"],
        'Activities': ["UserCreate_CMD",
                       "UserCreate_REST",
                       "UserCreate_XML",
                       "UserDelete",
                       "UserList",]
    },
    'wf_client_operations': {'Activities': ["CreateClientGroup", "DeleteClientGroup",]},
    'wf_miscellaneous': {'Child': ["wf_conditional_loop_test"],},
    'wf_logging': {'Child': ["wf_conditional_loop_test"],},
    'wf_utilities': None,
    'wf_db_operations': None,
    'wf_conditional_loop_test': None,
    'WF_HashFile': None,
    'wf_web_services': None,
    'wf_bl_delete_backupset': None,
    'wf_foreach_json': None,
    'wf_foreachxml_switchtojob': None,
    'wf_email_commserver': None,
    'wf_file_upload_operations': None,
    'wf_wizard_block': None,
    'wf_credential_manager': None,
    'deleteclientauthorization': {'Child': ["getandprocessauthorization"]},
    'deleteclientauthorizationapi': {'Child': ["getandprocessauthorization"]},
    'multiplemessagenames': None,
    'wf_httpclient_basic': None
}
"""str:     Embedded workflows and workflow custom activities mapping
            Common workflows will be deployed first followed by Child workflows
            Child workflows will be deployed in the order they are defined"""

WORKFLOW_DEFAULT_USER_INPUTS = "<inputs><requestedBy>%s</requestedBy><objectName/><CustomMessage/></inputs>"
''' Default inputs to BL workflow test cases. Declared here as it's used by multiple testcases '''