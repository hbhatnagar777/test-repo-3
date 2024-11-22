# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for performing post config related operations in Metallic Ring

    PostConfigRingHelper:

        __init__()                      --  Initializes Post Config Ring Helper
        start_task                      --  Start the post config helper task
        check_connectivity_to_ring      --  Checks connectivity to ring commcell
        create_company                  --  Creates a company in the ring using the Activate trials v2 workflow

"""
import random
from time import sleep
from urllib.parse import urlparse

from AutomationUtils.config import get_config
from dynamicindex.activate_tenant_helper import ActivateTenantHelper
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Helpers.workflow_helper import WorkflowRingHelper
from cvpysdk.commcell import Commcell

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class PostConfigRingHelper(BaseRingHelper):
    """ contains helper class for post config ring validation related operations"""

    def __init__(self, orbit_commcell):
        """
        Initializes Post Config Ring Helper
        Args:
            orbit_commcell(object)     --   Instance of orbit commcell class
        """
        super().__init__(orbit_commcell)
        self.orbit_commcell = orbit_commcell
        self.wf_helper = WorkflowRingHelper(self.commcell)
        self.user_info = _CONFIG.commserv

    def start_task(self):
        """
        Start the post config helper task
        """
        try:
            self.log.info("Request received to perform post config validaten.\n"
                          "1. Check connectivity to ring url. \n"
                          "2. Run Trials v2 workflow. \n"
                          "3. Check if tenant is created by trials v2 workflow.")
            retry_attempt = 0
            max_attempt = 45
            commcell = self.check_connectivity_to_ring(self.ring.custom_webconsole_url)
            company = f"{cs.CMP_NAME}{self.ring.name.upper()}"
            first_name = cs.CMP_USER_NAME
            commcell_name = self.ring.name.upper()
            self.create_company(company, first_name, commcell_name)
            self.log.info("Workflow execution complete. Checking if tenant is created")
            while not commcell.organizations.has_organization(company):
                commcell.organizations.refresh()
                self.log.info(f"Tenant is still not created [{company}]. Sleeping for couple of minutes")
                retry_attempt += 1
                sleep(120)
                if retry_attempt >= max_attempt:
                    raise Exception("Tenant creation from trials v2 workflow failed. Please check logs for more info")
            self.log.info(f"Tenant [{company}] created successfully. Changing company user password")
            ath = ActivateTenantHelper(commcell)
            user_name = f'{company}\\{first_name}'
            ath.change_company_user_password(user_name, self.user_info.new_password,
                                             self.user_info.new_password)
            self.log.info("Company user password changed. Adding a new role for workflow execute permission")
            commcell.users.refresh()
            commcell.roles.add(cs.WF_ROLE, [cs.WF_EXEC_PERM], [])
            self.log.info(f"New role added. Updating security association for group [{company}\\{cs.UG_TENANT_ADMIN}]")
            user_group_obj = commcell.user_groups.get(f"{company}\\{cs.UG_TENANT_ADMIN}")
            user_group_obj.update_security_associations(
                entity_dictionary={'assoc1':
                    {
                        cs.WORKFLOW_NAME: [cs.CSR_WORKFLOW],
                        cs.ROLE: [cs.WF_ROLE]
                    }}, request_type=cs.REQUEST_TYPE_UPDATE)
            self.log.info("Role updated for user group, Post config validation complete")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute workflow helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def check_connectivity_to_ring(self, ring_url):
        """
        Checks connectivity to ring commcell
        Args:
            ring_url(str)       --  Webconsole URL for the ring
        Returns:
            Commcell object if connectivity is successful
        """
        parsed_url = urlparse(ring_url)
        hostname = parsed_url.hostname
        self.log.info("Request received to initialize ring commcell. "
                      f"\n hostname - {hostname}")
        commcell = Commcell(hostname, self.ring.commserv.new_username, self.ring.commserv.new_password)
        self.log.info("Commcell Connectivity successful")
        return commcell

    def create_company(self, company, first_name, commcell):
        """
        Creates a company in the ring using the Activate trials v2 workflow
        Args:
            company(str)        --  Name of the company
            first_name(str)     --  first name of the admin user for the company
            commcell(str)       --  Name of the ring commcell where the company needs to be created
        """
        workflow_inputs = {"firstname": first_name, "lastname": "Admin01",
                           "company_name": company,
                           "phone": f"{random.randint(1000000000, 9999999999)}",
                           "commcell": f"{commcell}"}
        workflow_inputs["email"] = f"{workflow_inputs['firstname']}@{company}.com"
        workflow_name = "Metallic Trials On-boarding v2"
        self.log.info(f"Starting workflow [{workflow_name}] with inputs - [{workflow_inputs}]")
        self.wf_helper.execute_trials_v2_workflow(workflow_name, workflow_inputs)
        self.log.info("Workflow execution complete")
