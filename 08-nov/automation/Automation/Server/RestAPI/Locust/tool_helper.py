from collections import OrderedDict
from inspect import getmembers, isfunction
import sys
import json
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import AutomationUtils.constants as ac
from datetime import datetime
from API import locust_instance

# Creates a list of APIs available for execution


def make_list(obj):
    tup_list = [api for api in getmembers(obj) if isfunction(api[1])]
    api_list = []
    api_val = []
    for ele in tup_list:
        api_list.append(ele[0])
    return api_list

# Takes user input to determine what APIs need to run and their order


def get_api(val):
    flag = 0
    print("The list of APIs available for testing are:")
    for i in range(0,len(val)) :
        print(str(i+1)+" "+str(val[i]))

    dict_func = OrderedDict()

    for i in range(0, len(val)):
        key = input("Enter the API number to be run. Enter \"stop\" if you have selected enough APIs: ")
        if key == "stop":
            break
        try:
            jsonfile = open("temp_var.json", "r")
            variables = json.load(jsonfile)
            jsonfile.close()
            dict_func[int(key)] = val[int(key)-1]
            if val[int(key)-1] in variables["nec_inputs"].keys():
                for i in variables["nec_inputs"].get(val[int(key)-1]):
                    a = input("Enter the "+str(i)+" please :")
                    variables.update({i: a})
            tempjson = open("temp_var.json", "w+")
            tempjson.write(json.dumps(variables))
            tempjson.close()

        except:
            flag = 1
            print("Please enter only numbers provided above")
            sys.exit(1)
    return dict_func.values()

# Converts the API functions into executable objects


def eval_func(dict_func):
    only_vals = ["locust_instance."+str(i) for i in dict_func]
    only_call = []
    for i in only_vals:
        only_call.append(eval(i))
    return only_call


def get_api_cleanup(val):
    jsonfile = open("temp_var.json", "r")
    variables = json.load(jsonfile)
    jsonfile.close()
    cleanup_list = []
    if len(variables["user_list"]) != 0:
        cleanup_list.append("delete_user")
    if len(variables["org_list"]) != 0:
        cleanup_list.append("delete_organization")
    if len(variables["pool_list"]) != 0:
        cleanup_list.append("delete_pool")
    if len(variables["plan_list"]) != 0:
        cleanup_list.append("delete_plan")
    if len(variables["user_group_list"]) != 0:
        cleanup_list.append("delete_usergroup_papi")
    if len(variables['role_list']) != 0:
        cleanup_list.append('delete_role')
    if len(variables['clientgroup_list']) != 0:
        cleanup_list.append('delete_servergroup_api')
    return cleanup_list


def load_unload(json_type,var_json=None):
    if json_type == 'r':
        jsonfile = open("temp_var.json", "r")
        variables = json.load(jsonfile)
        jsonfile.close()
        return variables
    if json_type == 'w':
        jsonfile = open("temp_var.json", "w+")
        jsonfile.write(json.dumps(var_json))
        jsonfile.close()


def api_response(apiDetails,response):
    print(str(datetime.now()))
    print("======================================== "+apiDetails+" ====================================")
    if response and len(response.json())>0:
        if len(str(response.json()).encode('utf-8'))//1024 < 4:
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        else:
            print(json.dumps(response.json(), indent=4, sort_keys=True)[:1000]+".....")
        print()
        print("Response status code", response.status_code)
        variables =load_unload('r')
        if response.status_code != 200:
            variables["api_flag"] = "1"
            load_unload('w',variables)
        print("=============================================================================================")


def headers(extra_header={}):
    header = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if len(extra_header)>0:
        header.update(extra_header)
    return header


def check_key(dictionary, key, list_key, entity_id):
    if key in dictionary.keys():
        dictionary[key].append(entity_id)
        dictionary[list_key].append(entity_id)
        load_unload('w', dictionary)
    else:
        dictionary[key] = []
        dictionary[key].append(entity_id)
        dictionary[list_key].append(entity_id)
        load_unload('w', dictionary)

def get_tempjson():
    filePath= os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust',
                             'Locust_testcase',
                             'temp.json')
    if os.path.isfile(filePath):
        temp = open(os.path.join(ac.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', 'Locust',
                                 'Locust_testcase',
                                 'temp.json'), 'r')
        return json.load(temp)
    else:
        return False