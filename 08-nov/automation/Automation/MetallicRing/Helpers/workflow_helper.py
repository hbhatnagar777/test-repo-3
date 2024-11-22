# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for performing workflow related operations in Metallic Ring

    WorkflowRingHelper:

        __init__()                      --  Initializes Alert Ring Helper

        disable_workflow                --  Disable a workflow with a given name

        execute_trials_v2_workflow      --  Executes Activate Trials V2 workflow

"""

from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from cvpysdk.commcell import Commcell


class WorkflowRingHelper(BaseRingHelper):
    """ contains helper class for workflow ring helper related operations"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.wfs = self.commcell.workflows

    def start_task(self):
        """
        Starts the workflow related tasks for metallic ring
        """
        try:
            self.log.info("Starting workflow helper task")
            for workflow in cs.WFS_TO_DISABLE:
                self.disable_workflow(workflow, with_retry=True)
            self.log.info("Workflow helper task complete. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute workflow helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def disable_workflow(self, workflow_name, with_retry=False):
        """ disables a given workflow in the metallic ring
                Args:
                    workflow_name(str)  --  Name of the workflow to be disabled
                    with_retry(bool)    --  Should retry with another user to disable the workflow
                Returns:
                    None:

                Raises:
                    Exception when workflow with given name doesn't exist

        """
        if not self.wfs.has_workflow(workflow_name):
            raise Exception(f"Workflow [{workflow_name}] with given name doesn't exist")
        try:
            self.log.info(f"Disabling the following workflow - [{workflow_name}] with user - [{self.commcell.commcell_username}]")
            wf_obj = self.wfs.get(workflow_name)
            wf_obj.disable()
            self.log.info(f"Workflow - [{workflow_name}] disabled")
        except Exception as exp:
            if not with_retry:
                raise
            self.log.info("We need two admin users to disable the workflow in SP36 and above")
            cc = Commcell(self.ring.web_consoles[0].hostname,
                          f"{self.ring.hub_user.domain}\\{self.ring.hub_user.username}", self.ring.hub_user.password)
            wf_helper = WorkflowRingHelper(cc)
            wf_helper.disable_workflow(workflow_name, with_retry=False)

    def execute_trials_v2_workflow(self, workflow_name, workflow_inputs=None):
        """
        Executes Activate Trials V2 workflow
        """
        wfs = self.wfs
        request_xml = cs.WF_START_TAG % workflow_name
        client_id = self.commcell.commserv_client.client_id
        client_name = self.commcell.commserv_client.client_name
        hostname = self.commcell.commserv_client.client_hostname
        self.log.info(f"Sending request - [{request_xml}]")
        flag, response = wfs._cvpysdk_object.make_request(
            'POST', self.commcell._services['EXECUTE_INTERACTIVE_WORKFLOW'], request_xml)
        self.log.info(f"Received response - [{response}]")
        if flag:
            if response.json():
                xml_string = response.json().get("message", {})
                import xml.etree.ElementTree as ET
                tree = ET.ElementTree(ET.fromstring(xml_string))
                root = tree.getroot()
                session = root.attrib['sessionId']
                job_id = root.attrib['jobId']
                process_step_id = root.attrib['processStepId']
                wf_popup_inputs = (session, job_id, process_step_id, workflow_inputs["firstname"], workflow_inputs["lastname"],
                       workflow_inputs["company_name"], workflow_inputs["email"], workflow_inputs["commcell"],
                       workflow_inputs["phone"], client_id, client_name, hostname, client_id, client_name)
                popup_request_xml = cs.WF_TRIALS_V2_POPUP_INPUT_XML % wf_popup_inputs
                self.log.info(f"Sending request - [{popup_request_xml}]")
                flag, response = wfs._cvpysdk_object.make_request(
                    'POST', self.commcell._services['EXECUTE_INTERACTIVE_WORKFLOW'], popup_request_xml)
                self.log.info(f"Response received - [{response}]")
                if flag:
                    if response.json():
                        xml_string = response.json().get("message", {})
                        success_response = " Request Queued , look out for email with reset password link or " \
                                           "reset pwd from Commandcenter as MSP"
                        if success_response in xml_string:
                            self.log.info(
                                "\n\n\nWorkflow execution complete. Sending request to complete the workflow \n\n\n")
                            xml_string = response.json().get("message", {})
                            tree = ET.ElementTree(ET.fromstring(xml_string))
                            root = tree.getroot()
                            process_step_id = root.attrib['processStepId']
                            info_inputs = (session, job_id, process_step_id, client_id, client_name, hostname,
                                           client_id, client_name)
                            request_xml = cs.WF_TRIALS_V2_INFO_INPUT_XML % info_inputs
                            self.log.info(f"Request XML - {request_xml}")
                            flag, response = wfs._cvpysdk_object.make_request(
                                'POST', self.commcell._services['EXECUTE_INTERACTIVE_WORKFLOW'], request_xml)
                            self.log.info(f"Response - [{response}] \n We can ignore this error as the "
                                          f"workflow already completed create tenant task")
                            return
            else:
                raise Exception("Failed to execute workflow")
        response_string = self.commcell._update_response_(response.text)
        raise Exception(f"Failed to execute workflow. Exception {response_string}")
