import sys
from locust import HttpUser, constant, SequentialTaskSet, task, TaskSet, events, exception
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
import AutomationUtils.constants as ac
import base64
import copy
from Server.RestAPI.Locust.Locust_testcase import locust_helper

sys.path.append(os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust'))
from Server.RestAPI.Locust.API import *
from Server.RestAPI.Locust.tool_helper import *

# Picks all the needed values for locust execution run from temp.json
inputJSON = os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust', 'Locust_testcase',
                         'temp.json')
f = open(inputJSON)
data = json.load(f)
f.close()

# Obtains API list to execute and converts into an executable format
api_list = data['apiList'].split(',')
executable_function = locust_helper.Exec_Function(API, api_list)
eval_list = executable_function.list_conversion()

# Storing user list and collective password for locust execution
variables = load_unload('r')
password = variables['password'] = data['password']
username = variables['username'] = data['username']
user_list = copy.deepcopy(variables["locust_user_list"])
load_unload('w', variables)
# Converts password to base64 format
sample_string_bytes = password.encode("ascii")
base64_bytes = base64.b64encode(sample_string_bytes)
base64_password = base64_bytes.decode("ascii")


@events.request.add_listener
def request_handler(request_type, name, response_time, response_length, response, **kw):
    if response.status_code != 200:
        tool_helper.load_unload('r')
        variables["api_flag"] = "1"
        tool_helper.load_unload('w', variables)
    if response:
        response_data = response.json()
        print(response_data)
        errList = response_data.get("errList")
        if errList and name == "Login":
            if len(errList) > 0:
                print("Login actually failed with wrong credentials")
                if errList[0].get('errorCode') == 1116:
                    raise exception.StopUser
            elif response.status_code != 200:
                raise exception.StopUser


class Locust(SequentialTaskSet):

    def on_start(self):
        # first request
        user = user_list.pop(0)
        self.client.verify = False
        print("LOGIN USER")
        headers = {'content-type': 'application/json', 'Accept-Encoding': 'gzip', 'Accept': 'application/json'}
        response = self.client.post("/webconsole/api/Login", data=json.dumps({
            "username": user,
            "password": base64_password
        }),
                                    headers=headers,
                                    name="Login",verify=False)
        print("Response status code", response.status_code)
        # print("Response content:", response.text)
        if response.status_code == 200:
            print("Status code is correct!")
            variables[user] = response.json().get('token')
            load_unload('w', variables)
        else:
            print("User Not logged in!")

    tasks = eval_list

    def on_stop(self):
        variables = load_unload('r')
        print("LOGOUT")
        headers = {'Accept-Encoding': 'gzip', 'Accept': 'application/json', 'Authtoken': variables["token"]}
        response = self.client.post("/webconsole/api/Logout", headers=headers, name="Logout")
        print("Response status code", response.status_code)
        print("Response content:", response.text)
        if response.status_code == 200:
            logout_message = response.json()
            print("response:", logout_message)


class User(HttpUser):
    tasks = [Locust]
    wait_time = constant(1)
