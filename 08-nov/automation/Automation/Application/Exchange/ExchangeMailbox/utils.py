# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Main file containing generic utilities like FileOperations, XML formatting,
    string formatting etc...
"""

import os
import logging
import time
from datetime import datetime
from time import strftime, localtime
from dateutil import tz

from Application.Exchange.ExchangeMailbox.constants import EXCHMB_REG_FOLDER
from AutomationUtils.constants import LOG_DIR
from Web.Common.page_object import TestStep

test_step = TestStep()


def calculate_duration(received_time):
    """Returns the number of days between received time and
    local time

        Args:
            received_time (EWS) -- Message received time

        returns:
            no_of_days (int)   - duration of days"""

    # Fetching time and converting GMT to local time
    local_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    received_time = datetime.strptime(
        str(received_time).split('+')[0], "%Y-%m-%d %H:%M:%S")
    received_time = received_time.replace(tzinfo=from_zone)
    received_time = received_time.astimezone(to_zone)
    local_time = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S")
    local_time = local_time.replace(tzinfo=to_zone)
    local_time = local_time.astimezone(to_zone)

    no_of_days = abs((local_time - received_time).days)
    return no_of_days


def create_config_file(testcase_id):
    """Configuration for logging file. This logging file is used to print
    Exchange properties of every message item.

        Args:
            testcase_id -- Test Case ID"""

    filename = os.path.join(LOG_DIR, "{}_helper.log".format(testcase_id))
    logging.basicConfig(
        filename=filename,
        level=logging.DEBUG,
        format='%(message)s')

    with open(filename, 'w'):
        pass
    logging.info("*********************************************************************")


def get_mailbox_guid(mailbox_name, subclient_id, csdb):
    """Method to get mailbox guid of mailbox
        Args:
            mailbox_name  (str)  --  Mailbox name associated to subclient
            subclient_id  (int)  --  subclient id
            csdb                 --  csdb object

        Returns:
            mailbox_guid (str) -- mailbox guid of mailbox"""
    _query = ("select userguid from APP_EmailConfigPolicyAssoc where "
              "subClientId = '%s'and displayName = '%s'" % (subclient_id, mailbox_name))

    csdb.execute(_query)
    mailbox_guid = csdb.fetch_one_row()
    return mailbox_guid[0]


def create_automation_registry(ida_machine):
    """
        Method to create the Test Automation registry on the proxy machine

        Arguments:
            ida_machine       (object)--  Machine class instance for the proxy machine

        Returns:
            None
    """
    automation_key_name = "nRunDiscoveryAutomation"
    automation_key_folder = EXCHMB_REG_FOLDER

    key_path = automation_key_folder + "\\" + automation_key_name

    if ida_machine.check_registry_exists(key=key_path):
        ida_machine.remove_registry(key=key_path)

    ida_machine.create_registry(key=automation_key_folder, value=automation_key_name, data=1, reg_type="DWord")


def create_automation_mailbox_file(machine, mailbox_list):
    """
        Method to write the list of mailboxes to the Test Automation File
        Arguments:
            machine         (object)--     Machine class instance for the Proxy machine
            mailbox_list    (list)--        List of mailboxes to write to the file
    """
    file_name = "testautombxlist.txt"
    file_location = r"C:\testautombxlist.txt"

    if machine.is_file(path=file_location) == "True":
        machine.delete_file(file_path=file_location)

    machine.create_file(file_path=file_location, content="\n".join(mailbox_list))


def verify_mailbox_guids_association(csdb_mailbox_guid, ad_guid_list):
    """
        Method to verify that the GUIDs for an associated mailbox in the CSDB
        Is same as the corresponding GUID in the AD Server ( OnPrem AD or Azure AD server)

        Arguments:
            csdb_mailbox_guid       (list)--    List of GUIDs fetched from CSDB
            ad_guid_list            (list)--    List of GUIDs as read from the AD Server

        Returns:
            verf_status             (bool)--    Whether the two list of GUID match up or not
    """
    import collections
    return collections.Counter(ad_guid_list) == collections.Counter(csdb_mailbox_guid)


def is_mailbox_cache_valid(exmb_client):
    """
        Function to verify whether the mailbox cache for the exchange client
        eas refreshed recently or nor.

        Arguments:
            exmb_client         (ExchangeMailbox)-- object of ExchangeMailbox type for the Exchange Client
    """
    client_id = exmb_client.tc_object.client.client_id
    _last_discovery_stats = exmb_client.csdb_helper.get_discovery_prop()
    _curr_time = int(time.time())

    _last_discovery_time = _last_discovery_stats['App_Office365DiscoverState']['@lastCacheUpdateTime']
    if _curr_time - int(_last_discovery_time) > 108000:
        return False
        # last successful discovery ran more than 30 hours ago: so return False
    return True


def create_test_mailboxes(tc_object, count: int):
    """
        Create Mailboxes for Test purpose and populate data in them

        Arguments:
            tc_object       (CVTestCase)--      TestCase object for whihc mailboxes are to be created
            count           (int)--             Number of mailboxes to be created
    """
    tc_object.mailboxes_list = tc_object.testdata.create_online_mailbox(count=count, use_json=False)

    for mailbox in tc_object.mailboxes_list:
        smtp = mailbox + "@" + tc_object.tcinputs['DomainName']
        tc_object.smtp_list.append(smtp)

    tc_object.exmbclient_object.exchange_lib.send_email(mailbox_list=tc_object.smtp_list)
    tc_object.exmbclient_object.users = tc_object.smtp_list
