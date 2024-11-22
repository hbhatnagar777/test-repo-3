import datetime
import sys
import os
import time
import json
import shutil
import glob
import AutomationUtils.constants as ac
from AutomationUtils import config
from Server.RestAPI.Locust.graph_analysis import *
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from inspect import getmembers, isfunction
from cvpysdk.commcell import Commcell
from cvpysdk.security.user import Users
from cvpysdk.exception import SDKException

sys.path.append(os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust'))
from Server.RestAPI.Locust.API import *
from Server.RestAPI.Locust.tool_helper import *


class Locust_Helper:

    def __init__(self, input_json):
        self.input_json = input_json
        self.version = None

    def locust_setup(self):
        # This method picks all the locust inputs and creates a json file containing these values for locust execution
        jsonfile = open(os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust', 'variable.json'), "r")
        variables = json.load(jsonfile)
        jsonfile.close()

        # Creates a temporary json file
        load_unload('w', variables)

        # List of inputs required for locust execution
        locust_exec_inputs = {"hostname": self.input_json['webserver'], "threads": self.input_json['threads'],
                              "rate": self.input_json['spawnRate'], "mts": self.input_json['minutes'],
                              "email": self.input_json['email'],
                              "filename": self.input_json['fileName'].split('\\')[-1].split('.')[0],
                              "locust_file": os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust',
                                                          'Locust_testcase', 'testcase_executable.py'),
                              "cleanup_file": os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust',
                                                           'tool_executable.py'),
                              "temp_file_path": os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust',
                                                             'Locust_testcase',
                                                             'temp.json')}

        # loading the temporary json file
        variables = load_unload('r')

        # Creating a commcell object from username and password inputs to create new users for locust execution
        commcell_object = Commcell(self.input_json['webserver'], self.input_json["username"],
                                   self.input_json["password"], verify_ssl=False)
        self.version = str(commcell_object.commserv_version)
        variables["version"] = self.version
        check = Users(commcell_object)
        for i in range(1, int(self.input_json['threads']) + 1):
            if Users.has_user(check, "locust_user" + str(i)):
                username = Users.get(check, "locust_user" + str(i))
            else:
                username = Users.add(check, "locust_user" + str(i), "locust" + str(i) + "@cv.com",
                                     password=self.input_json["password"],
                                     local_usergroups=["master"])
            user_object_split = str(username).split('"')
            variables["locust_user_id"][user_object_split[-2]] = username.user_id
        variables["locust_user_list"] = list(variables["locust_user_id"])
        load_unload('w', variables)

        # Uploading the API list to a temporary json file for locust execution
        with open(locust_exec_inputs["temp_file_path"], 'w') as json_file:
            json.dump(self.input_json, json_file)

        # Returns all the needed inputs for execution
        return locust_exec_inputs

    def generate_directory(self):

        # This method is used to create a directory to store reports generated from locust run

        cmd = str(time.asctime(time.localtime(time.time()))).replace(" ", "_").replace(":", "_")
        path = os.getcwd()
        if not os.path.exists('CSV_Reports'):
            os.makedirs('CSV_Reports')
        os.system('cd CSV_Reports & mkdir ' + str(cmd) + ' & cd ..')
        return cmd, path

    def generate_log_directory(self, filename):

        #  This method is used to create a directory to store logs generated from locust run

        dir_path = os.path.join(ac.LOG_DIR, "Locust")
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        log_file = os.path.join(ac.LOG_DIR, "Locust", filename + '_locust.log')
        return log_file

    def generate_graphs(self, cmd):
        generate_avg(str(cmd) + "_stats.csv", str(cmd) + "_avg.png")
        generate_med(str(cmd) + "_stats.csv", str(cmd) + "_med.png")
        generate_req(str(cmd) + "_stats.csv", str(cmd) + "_req.png")
        generate_fail(str(cmd) + "_stats.csv", str(cmd) + "_fail.png")
        time.sleep(2)
        for file in glob.glob('*.csv'): 
            shutil.move(file, os.path.join('CSV_Reports', str(cmd)))
        for file in glob.glob(str(cmd) + '*.png'):
            shutil.move(file, os.path.join('CSV_Reports', str(cmd)))
        time.sleep(10)

    def email_reports(self, cmd, email, path, filename):
        fromaddr = "locust@commvault.com"
        toaddr = email.split(', ')

        msg = MIMEMultipart()

        msg['From'] = fromaddr
        msg['To'] = ", ".join(toaddr)

        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader(filename, os.path.join(ac.AUTOMATION_DIRECTORY, "Testcases", filename + ".py"))
        module = loader.load_module()
        test_case_class = getattr(module, "TestCase")
        test_case_class = test_case_class()
        testcasename = test_case_class.name
        msg['Subject'] = "SP" + self.version + " " + filename + " " + testcasename
        body = f'''Hi,

                    Please find the report for the latest locust run for

                    {testcasename} . This testing involved {self.input_json['threads']} users with the 

                    spawn rate of {self.input_json['spawnRate']} for over {self.input_json['minutes']} minutes

                    Thank you!
                    '''

        msg.attach(MIMEText(body, 'plain'))

        filename = str(cmd) + "_stats.csv"
        avgname = str(cmd) + "_avg.png"
        medname = str(cmd) + "_med.png"
        reqname = str(cmd) + "_req.png"
        failname = str(cmd) + "_fail.png"
        file_list = [filename, avgname, medname, reqname, failname]

        for f in file_list:
            attachment = open(str(path) + '\\CSV_Reports\\' + str(cmd) + '\\' + str(f), "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % f)
            msg.attach(part)

        smtp_hostname = config.get_config().PostmanVariables.smtpHostname
        server = smtplib.SMTP(smtp_hostname)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

    def locust_cleanup(self, cleanup_command, cleanup_file, mts):
        process = subprocess.Popen('locust -f \"' + cleanup_file + '\"' + cleanup_command)
        seconds = int(mts) * 60
        time.sleep(int(seconds))
        process.kill()
    
    def delete_entities(self, entity, pattern="locust"):
        """Method used to delete entities which are cleaned up during testcases"""
        commcell_object = Commcell(self.input_json['webserver'], self.input_json["username"],
                                   self.input_json["password"], verify_ssl=False)
        self.commcell = commcell_object
        entity_map = {
            "users": {
                "obj": "self.commcell.users",
                "all_value": "all_users"
            },
            "usergroups":{
                "obj": "self.commcell.user_groups",
                "all_value": "all_user_groups"
            },
            "plans": {
                "obj": "self.commcell.plans",
                "all_value": "all_plans"
            },
            "roles": {
                "obj": "self.commcell.roles",
                "all_value": "all_roles"
            },
            "organizations": {
                "obj": "self.commcell.organizations",
                "all_value": "all_organizations"
            },
            "clientgroups": {
                "obj": "self.commcell.client_groups",
                "all_value": "all_clientgroups"
            },
            "storagepolicies": {
                "obj": "self.commcell.storage_policies",
                "all_value": "all_storage_policies"
            }

        }
        current_entity = eval(entity_map[entity].get("obj"))
        current_entity_values = eval("current_entity" + "." + entity_map[entity].get("all_value"))
        print("Clearing the locust created entiites for " + entity)
        for i in current_entity_values:
            try:
                if pattern in i:
                    print("Entity : "+str(i))
                    if entity == "users" or entity == "usergroups":
                        current_entity.delete(i, new_user="admin")
                    else:
                        current_entity.delete(i)
            except SDKException as exp:
                print("Exception while deleting the entity " + str(i))
                print(exp)

    def locust_execute(self):

        run_inputs = self.locust_setup()
        cmd, path = self.generate_directory()
        log_file = self.generate_log_directory(run_inputs["filename"])
        f = open(log_file, "a")
        f.write(str(datetime.now()))
        f.write("================================ STARTING LOCUST EXECUTION ==================================== \n")
        f.write(" ")
        f.close()
        f = open(log_file, "a")
        # Locust file execution command
        locust_command = str(
            cmd + ' --headless --host https://' + run_inputs["hostname"] + ' -u ' + run_inputs["threads"] + ' -r ' +
            run_inputs["rate"] +
            ' --run-time ' + run_inputs["mts"] + 'm ')
        cleanup_command = str(
            ' --headless --host https://' + run_inputs["hostname"] + ' -u ' + run_inputs["threads"] + ' -r ' +
            run_inputs["rate"] +
            ' --run-time ' + run_inputs["mts"] + 'm ')

        # Start locust execution
        process = subprocess.Popen('locust -f \"' + run_inputs["locust_file"] + '\" --csv=' + locust_command, stdout=f)
        seconds = int(run_inputs["mts"]) * 60
        time.sleep(int(seconds))
        process.kill()
        f.write("================================== ENDING LOCUST EXECUTION ===================================== \n")
        f.write(" ")

        # Close log file
        f.close()
        self.generate_graphs(cmd)
        self.email_reports(cmd, run_inputs["email"], path, run_inputs['filename'])
        variables = load_unload('r')
        api_flag = variables["api_flag"]

        if int(variables["flag"]) == 1:
            self.locust_cleanup(cleanup_command, run_inputs["cleanup_file"], run_inputs["mts"])

        variables = load_unload('r')
        commcell_object = Commcell(run_inputs["hostname"], variables["username"], variables["password"], verify_ssl=False)
        check = Users(commcell_object)
        # for i in range(len(variables["locust_user_list"])):
        #     username = Users.delete(check, variables["locust_user_list"][i], new_user="admin")

        # os.remove("temp_var.json")
        os.remove(run_inputs["temp_file_path"])

        if int(api_flag) == 0:
            return 0
        else:
            raise ValueError("API execution failed. Please check locust logs for more details")


class Exec_Function:

    def __init__(self, api_object, api_list):
        self.api_object = api_object
        self.api_list = api_list

    def list_conversion(self):
        variables = load_unload('r')
        tuple_list = [api for api in getmembers(self.api_object) if isfunction(api[1])]
        converted_list = []
        for ele in tuple_list:
            converted_list.append(ele[0])
        for api in self.api_list:
            if str(api) in converted_list:
                if str(api) in variables["nec_inputs"].keys():
                    print("entering necessary inputs")
                    inputJSON = os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust', 'Locust_testcase',
                                             'temp.json')
                    f = open(inputJSON)
                    data = json.load(f)
                    f.close()
                    for i in variables["nec_inputs"].get(str(api)):
                        variables[i] = data[i]
                        load_unload('w', variables)
            else:
                self.api_list.remove(api)
        final_val = ["locust_instance." + str(i) for i in self.api_list]
        final_call = []
        for i in final_val:
            final_call.append(eval(i))
        return final_call
