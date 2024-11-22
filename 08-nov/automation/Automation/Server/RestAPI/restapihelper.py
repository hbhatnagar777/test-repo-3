# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing REST API operations

RESTAPIHelper is the only class defined in this file

RESTAPIHelper: Helper class to perform REST API operations

RESTAPIHelper:

 __init__()                      --  initializes REST API helper object

run_newman()                     --  executes the collection file using newman

clean_up()                       -- deletes temporary files generated during newman execution

"""
import os
import json
import re
import subprocess
from base64 import b64encode
from shutil import copyfile
from Server.RestAPI import restapiconstants as RC
from AutomationUtils import logger
import datetime


class RESTAPIHelper(object):
    """Helper class to perform REST API operations"""

    def __init__(self):
        """Initializes RESTAPIhelper object """
        self.log = logger.get_log()

    def __repr__(self):
        """Representation string for the instance of the RESTAPIHelper class."""
        return "RESTAPIHelper class instance"

    def run_newman(self, collection_json, tc_input, delay=2, **kwargs):
        """Executes the given collection file using newman

        Args:
            collection_json  (dict)   --  dictionary value with test case id as key
                                        and collection file name created using postman as value

                                        Example:
                                        {'tc_id': self.id, 'c_name': collection_json}

            tc_input         (dict)  --      test case input dictionary

                                        Example:
                                        self.tcinputs

            delay            (int)   -- delay in execution between two APIs. Value is in ms.

                                        Example:
                                        5000

            **kwargs          (dict)       -- Provides additional run options for newman run

                    {
                        "return_newman_output" : True,
                    }

            Returns:
                tuple       --      (return code, newman_output, error_msg) if input 'return_newman_output' is passed.

            Raises:
                Exception:
                    if newman execution fails
        """
        run_options =  dict(kwargs.items())

        if 'custom_endpoint' in run_options:
            webserver_url = run_options.get('custom_endpoint')
            tc_input['ServerURL'] = webserver_url
        else:
            webserver_url = 'https://' + tc_input["webserver"] + '/commandcenter/api'
            tc_input['ServerURL'] = webserver_url

        tc_input.pop('webserver', None)

        base64pwd = b64encode(tc_input["password"].encode()).decode()

        tc_input['Password'] = base64pwd
        tc_input.pop('password', None)

        tc_input['UserName'] = tc_input["username"]
        tc_input.pop('username', None)

        env_file = RC.ENVIRONMENT_FILE

        collection_file = os.path.join(RC.COLLECTION_FILE, collection_json['c_name'])

        temp_env_file = RC.TEMP_ENVIRONMENT_FILE

        if not os.path.exists(RC.NEWMAN_LOG_LOCATION):
            os.makedirs(RC.NEWMAN_LOG_LOCATION)

        if RC.CREATE_REPORTS:
            # Set CREATE_REPORTS as True in restapiconstants only after installing newman reporter htmlextra
            # Command to install reporter : “npm install -g newman-reporter-htmlextra” 
            request_path = str(os.getcwd()).split('\\')
            request_id = request_path[-1]
            if not os.path.exists(RC.RESTAPI_REPORT_PATH):
                os.makedirs(RC.RESTAPI_REPORT_PATH)
            if request_id.isdigit():
                restapi_report_path = os.path.join(RC.RESTAPI_REPORT_PATH, request_id)
                if not os.path.exists(restapi_report_path):
                    os.makedirs(restapi_report_path)
                restapi_report_name = os.path.join(restapi_report_path, collection_json['tc_id'] + '.html')
            else:
                time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
                restapi_report_name = os.path.join(RC.RESTAPI_REPORT_PATH, collection_json['tc_id'] + '_' + time_stamp + '.html')

        newman_log_file_name = os.path.join(RC.NEWMAN_LOG_LOCATION,
                                            'newman_'+collection_json['tc_id']+'.log')

        self.log.info("Creating copy of environment file to location {0}".format(RC.COLLECTION_FILE))

        copyfile(env_file, temp_env_file)
        missing_keys= []

        with open(temp_env_file, 'r+') as f:
            json_data = json.load(f)

            self.log.info("Replacing values in copied environment file with test case answers")

            for tc_key in tc_input:
                key_present = True
                for value in json_data['values']:
                    if tc_key in value['key']:
                        value['value'] = tc_input[tc_key]
                    else:
                        if tc_key not in missing_keys:
                            missing_keys.append(tc_key)

                        else:
                            self.log.info("Duplicate key , ignoring it as it is already part of missing keys ")

            if missing_keys:
                for each_key in missing_keys:
                    temp_data = {'enabled': True, 'key': each_key, 'type': "text", 'value': tc_input[each_key]}
                    json_data['values'].append(temp_data)

            json_data['values'] = [i for n, i in enumerate(json_data['values']) if i not in json_data['values'][n + 1:]]
            f.seek(0)
            f.write(json.dumps(json_data))
            f.truncate()
            self.log.info("File copied and values replaced....starting newman execution...")
        
        if RC.CREATE_REPORTS:
            cmd = ('newman run "' + collection_file + '" --environment "' + \
                  temp_env_file + '" --verbose -r cli,htmlextra --reporter-htmlextra-export "' +
                   restapi_report_name + '" --insecure --delay-request "' + str(delay) + '"')
        else:
            cmd = 'newman run "' + collection_file + '" --environment "' + \
              temp_env_file + '" --verbose --insecure"'
        
        if('run_flags' in run_options):
            for flag in run_options.get('run_flags'):
                cmd += " --{0}".format(flag)

        if run_options.get('return_newman_output'):

            cmd = cmd.replace(" >> " + '"' + newman_log_file_name + '"', "")
            self.log.info("Command being executed is: %s ", cmd)
            output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_error = output.stderr.decode('utf-8')
            print(output_error)
            if "'newman' is not recognized" in output_error:
                raise Exception("Failure in execution. Newman package not found")
            output_text = output.stdout.decode("utf-8")
            cleaned_output = re.sub(r"\x1B\[[0-9;]*[JKmsu]", "", output_text)
            with open(newman_log_file_name, "w", encoding="utf-8") as log_file:
                log_file.write(cleaned_output)
            return output.returncode, output.stdout.decode(), output.stderr
        else:
            self.log.info("Command being executed is: %s ", cmd)
            output = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_error = output.stderr.decode('utf-8')
            print(output_error)
            if "'newman' is not recognized" in output_error:
                raise Exception("Failure in execution. Newman package not found")
            output_text = output.stdout.decode("utf-8")
            cleaned_output = re.sub(r"\x1B\[[0-9;]*[JKmsu]", "", output_text)
            for line in cleaned_output.splitlines():
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(newman_log_file_name, "a", encoding="utf-8") as log_file:
                    log_file.write(f"[{timestamp}] {line}\n")

            self.log.info("Generating Newman logs at the location: %s", RC.NEWMAN_LOG_LOCATION)
            
            if "AssertionError" in cleaned_output or "JSONError" in cleaned_output or "TypeError" in cleaned_output:
                if RC.CREATE_REPORTS:
                    raise Exception("Failure in execution.Please check REST API Report located at {0} and Newman logs located at: {1}"
                                    .format(restapi_report_name,newman_log_file_name))
                else:
                    raise Exception("Failure in execution.Please check Newman logs located at: {0}".format(newman_log_file_name))
            # if res == 0:
            #     self.log.info("Newman tests executed successfully")

            # else:
            #     raise Exception("Failure in execution.Please check Newman logs located at: {0}".
            #                     format(newman_log_file_name))
        if RC.CREATE_REPORTS:
            self.log.info("Generating RESTAPI reports in : %s", str(restapi_report_name))
    def clean_up(self):
        """clean-up function to delete temporary files"""

        self.log.info("Starting clean-up phase")
        self.log.info("Deleting temporary environment file")
        os.remove(RC.TEMP_ENVIRONMENT_FILE)
        self.log.info("Temporary environment file deleted")
