# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing ring commserv related tasks

    CommservRingHelper:

        __init__()                              --  Initializes Admin Ring Helper

        start_task                              --  Starts the commserve helper task for ring configuration

        update_email_server                     --  Updates the email settings for the ring commcell

        update_job_streams                      --  Sets the max streams for backup jobs

        add_additional_settings_in_bulk         --  Adds all the needed additional setting for the commcell

        add_additional_settings                 --  adds additional setting on the ring commcell

"""

from AutomationUtils.config import get_config
from MetallicRing.Core.db_helper import DBQueryHelper
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_AD_SETTING_CONFIG = get_config(json_path=cs.ADDITIONAL_SETTING_CONFIG_FILE_PATH)


class CommservRingHelper(BaseRingHelper):
    """ helper class for performing ring commserve related tasks"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.job_management = self.commcell.job_management
        self.cs_client = self.commcell.commserv_client
        self.db_query_helper = DBQueryHelper(ring_commcell)

    def start_task(self):
        """Starts the commserve helper task for ring configuration"""
        try:
            self.log.info("Starting commserve task")
            smtp = _CONFIG.commserv.smtp_server
            self.update_email_server(smtp.server, smtp.sender_name, smtp.sender_email)
            self.update_job_streams()
            self.add_additional_settings_in_bulk()
            self.log.info("All commserve tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute Commserv helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def update_email_server(self, smtp_server, sender_name, sender_email, **kwargs):
        """
        Set Email Server (SMTP) setup for commcell
            Args:
                smtp_server(str)    --  hostname of the SMTP server
                sender_name(str)    --  Name of the sender
                sender_email(str)   --  Email address of the sender to be used
                ** kwargs(dict)     --  Key value pairs for supported arguments
                Supported argument values:
                    enable_ssl(boolean) --  option to represent whether ssl is supported for the EMail Server
                                            Default value: False
                    smtp_port(int)      --  Port number to be used by Email Server
                                            Default value: 25
                    username(str)       --  Username to be used
                    password(str)       --  Password to be used

            Returns:
                None
        """
        self.log.info(f"Request received to update email with following SMTP Server - [{smtp_server}], "
                      f"Sender Name - [{sender_name}], sender Email - [{sender_email}] on the commserver")
        self.commcell.set_email_settings(smtp_server, sender_name, sender_email, **kwargs)
        self.log.info("Email settings updated on the commserver")

    def update_job_streams(self, job_streams=cs.JOB_STREAMS):
        """
        Updates the job streams high level watermark
        """
        self.log.info(f"Setting the default job streams on the commserver to [{job_streams}]")
        self.job_management.job_stream_high_water_mark_level = job_streams
        self.log.info(f"Job Streams High WaterMark set to [{job_streams}] on the commcell")

    def add_additional_settings_in_bulk(self):
        """
        Adds the needed additional setting for the commcell
        """
        cs_add_settings = _AD_SETTING_CONFIG.Commserve
        for add_setting in cs_add_settings:
            self.add_additional_settings(category=add_setting.category,
                                         key_name=add_setting.key_name,
                                         data_type=add_setting.data_type,
                                         value=add_setting.value)

    def add_additional_settings(self, category, key_name, data_type, value):
        """ Adds new additional setting with provided name on the commcell
                Args:
                    category        -   Category of the additional settings
                    key_name        -   Name of the additional setting
                    data_type       -   Type of key
                    value           -   Value for additional settings
                        Example     --  "category":"EventManager",
                                        "key_name":"GuiTimeout",
                                        "data_type":"INT",
                                        "value":"10000"
        """
        self.log.info(f"Request received to create additional setting [{key_name}] on the commcell]")
        if key_name == cs.ADD_SETTING_WEBCONSOLE_URL:
            value = cs.ADD_SETTING_WEBCONSOLE_URL_VALUE % _CONFIG.custom_webconsole_url
        if key_name in (cs.ADD_SETTING_PACKAGE_MAC, cs.ADD_SETTING_PACKAGE_WIN32, cs.ADD_SETTING_PACKAGE_WIN64):
            value = value % self.ring.name
        self.cs_client.add_additional_setting(category=category,
                                              key_name=key_name,
                                              data_type=data_type,
                                              value=value)
        self.log.info("Additional settings on the commcell added successfully")
