from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils import logger


class CvAppMgrAccessControlTest:
    """Class for CvAppMgrAccessControlTest.exe related operations"""

    def __init__(self, client_obj=None, commcell_object=None, csdb=None):

        self._client_obj = client_obj
        self._commcell_obj = commcell_object
        self._csdb = csdb
        self._client_obj_props(self._client_obj)
        self.log = logger.getLog()

    def _client_obj_props(self, client_obj):
        """Method to initialize a client machine object and client properties"""

        self._machine_obj = WindowsMachine(client_obj.client_name, self._commcell_obj)
        self._client_install_dir = self._client_obj.install_directory
        self._client_id = client_obj.client_id
        self._client_instance = client_obj.instance

    @property
    def client_machine_obj(self):
        """Returns client machine object"""
        return self._machine_obj

    @client_machine_obj.setter
    def client_machine_obj(self, client_obj):
        """Sets the client machine obj """
        self._client_obj_props(client_obj)

    def copy_exe_to_remote_machine(self, local_path):
        """Method to copy CvAppMgrAccessControlTest.exe to the client"""

        self._remote_path = self._client_install_dir + "\\Base"
        self._machine_obj.copy_from_local(local_path, self._remote_path)
        self._executable_path = f"{self._remote_path}\\CvAppMgrAccessControlTest.exe"

    def remove_exe_from_remote_machine(self):
        """Method to delete CvAppMgrAccessControlTest.exe from the client"""

        self._machine_obj.delete_file(self._executable_path)

    def execute_all_queries(self, query_dict):
        """Method to execute all the given queries"""
        self._query_res_dict = dict()

        for key, value in query_dict.items():
            self._csdb.execute(value)
            rows = self._csdb.fetch_all_rows()
            self._query_res_dict[key] = rows

    def run_command(self, entity_id, entity_type, attr_name, client_id=None):
        """Method to run cvappmgraccess command"""

        self._machine_obj.execute_command(f"cd {self._remote_path}")

        if client_id:
            appmgr_tool_cmd = f"CvAppMgrAccessControlTest.exe -inst {self._client_instance} -id " \
                              f"{entity_id} -type {entity_type} -clientId {client_id} " \
                              f"-attrName \"{attr_name}\""
            output = self._machine_obj.execute_command(appmgr_tool_cmd).formatted_output

        else:
            appmgr_tool_cmd = f"CvAppMgrAccessControlTest.exe -inst {self._client_instance} -id " \
                              f"{entity_id} -type {entity_type} -attrName \"{attr_name}\""
            output = self._machine_obj.execute_command(appmgr_tool_cmd).formatted_output
        self.log.info(appmgr_tool_cmd)
        return appmgr_tool_cmd, output

    def verify_access_for_all_rows(self, infrastructure_client=True):
        """Method to verify cvappmgraccess for all rows"""

        expected_success = []
        unexpected_success = []
        failure = []
        incorrect_command = []

        for key, value in self._query_res_dict.items():
            if value != [['']]:
                if key == "apptype_prop_query":
                    for row in value:
                        output = self.run_command(entity_id=row[1], entity_type=row[2],
                                                  attr_name=row[3], client_id=row[0])
                        if "returned: found property" in output[1]:
                            if row[0] == self._client_id:
                                expected_success.append(output[0])
                                self.log.info("####")
                            else:
                                unexpected_success.append(output[0])
                        elif "returned: property not found" in output[1]:
                            failure.append(output[0])
                        else:
                            incorrect_command.append(output[0])
                else:
                    for row in value:
                        output = self.run_command(entity_id=row[0], entity_type=row[1],
                                                  attr_name=row[2])
                        if "returned: found property" in output[1]:
                            if row[4] == self._client_id:
                                expected_success.append(output[0])
                                self.log.info("****")
                            else:
                                unexpected_success.append(output[0])
                        elif "returned: property not found" in output[1]:
                            failure.append(output[0])
                        else:
                            incorrect_command.append(output[0])

        if infrastructure_client:
            if failure or incorrect_command:
                raise Exception(f"These command should not fail. Failed:{failure}. "
                                f"Incorrect commands:{incorrect_command}")

        else:
            if unexpected_success or incorrect_command:
                raise Exception(f"These commands should not succeed. Successful commands: "
                                f"{unexpected_success} Incorrect commands: {incorrect_command}")

