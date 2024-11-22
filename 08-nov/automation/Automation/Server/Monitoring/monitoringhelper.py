# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Main file for performing log monitoring related operations.

MonitoringHelper: monitoring helper class to perform monitoring related operations

MonitoringHelper:
    __init__(class_object)                              --  initialise object of the
                                                            monitoringhelper class

    create_monitoring_policy(policy_name,template_name, -- creates and runs a monitoring policy for
                index_server, client_name, path, run)      given template, index server and client

    cleanup_policies()                                  -- deletes the created policies for the TC

"""

from AutomationUtils import logger


class MonitoringHelper(object):
    """monitoring helper class to perform monitoring related operations"""

    def __init__(self, commcell_object):
        """
        Initialises the monitoringhelper class with the commcell object

        Args:
            commcell_object (object) -- commcell object of the monitoring commcell
        """

        self._commcell_object = commcell_object
        self.log = logger.get_log()
        self.policy_list = []

    def create_monitoring_policy(self, policy_name, template_name, index_server,
                                 client_name, path, run=True, **kwargs):
        """
        Creates and runs the monitoring policy

        Args:

            policy_name    (str)   -- name of the monitoring policy to be created

            template_name  (str)   -- template for the policy to be created

            index_server   (str)   -- analytics server to be used for indexing

            client_name    (str)   -- client for which policy has to run

            path           (str)   -- path for the source file to be used as content

            run            (Bool)  -- if set to True, will trigger the monitoring job
        """
        try:

            self.log.info("Creating a (%s) monitoring policy" % template_name)
            mp_obj = self._commcell_object.monitoring_policies.add(
                policy_name, template_name, index_server, client_name, path, **kwargs)

            if not mp_obj:
                raise Exception("Failed to create MonitoringPolicy")
            self.policy_list.append(policy_name)

            if run is True:
                self.log.info("Running the monitoring policy")
                job_obj = mp_obj.run()
                job_status = job_obj.wait_for_completion()
                if job_status:
                    self.log.info("Monitoring Policy Job ran successfully with job id :" +
                                  str(job_obj.job_id))
                else:
                    raise Exception("LogMonitoring job failed with job id :" + str(job_obj.job_id))
            self.log.info("Policy Creation successful")

        except Exception as excp:
            raise Exception(str(excp))

    def cleanup_policies(self):
        """
        Deletes all the policies created during the test case
        """
        self.log.info("Deleting the monitoring policy/policies")
        for policy in self.policy_list:
            if self._commcell_object.monitoring_policies.has_monitoring_policy(policy):
                self._commcell_object.monitoring_policies.delete(policy)
