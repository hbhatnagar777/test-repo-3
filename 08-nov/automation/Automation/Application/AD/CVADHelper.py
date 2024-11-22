# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for AD cvpysdk operations"""




import time
from AutomationUtils import machine
from Application.AD import constants
from Application.AD.exceptions import ADException
from cvpysdk.subclients.adsubclient import ADSubclient



class CVADHelper(object):
    """class to perform AD operations """

    def __init__(self,log,commcell_object, server_name,
                 ad_username, ad_password):
        """Initializes the class to perform AD operations

            Args:


                server_name             -- Server name is the machine with commvault's package

                ad_username (str)       -- AD administrator username

                ad_password (str)       -- AD administrator password



                log                     --instance of the logger class

                commcell_object          --instance of the commcell

        """
        self.log=log
        self.server_name = server_name
        self.ad_username = ad_username
        self.ad_password = ad_password
        self.host_machine = machine.Machine(server_name, commcell_object)

    def access_ad_client(self,client_name,commcell_obj):
        """
        Function to return client object
        param client_name(str):  name of the client
        param commcell_obj : commcell instance
        """
        client_obj=commcell_obj.clients.get(client_name)
        self.log.info(f"Returning Client Object of client {client_name}")
        return client_obj

    def do_backup(self,subclient_obj,backup_level="Incremental"):
        """
        Function to trigger incremental backup and return backup end time
        param subclient_obj: instance of subclient
        param bacup_level: the level of backup to perform
        """
        backup_obj=subclient_obj.backup(backup_level=backup_level)
        backup_obj.wait_for_completion()
        job_end_time = int(backup_obj._summary['jobEndTime'])
        self.log.info(" Backup Done Returning end Time")
        return job_end_time

    def user_ps_operation(self, username, principalname, op_type, computer_name, attribute_value, attribute):
        """
        Function to execute power shell operations depending on operation type
        param username(str): name of user
        param principalname(str): Principal Name of the user
        param OPType(str) : Type of operation to perform like
        creation , modification or deletion of user
        param CompName(str): Name of the machine with AD installed
        param Description(str): Description of the user
        """
        try:
            prop_dict = {
                "LoginPassword": self.ad_password,
                "LoginUser": self.ad_username,
                "UserName": username,
                "UserPrincipalName": principalname,
                "OpType": op_type,
                "ServerName": self.server_name,
                "AttributeValue": attribute_value,
                "CompName": computer_name,
                "attribute": attribute
            }
            self.log.info("Executing power shell script")
            power_output = self.host_machine.execute_script(
                constants.USER_OPS, prop_dict)

            if op_type == "RETURN_PROPERTY":
                attr_value = power_output.__dict__
                result_array = attr_value['_formatted_output'][0]
                return result_array

        except ADException as excp:
            raise ADException('ad', '77', "Exception occured while using Powershell") from excp

    def generate_compare_result(self, subclient_obj, left_set_time,right_set_time,
                                display_name, client_name,comparison_name,domain,op_type=2):
        """
        Function that triggers AD Compare job generates AD compare report and returns it
        param subclient_obj: subclient object
        param left_set_time(int): End Time of the first backup for comparison
        param right_set_time(int):End Time of the second backup for comparison
        param display_name(str): displayName of the client
        param client_name(str): name of the client
        param comparison_name(str): name of AD Compare job
        param domain(str): name of the domain
        """
        self.log.info("Launching Compare and Generating Results")
        #Generating source item
        domain_split = domain.split('.')
        source_item = ",DC=" + domain_split[-1]

        comparison_name_timestamp = comparison_name + str(int(time.time()))


        #To generate compareID
        comp_id= subclient_obj.compare_id( left_set_time,right_set_time,
                                 source_item,comparison_name_timestamp)
        self.log.info(f"Comparison ID generated {comp_id}")
        #To trigger compare job
        self.log.info("Triggering Compare job")
        subclient_obj.trigger_compare_job(left_set_time,right_set_time,
                                 display_name,client_name,
                                 comp_id,source_item,comparison_name_timestamp)
        self.log.info("Compare Job Started")
        #To check if compare report generated
        self.log.info("Checking if compare results generated")
        comparison_cache_path=subclient_obj.checkcompare_result_generated(comp_id)
        #To generate compare report
        result=subclient_obj.generate_compare_report(comp_id,comparison_cache_path,op_type)
        #returning compare report
        return result
