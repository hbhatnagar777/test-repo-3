import tool_helper
import json
from locust import HttpUser, constant, SequentialTaskSet, task, TaskSet
import base64
from API import *
import copy


# Takes in commcell credentials to start execution
variables = tool_helper.load_unload('r')
username = variables["username"]
password = variables["password"]
user_list = copy.deepcopy(variables["locust_user_list"])
flag = int(variables["flag"])
# Returns the list of available APIs so that the user can pick order of execution 
if flag == 0:
    val = tool_helper.make_list(API)
    dict_func = tool_helper.get_api(val)
    only_call = tool_helper.eval_func(dict_func)
elif flag == 1:
    val = tool_helper.make_list(API)
    dict_func = tool_helper.get_api_cleanup(val)
    if len(dict_func) == 0:
        print("There are no residual entities. Exiting run...")
        quit()
    only_call = tool_helper.eval_func(dict_func)


# Converts password to base64 format
sample_string_bytes = password.encode("ascii") 
base64_bytes = base64.b64encode(sample_string_bytes) 
base64_password = base64_bytes.decode("ascii") 


class Locust(SequentialTaskSet):
    # Logs in the user
    def on_start(self):
        # first request
        user = user_list.pop(0)
        print("LOGIN USER")
        headers = {'content-type': 'application/json', 'Accept-Encoding': 'gzip', 'Accept': 'application/json'}
        response = self.client.post("/webconsole/api/Login", data=json.dumps({
            "mode": 4,
            "username": user,
            "password": base64_password
        }),
                                    headers=headers,
                                    name="Login")
        print("Response status code", response.status_code)
        # print("Response content:", response.text)
        if response.status_code == 200:
            print("Status code is correct!")
            variables[user] = response.json().get('token')
            print("Token value:", variables[user])
            tool_helper.load_unload('w',variables)
        else:
            print("User Not logged in!")

    # List of APIs to execute
    tasks = only_call

    # Terminates execution by logging out
    def on_stop(self):
        variables = tool_helper.load_unload('r')
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
