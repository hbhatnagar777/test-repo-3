# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This library is used to communicate with Micsoft Azure AD

Class:
    AzureAd        Azure Ad related operation
    CvAzureAd        Commvault Azure Ad operation class
"""
__all__ = []
import datetime
import random
import os
import json
from time import sleep
import requests

import adal
from adal.adal_error import AdalError
from .exceptions import ADException
from .adconstants import AadGraphTypeUrl, AadTypeAttribute, AadIndexMeta
from functools import wraps
from AutomationUtils.logger import get_log_dir

def renew_token(func):
    """
    decorator to renew token
    Args:
        func    (function)    function to be decorated
    Return:
        wrapper    (function)    decorated function
    exception:
        ADException    raise when token renew failed
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ADException as e:
            self.log.info(e)
            print(f"exception is {e}, renew token and try again")
            self.token = self.adal_token(self.client_id, self.client_pass, self.tenant)
            return func(self, *args, **kwargs)
    return wrapper

class AzureAd():
    """
    Azure AD class to handle regular AD operations
    """

    def __init__(self,  client_id, client_pass,  tenant, log, graphver='beta', vendor=None):
        """ initial class for Azure AD connection
        args:
            tenant      (string)    azure ad tenant id
            client_id    (string)    azure client to handle delete objects
            client_pass    (string)    azure clinet password
            log    (CV log instance)    log instance passed from test case
            graphver        (string)        graph version, can be picked form 'beta' and '1.0'
        """
        self.log = log
        self.client_id = client_id
        self.client_pass = client_pass
        self.tenant = tenant
        self.token = self.adal_token(self.client_id, self.client_pass, self.tenant)

        # domain query only support beta, not 1.0
        self.graph_beta_api_endpoint = self._graph_request_entrypoint('beta', vendor)

        self.graph_api_endpoint = self._graph_request_entrypoint(graphver, vendor)
        self.headers = {
            'Content-Type' : 'application/json',
            'Authorization': f"Bearer {self.token['accessToken']}",
            'Accept' : 'application/json, text/plain',
            'ConsistencyLevel': 'eventual'}
        self.domainname = self.get_domain_name()

    def _graph_request_entrypoint(self, graphver, vendor):
        """
        generate graph entry point based on the graphver and tenant
        Args:
            graphver        (string)        graph version, can be picked form 'beta' and '1.0'
            vendor          (string)        entry for different vendor, choice from gcc, gcchigh and others, still working
        """
        if vendor == "gcchigh":
            url =  "https://graph.microsoft.us"
        else:
            url = "https://graph.microsoft.com"


        if graphver == "beta":
            url = f"{url}/beta"
        else:
            self.log.debug("will use 1.0 version")
            url = f"{url}/v1.0"
        return url

    def adal_token(self, client_id, client_pass, tenant):
        """ connect to azure ad with client and cilent pass to generate token
        args:
            client_id    (string)    azure client to handle delete objects
            client_pass    (string)    azure clinet password
        return:
            token    (obj)    adal connection token for app
        """
        context = adal.AuthenticationContext(f'https://login.microsoftonline.com/{tenant}')
        token = context.acquire_token_with_client_credentials("https://graph.microsoft.com/",
                                                              client_id,
                                                              client_pass)
        self.log.debug("Azure connection token is setup")
        return token

    def type_operation(self, type_, operation, objs = None, harddelete=False, **kwargs):
        """ common type operation to avoid duplicate code
        args:
            type_    (string)    object type, select from the following type
                                    user, group, reg_app, ent_app
            operation(string)    supported operation from the following ops
                                    list, create, delete, find, update
                                    find need exact attribute and name, it can only support one attribute to search
                                        {"displayname": "20240129-guser1"}
                                        {"username": "20231025-muser"}
            kwargs    (dict)    additional parameter to operation on azure ad obj
            objs      (list)    azure ad objects to process
        return:
            result    (obj/list/int/None)       return result
                                                int will be returned when we do count operation
                                                list will be returned when mutliple objects are found
                                                obj will be returned when only one object found
        """

        result = None
        if operation in ["list", "count", "id", "find", "search", "one", "page", "all"]:
            self.log.debug(f"will use get to fetch result for {operation}")
            if operation == "id":
                url = self.graph_requests_builder(type_, "base")
                url = f"{url}/{objs}"
            elif operation in ['find', 'search']:
                search_switch = False
                if kwargs:
                    inputattribute = list(kwargs.keys())[0]
                    if inputattribute in AadTypeAttribute[type_]['all']:
                        if kwargs[inputattribute].startswith("*"):
                            search_switch = True
                    else:
                        raise ADException("azuread", "701",
                                          f"{inputattribute} is not in {type_} supported attributes {AadTypeAttribute[type_]['all']}")
                url = self.graph_requests_builder(type_, "base")
                if search_switch:
                    self.log.debug(f"will search attribute {inputattribute} with key {kwargs[inputattribute][1:]}")
                    url = f"{url}?$count=true&$search=\"{inputattribute}:{kwargs[inputattribute][1:]}\""
                else:
                    self.log.debug(f"will find exact attribute {inputattribute} with value {kwargs[inputattribute]}")
                    url = f"{url}?$filter=startsWith({inputattribute}, '{kwargs[inputattribute]}')"
            elif operation in  ["list", "one", "all", "page"]:
                url = self.graph_requests_builder(type_, "base")
            else:
                url = self.graph_requests_builder(type_, operation)
            

            if operation == "one":
                result, _ = self.graph_requests(url, type_, operation)
                result = random.choice(result)
            elif operation == "all":
                result, _ = self.graph_all(url, type_)
            else:
                result, _ = self.graph_requests(url, type_, operation)
        elif operation == "create":
            url = self.graph_requests_builder(type_, "base")
            result = self._operation_create(url, type_, **kwargs)
        elif operation == "delete":
            self.log.debug(f"start to delete {type_} objects")
            if objs:
                if isinstance(objs, list):
                    self.log.debug(f"will process {objs} direclty")
                else:
                    objs = [objs]
                    self.log.debug(f" will process {objs} in list format")
            else:
                if kwargs:
                    self.log.debug("will find the objects first")
                    objs = self.type_operation(type_, "find", **kwargs)
                    self.log.debug(f"will delete {len(objs)} {type_} objects")

            for obj_ in objs:
                url = self.graph_requests_builder(type_, "base")
                url = f"{url}/{obj_['id']}"
                result, _ = self.graph_requests(url, type_, "delete")
                self.log.debug(f"{type_} object {obj_['id']} with name {obj_['displayName']} is deleted")
                if harddelete:
                    sleep(2)
                    url = self.graph_requests_builder(type_, "harddelete")
                    url = f"{url}/{obj_['id']}"
                    result, _ = self.graph_requests(url, type_, "delete")
        elif operation == 'deletelist':
            self.log.debug(f'will get all deleted {type_} object from recycle bin')
            url = self.graph_requests_builder(type_, "deletelist")
            result, _ = self.graph_requests(url, type_, "list")
            if kwargs:
                inputattribute = list(kwargs.keys())[0]
                if not inputattribute in AadTypeAttribute[type_]['all']:
                    raise ADException("azuread", "701",
                                      f"{inputattribute} is not in {type_} supported attributes {AadTypeAttribute[type_]['all']}")
                if inputattribute == "id":
                    for _ in result:
                        if _['id'] == kwargs['id']:
                            result = [_]
                            break
                else:
                    if kwargs[inputattribute].startswith("*"):
                        result = [_ for _ in result if _[inputattribute].find(kwargs[inputattribute][1:]) >= 0]
                    else:
                        result = [_ for _ in result if _[inputattribute]==kwargs[inputattribute]]
        elif operation == "harddelete":
            result = self.type_operation(type_, "deletelist", **kwargs)
            if isinstance(result,dict):
                result = [result]
            for obj_ in result:
                url = self.graph_requests_builder(type_, "harddelete")
                url = f"{url}/{obj_['id']}"
                result, _ = self.graph_requests(url, type_, "delete")
        elif operation == "update":
            if not objs:
                objs = self.type_operation(type_, "find", **kwargs)
                if len(objs) != 1:
                    raise ADException("azuread", 702, f"found {len(objs)} objects, please provide id to update")
            url = self.graph_requests_builder(type_, "base")
            url = f"{url}/{objs['id']}"
            if "id" in kwargs:
                del kwargs['id']
            result, _ = self.graph_requests(url, type_, operation, new_define=kwargs)
            result = self.type_operation(type_, "id", objs=objs['id'])
        elif operation == "delta":
            self.log.debug("will proces delta link to get the change")
            url = self.graph_requests_builder(type_, "delta")
            url = f"{url}{kwargs['delta_token']}"
            result, _ = self.graph_requests(url, type_, "delta")
        if isinstance(result, list) and len(result) ==1:
            result = result[0]
        return result

    def _operation_create(self, url, type_, **kwargs) :
        """ create object
        args:
            obj_type (obj)    auzre object operation  obj create function
            ins_    (obj)    azure object opeeration obj
            type_    (str)    object type, select from the following type
                                    user, group, reg_app, ent_app
            kwargs    (dict)    additional parameter to create azure ad obj
        return:
            operation_result    (obj)    new object created or found obj
        """
        timestamp = int(datetime.datetime.now().timestamp())
        new_define = {}
        for entry in AadTypeAttribute[type_]["new"]:
            if entry in kwargs:
                new_define[entry] = kwargs[entry]
            else:
                new_define[entry] = f"Script_{type_}_{timestamp}"
        self.log.debug(f"new {type_} object define {new_define}")
        new_define = self._type_create_decoration(type_, new_define)
        self.log.debug(f"updated {type_} object define {new_define}")

        self.log.debug(f"check the object first before creation {new_define}")
        result = self.type_operation(type_, "find", ** {"displayName": new_define['displayName']})
        self.log.debug(f"found {len(result)} exist {type_} object name {new_define['displayName']}")
        if len(result) ==0:
            self.log.debug(f"start to create new object {new_define}")
            result, _ = self.graph_requests(url, type_, operation="create", new_define=new_define)
        return result

    def obj_ops(self, type_, operation, **kwargs):
        """
        process different operation
        """
        if operation == "update":
            result = self.type_operation(type_, 'id', kwargs['id'])
            del kwargs['id']
            objs = self.type_operation(type_, "update", objs=result, **kwargs)
        elif operation == "delete":
            if "id" in kwargs:
                objs = self.type_operation(type_, "id", objs=kwargs['id'])
            else:
                objs = self.type_operation(type_, 'search', **kwargs)
            self.log.debug(objs)
            self.log.debug(f"found {len(objs)} to process, will delete all of them")
            self.type_operation(type_, "delete", objs=objs)
        else:
            if "id" in kwargs and operation not in ['deletelist', 'harddelete']:
                objs = self.type_operation(type_, "id", objs=kwargs['id'])
            else:
                objs = self.type_operation(type_, operation, **kwargs)
        return objs

    def user(self, operation="find", **kwargs):
        """User related operations
        args:
            operation    (string)    supported operation from the following ops
                                     count, list, create, delete, update,
                                     default operation is find the
                                        count   will return total count
                                        list    will return a list of objects (will return count if more than 3K objects)
                                        find    will find or search matched objects based on kwargs
                                        one     will get random one object from type list
                                        page    will return one page of objects
                                        all     will return all objects, it may take times 
                                        create  will create a new user, you can provide the obj information in kwargs
                                        delete  will delete the object based on kwargs
                                        deletelist  will list deleted objects based on kwargs
                                        update  will update only one object each time, you must provide "id"
                                                and update attribute
            kwargs    (dict)    additional parameter to operation on azure ad obj
                                supported object attribute can be found in constants.jon in this same folder,
                                    check "AadTypeAttribute" with object type
                                in general, it only support one attribute.
                                    if you have "*" in the value, it will run search operation and return all matched result.
                                example:
                                    {"id":'6c81ecec-5a34-4e46-8e3a-9c4044c2c5da'}    will return matched object
                                    {"displayName" : 'Script_user_1706812174'}       will return matched object
                                    {"displayName" : "*Script"}                      will search keyword "Script" in
                                                                                       displayname and return list
                                    {"id":'6c81ecec-5a34-4e46-8e3a-9c4044c2c5da', "department": "Newsale"}
                                                                                     will only used in update case.
                                                                                     will find hte object and update the value
        return:
            users    (objs)    azure user objects
        """
        return self.obj_ops("user", operation, **kwargs)

    def group(self, operation="find", **kwargs):
        """group related operations
        args:
            please see user operation for all the details
        return:
            groups    (objs)    azure groups objects
        """
        return self.obj_ops("group", operation, **kwargs)

    def reg_app(self, operation="find", **kwargs):
        """registred application related operation
        args:
        args:
            please see user operation for all the details
        return:
            reg_apps    (objs)    azure reg_app objects
        """
        return self.obj_ops("reg_app", operation, **kwargs)

    def ent_app(self, operation="find", **kwargs):
        """ enterprise app related operations
        args:
            please see user operation for all the details
        return:
            ent_apps    (objs)    azure ent_apps objects
        """
        return self.obj_ops("ent_app", operation, **kwargs)
    
    def ca_policy(self, operation="find", **kwargs):
        """ policy related operations
        https://learn.microsoft.com/en-us/graph/api/conditionalaccessroot-post-policies?view=graph-rest-1.0&tabs=http

{
    "displayName": "Require MFA to EXO from non-compliant devices.",
    "state": "enabledForReportingButNotEnforced",
    "conditions": {
        "applications": {
            "includeApplications": [
                "00000002-0000-0ff1-ce00-000000000000"
            ]
        },
        "users": {
            "includeGroups": ["ba8e7ded-8b0f-4836-ba06-8ff1ecc5c8ba"]
        }
    },
    "grantControls": {
        "operator": "OR",
        "builtInControls": [
            "mfa"
        ]
    }
}

        args:
            please see user operation for all the details
        return:
            ca_policy    (objs)    azure policy objects
        """
        return self.obj_ops("ca_policy", operation, **kwargs)

    def ca_name_location(self, operation="find", **kwargs):
        """ enterprise app related operations
        args:
            please see user operation for all the details
        return:
            ca_name_location    (objs)    azure name location objects
        """
        return self.obj_ops("ca_name_location", operation, **kwargs)

    def ca_auth_context(self, operation="find", **kwargs):
        """ auth context related operations
        it seem create and update is not allowed  from graph api 
        patch is working with the following 
        {"id": "c6  ", "displayName": "script_created_auth_context", "description": "soemthing special"}

        create the object with this url 
        /identity/conditionalAccess/authenticationContextClassReferences/c30
        patch 
        {"id": "c30  ", "displayName": "script_created_auth_context11", "description": "soemthing special11"}
        args:
            please see user operation for all the details
        return:
            ca_auth_context    (objs)    azure authentication context objects
        """
        return self.obj_ops("ca_auth_context", operation, **kwargs)

    def ca_auth_strength(self, operation="find", **kwargs):
        """ enterprise app related operations
        args:
            please see user operation for all the details
        return:
            ca_auth_strength    (objs)    azure authentication strength objects
        """
        return self.obj_ops("ca_auth_strength", operation, **kwargs)

    def role(self, operation="find", **kwargs):
        """ role related operations
        args:
            please see user operation for all the details
        return:
            role    (objs)    azure role objects
        """
        return self.obj_ops("role", operation, **kwargs)

    def admin_unit(self, operation="find", **kwargs):
        """ admin unit related operations
        {"displayName": "admin  unit 22"}
        args:
            please see user operation for all the details
        return:
            admin unit    (objs)    azure admin unit objects
        """
        return self.obj_ops("admin_unit", operation, **kwargs)

    def _type_create_decoration(self, type_, new_define):
        """ process specail case for object creation maping
        args:
            type_    (string)    object type, select from the following type
                                    user, group, reg_app, ent_app
            new_define    (obj)    auzre ad creattion obj based on input
        return:
            new_define    (obj)    azure ad creation obj with correct value
        """
        self.log.debug(f"start to process {type_} object attribute {new_define} with additional value")
        if type_ == "user":
            new_define = { "accountEnabled": True,
                           "displayName":  new_define['displayName'],
                           "mailNickname": new_define['mailNickname'],
                           "userPrincipalName": f"{new_define['userPrincipalName']}@{self.domainname}",
                           "passwordProfile": {
                               "password": "Azure!123!",
                               "forceChangePasswordNextSignIn": False}}
        elif type_ == "group":
            new_define = { "displayName": new_define['displayName'],
                           "mailEnabled": True,
                           "mailNickname": new_define['mailNickname'],
                           "securityEnabled": True,
                           "groupTypes": ["Unified"]}
        elif type_ == "reg_app":
            new_define = {
                "displayName": new_define['displayName']}
        elif type_ == "ent_app":
            new_reg_app = self.reg_app(operation="create",
                                           **{"displayName": new_define['displayName']})
            self.log.debug(f"application {new_reg_app['appId']} is created, will waiting 30 seconds")
            sleep(30)
            new_define['appId'] = new_reg_app['appId']
            new_define['displayName'] = new_define["displayName"]
        elif type_ == "admin_unit":
            new_define = {"displayName": new_define['displayName']}
        elif type_ == "ca_auth_strength":
            new_define = {"displayName": new_define['displayName'],
                          "allowedCombinations" : ["windowsHelloForBusiness", "fido2"],
                          "policyType": "custom"}
        elif type_ == "ca_auth_context":
            self.log.debug("authentication contexnt only support update with patch operation")
            content_id = random.randint(30,99)
            new_define = {"displayName": new_define['displayName'],
                          "id": f"c{content_id}"}
        elif type_ == "ca_name_location":
            new_define = {"displayName": new_define['displayName'],
                          "@odata.type": "#microsoft.graph.countryNamedLocation",
                          "countriesAndRegions": ["US","GB"]}
        elif type_ == "role":
            new_define = {"displayName": new_define['displayName'],
                          "rolePermissions": [
                              {"allowedResourceActions": [
                                  "microsoft.directory/groups.security.assignedMembership/allProperties/update",
                                  "microsoft.directory/groups.security.assignedMembership/classification/update",
                                  "microsoft.directory/groups.security.assignedMembership/createAsOwner",
                                  "microsoft.directory/groups.security/allProperties/update"],
                                  "condition": None}],
                          "isEnabled": False}
        elif type_ == "ca_policy":
            one_entapp = self.ent_app(operation="one")
            onegroup = self.group(operation="one")
            onelocation = self.ca_name_location(operation="one")
            new_define = {
                "displayName": new_define['displayName'],
                "state": "enabledForReportingButNotEnforced",
                "conditions": {
                    "clientAppTypes": ["all"],
                    "applications": {
                        "includeApplications": [one_entapp['appId']]},
                    "users": {
                        "includeGroups": [onegroup['id']]},
                    "locations": {
                        "includeLocations": [onelocation['id']]},},
                "grantControls": {
                        "operator": "OR",
                        "builtInControls": ["mfa"]}
                }
        else:
            raise ADException("azuread", 703, f"unsupported type {type_} for create operation")
        return new_define

    def get_domain_name(self):
        """ get domain name from the tenant
        args:
        return:
            domainname    (string)    domain name in auzre ad
        """
        self.log.debug("start to get tenant domain name")
        url = self.graph_requests_builder("domain", "list", betaonly=True)
        result, _= self.graph_requests(url, "domain", operation="list")
        self.log.debug(f"found total  {len(result)} domains in this tenant")
        domainname = None
        for _ in result:
            if _['isDefault']:
                self.log.debug(f"found default domain name: {_['id']}")
                domainname = _['id']
                break

        if not domainname:
            raise ADException("azuread", 100, f" {url} reutrn {result.text}")
        return domainname

    def graph_requests_result_process(self, result, type_, operation, page=0, waittime=1, firstpage=False):
        """ process requests result
        args:
            result    (obj)    request response result
        return:
            return_result    (list)    a list of result in json format
        """
        result_ = result.json()
        if isinstance(result.json(), int):
            return_result = result.json()
        if isinstance(result.json(), dict):
            if "value" in result.json():
                return_result = result_['value']
                self.log.debug(f"current result return {len(return_result)} objects")
                if firstpage:
                    self.log.debug("only return the first page, no need  go ahead even there is more page")
                else:
                    if '@odata.nextLink' in result_:                    
                        self.log.debug(f"process page No. {page}")
                        self.log.debug(f"return result has multiple page need to process again, current page is {page}")
                        sleep(waittime)
                        page = page + 1
                        nextobjs_, _ = self.graph_requests(result_['@odata.nextLink'], type_, operation=operation, page=page)
                        if isinstance(nextobjs_, list):
                            return_result = return_result + nextobjs_
                        else:
                            self.log.debug(f"over the limit, return count result {nextobjs_}")
                        self.log.debug(f"result object include {len(return_result)} objects")
                    else:
                        self.log.debug("no additional page found any more")
            else:
                self.log.debug("no value is found in the result")
                return_result = [result.json()]

        if isinstance(result.json(), list):
            self.log.debug("new, check the following return list")
            return_result = result.json()
        return return_result, page

    def graph_requests_builder(self, type_, operation, betaonly=False):
        """
        build graph request based on the operation
        Args:
        Return
            url     (str)       url for the graph request
        """
        self.log.debug(f"start to build graph url for type {type_} {operation} action")
        self.log.debug(f"found correct url mapping {AadGraphTypeUrl[type_][operation]}")
        if betaonly:
            self.log.debug(f"this {type_} object {operation} only support beta version")
            url = f"{self.graph_beta_api_endpoint}{AadGraphTypeUrl[type_][operation]}"
        else:
            url = f"{self.graph_api_endpoint}{AadGraphTypeUrl[type_][operation]}"
        self.log.debug(f"correct url is generated {url}")
        return url

    def graph_all(self, url, type_):
        """
        get all objects in the azure ad
        """
        self.log.debug(f"will get all {type_} objects")
        self.log.debug(f"{type_} objects have total {self.type_operation(type_, operation='count')} objects")
        self.log.debug("process all objects, it may take a while")
        filename = os.path.join(get_log_dir(), f"aad_{type_}_all_{datetime.datetime.now().strftime("%H%M%S")}.json")
        currentpage = 0
        objs, page = self.graph_requests(url, type_, operation="page",  page=currentpage)
        while not isinstance(page, int):
            self.log.debug(f"current page is No. {currentpage} will process next page  {page}")
            currentpage = currentpage +1
            sleep(2)
            nextobjs_, page = self.graph_requests(page, type_, operation="page", page=currentpage)
            objs = objs + nextobjs_
            self.log.debug(f"current objs length is {len(objs)}, current page is {currentpage}, return page is {page}")
            if len(objs) > 900:
                self.log.debug(f"found more than 1000 objects, will save data to file first then continue")
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        oldobjs = json.load(f)
                    self.log.debug(f"old objs length is {len(oldobjs)}")
                else:
                    oldobjs = []
                newobjs = oldobjs + objs
                self.log.debug(f"new objs length is {len(newobjs)}")
                print(f"first and last objects are: {objs[0]['id']} {objs[-1]['id']}. current page is {currentpage} with {len(newobjs)} objects")
                with open(filename, "w") as f:
                    json.dump(newobjs, f)
                objs = []
        return objs, currentpage

    @renew_token
    def graph_requests(self, url, type_, operation="list", page=0, new_define=None):
        """
        run graph request and return result
        Args:
            url     (str)       url for the graph request
        Return:
            objs    (list)      list of objects from graph result
        """
        self.log.debug(f"will process the following {url}")
        if operation in ["list","count", "find", "id", "search", "delta", "one", "all", "page"]:
            result = requests.get(url, headers=self.headers, timeout=10)
        elif operation == "create":
            if type_ == "ca_auth_context":
                self.log.debug("auth context only support update with patch operation")
                url = f"{url}/{new_define['id']}"
                del new_define['id']
                self.log.debug(f"will create the ca auth context object {new_define} with {url}")
                result = requests.patch(url, headers=self.headers, json=new_define, timeout=10)
            else:
                result = requests.post(url, headers=self.headers, json=new_define, timeout=10)
        elif operation == "update":
            result = requests.patch(url, headers=self.headers, json=new_define, timeout=10)
        elif operation == "delete":
            result = requests.delete(url, headers=self.headers, timeout=10)

        if result.status_code in [200, 201]:
            if operation in ["one", "page"]:
                self.log.debug("only return the first page, no need go ahead even there is more page")
                objs, page = self.graph_requests_result_process(result, type_, operation=operation, page=page,
                                                                firstpage=True)
                if '@odata.nextLink' in result.json():
                    self.log.debug("found next page link, add one more page to page count")
                    page = result.json()['@odata.nextLink']
            elif operation in ["list", "all", "find", "search", "count", "delta"]:
                if page > 29:
                    self.log.debug("list operaiton return more than 3k objects, return the count instead")
                    objs = self.type_operation(type_, operation="count")
                    page = 0
                else:
                    objs, page = self.graph_requests_result_process(result, type_, operation=operation, page=page)
            else:
                objs, page = self.graph_requests_result_process(result, type_, operation=operation, page=page)
        elif result.status_code == 204:
            if operation == "udpate":
                self.log.debug("object attribute is updated")
            elif operation == "delete":
                self.log.debug("object is deleted")
            objs = None
            page = None
        elif result.status_code == 400:
            self.log.debug("reqeust return 400 error")
            objs = result
            page = None
            raise ADException("azuread", 503, f"result is {result.text}")
        elif result.status_code == 404:
            objs = None
        else:
            raise ADException("azuread", 501, f" {url} reutrn {result.text}")

        if isinstance(objs, list) and len(objs) >0:
            for obj_ in objs:
                obj_['type'] = type_
        return objs, page

    def group_objs_create(self, types=None, prestring="GroupObj"):
        """ create group objects based on the types
        args:
            types    (string)    object type, select from the following type
                                    user, group, reg_app, ent_app
            prestring (string)    the string put before the object name
        return:
            group_objs    (dict)    dict for each type. a list of type objects
        """
        group_objs = {}
        self.log.debug("start to create objects in group")
        for type_ in types:
            operation_ins = getattr(self, f"{type_}")
            obj_count = operation_ins(operation="count")
            self.log.info(f"There are total {obj_count} {type_} in Azure directory")
            newobj_name = f"{prestring}_{type_}"
            self.log.debug(f"will create the following object {newobj_name}")
            new_def = {}
            for atrribute in AadTypeAttribute[type_]['new']:
                new_def[atrribute] = newobj_name
            new_obj = operation_ins(operation="create",**new_def)
            self.log.debug(f"a new {type_} object created or found {new_obj}")
            group_objs[type_] = new_obj
        return group_objs

    def group_objs_check(self, objs, deleted=False):
        """
        check grouped objects
        Args:
            objs    (dict)      different type objects
        return:
            group_objs  (dict)      dict for each type. an object in each object type
        """
        group_objs = {}
        self.log.debug("start to check following objects in group")
        for type_ in objs:
            operation_ins = getattr(self, f"{type_}")
            obj_ = objs[type_]
            if deleted:
                group_objs[type_] = operation_ins(operation="deletelist", **{"id": obj_['id']})
            else:
                group_objs[type_] = operation_ins(**{"id": obj_['id']})
        return group_objs

class CvAzureAd():
    """ azure ad class for CV software"""

    def __init__(self, aad_ins, sc_ins):
        """ initial class
        args:
            aad_ins     ins    AzureAd instance
            sc_ins        ins     subclient instnace from test case
        """
        self.log = aad_ins.log
        self.aad_ins = aad_ins
        self.subclient = sc_ins

    def cv_restore_option_builder(self, cv_objs, type_, overwrite=True, browsetime=None):
        """ create cv restore option file
        args:
            cv_objs    list    azuread objects stored in cv backup
            types    (list)    object type, select from the following type
                                    user, group, reg_app, ent_app
            overwrite    Boolean    restore overwrite option
        return:
            restore_options    dict    restore option to create restore job
        """
        restore_items = []
        self.log.debug(f"This is the object will be restored {cv_objs}")
        for _ in cv_objs:
            item_ = {"type" : AadIndexMeta[type_],
                     "isFolder" : False,
                     "id": _['guid']}
            restore_items.append(item_)
        restore_options = {"fs_options" : {"overwrite" : overwrite},
                           "restore_option" : {"azureADOption" : {"restoreAllMatching": False,
                                                                  "restoreMembership" : True,
                                                                  "newUserDefaultPassword": "",
                                                                  "items": restore_items}}}
        if browsetime:
            self.log.debug(f"restore from the browsetime {browsetime}")
            restore_options['to_time'] = browsetime
        self.log.debug(f"restore job option is {restore_options}")
        return restore_options

    def cv_obj_delete_restore(self, sourceobjs, harddelete=False):
        """ process azure ad object, delete it first delete then run the restore job
        args:
            sourceobjs    list    auzre ad objects of source
            types        list    list of types from the following type
                                    user, group, reg_app, ent_app
            harddelete    Boolean    if the object type support hard delete or not
        return:
            obj_result    list    azure ad objects after rstore job
        """
        obj_result = {}
        for type_ in sourceobjs:
            operation_ins = getattr(self.aad_ins, type_)
            obj_ = sourceobjs[type_]
            self.log.debug(f"will delete {type_} object {obj_['id']}")
            operation_ins(operation="delete", **{"id": obj_['id']})
            self.log.debug("Wait for 60 seconds to check delete item in recycle bin")
            sleep(60)
            deletedlist = operation_ins(operation="deletelist", **{"id": obj_['id']})

            if deletedlist is not None and len(deletedlist) == 1:
                self.log.debug(f"{type_} object {obj_['id']} found in recycle bin with value like {deletedlist[0]}")
                if harddelete:
                    self.log.debug("hard delete is set, will permanent delete it")
                    operation_ins(operation="harddelete", **{"id": obj_['id']})
                    self.log.debug(f"{type_} object {obj_['id']} is hard deleted")
            else:
                deleted_state = False
                self.log.debug(f"{type_} object {obj_['id']} NOT found. it is hard deleted already")

            find_result = operation_ins(operation="find", **{"id": obj_['id']})
            if not find_result:
                self.log.debug(f"{type_} object {obj_['id']} is removed")
            self.cv_obj_restore(obj_)
            self.log.debug("Wait for 30 seconds to check objects after restore")
            sleep(30)

            obj_match = self.cv_objs_compare(sourceobjs, harddelete=harddelete)
            obj_result[type_] = obj_match
        self.log.debug(f"objects result after restore {obj_result}")
        return obj_result

    def cv_obj_change(self, sourceobjs, attribute_=None, value=None, attributes=None):
        """ process auzre object, change one attribute, then restor it
        args:
            sourceobjs    list    auzre ad objects of source
            types        list    list of types from the following type
                                    user, group, reg_app, ent_app
            changevlue    dict    type based change dict, will pass to change option
        return:
            changevalue    dict    type based change dict, use for compare
        """
        changevalue = {}
        for type_ in sourceobjs:
            self.log.debug(f"start to get default change value for {type_} object")
            operation_ins = getattr(self.aad_ins, type_)
            if attribute_:
                attribute = attribute_
            elif attributes:
                self.log.debug(f"passed the attributes {attributes}  to process")
                attribute = list(attributes[type_].keys())[0]
                self.log.debug(f"will update {type_} object attribute: {attribute}")
            else:
                attribute = random.choice(AadTypeAttribute[type_]['other'])

            if value:
                value_ = f"{attribute}_{value}"
            else:
                timestamp = int(datetime.datetime.now().timestamp())
                value_ = f"{attribute}_changed_to_{timestamp}"
            self.log.debug(f"here is the change attribute {attribute} and value {value_}")
            self.log.debug("wait 20 seconds before update the object")
            sleep(20)
            obj_ = operation_ins(**{"id": sourceobjs[type_]['id']})
            changevalue[type_] = {"id": obj_['id'],
                                  attribute: value_}
            self.log.debug(f"before change, {type_} object with id {obj_['id']} and {attribute} : {obj_[attribute]}")
            new_obj = operation_ins(operation="update", **changevalue[type_])
            self.log.debug("wait 20 seconds before update the object")
            sleep(20)
            new_obj = operation_ins(**{"id": sourceobjs[type_]['id']})
            self.log.debug(f"after change, {type_} object with id {new_obj['id']} and {attribute} : {new_obj[attribute]}")
            del changevalue[type_]['id']

        self.log.debug(f"There is the change value {changevalue}")
        return changevalue

    def cv_obj_change_restore(self, sourceobjs, job_base, attributes):
        """ run retore job from base and restore to old way
        args:
            sourceobjs    list    auzre ad objects of source
            job_ins        ins    the resetore job instance
        """
        obj_result = {}
        for type_ in sourceobjs:
            operation_ins = getattr(self.aad_ins, type_)
            attribute = list(attributes[type_].keys())[0]
            obj_ = sourceobjs[type_]
            self.log.debug("check current object attirbute value")
            current_obj = operation_ins(**{"id": obj_['id']})
            self.log.debug(f"current attribute {attribute} has value:  {current_obj[attribute]}")
            self.log.debug("start to restore object from base job")
            browse_restore_time = job_base.end_time
            self.cv_obj_restore(obj_, browsetime=browse_restore_time)
            self.log.debug("wait 30 seconds to check the restored value")
            sleep(30)
            restored_obj = operation_ins(**{"id": obj_['id']})
            self.log.debug(f"restored attribute {attribute} has value:  {restored_obj[attribute]}")
            if restored_obj[attribute] != current_obj[attribute]:
                self.log.debug(f"after restore attribute {attribute} value change \
                                from {current_obj[attribute]} to {restored_obj[attribute]}")
                obj_result[type_] = True
            else:
                obj_result[type_] = False
                self.log.debug(f"after restore attribute {attribute} value change \
                                from {current_obj[attribute]} to {restored_obj[attribute]}")
        return obj_result

    def cv_obj_restore(self, obj_, matchobj=True, browsetime=None):
        """ run a restore job with more options
        args:
            obj_    obj    azure ad object
            matchobj     Boolean    decide if search by object id or name
        return:
            restore_job    ins    restore job instance
        """
        self.log.debug(f"start to restore {obj_}")
        if browsetime:
            browse_option ={"to_time" : browsetime,
                            "folder" : obj_['type'], "search" : obj_['displayName'], "show_deleted": True}
        else:
            browse_option = {"folder" : obj_['type'], "search" : obj_['displayName'], "show_deleted": True}
        self.log.debug(f"The browse option is {browse_option}")
        count, aad_ids = self.subclient.browse(**browse_option)
        self.log.debug(f"restore {count} ojbects and the objcts list is {aad_ids}")
        if matchobj:
            match_obj = []
            for _ in aad_ids:
                if _['azureid'] == obj_['id']:
                    match_obj.append(_)
                    break
            aad_ids = match_obj
        restore_option = self.cv_restore_option_builder(aad_ids, obj_['type'], browsetime=browsetime)
        restore_job = self.subclient.restore_in_place(**restore_option)
        self.log.info(f"restore job {restore_job.job_id} started")
        jobresult = restore_job.wait_for_completion()
        if not jobresult:
            raise ADException("cvaad", 201,
                              f"restore job have some issue {restore_job.summary}.")
        self.log.info(f"restore job {restore_job.job_id} is completed with {jobresult}")

    def cv_objs_compare(self, source, attributes=None, harddelete=False):
        """
        compare multiple objects
        """
        match_result = False
        for type_ in source:
            operation_ins = getattr(self.aad_ins, type_)
            source_objs = source[type_]
            obj_ = source_objs
            if harddelete:
                self.log.debug(f"{type_} object is hard deleted, check the displayname")
                destination_obj = operation_ins(**{"displayName": obj_['displayName']})
            else:
                destination_obj = operation_ins(**{"id": obj_['id']})

            if isinstance(destination_obj,dict):
                self.log.debug(f"found {type_} object {obj_['id']} in browse")
                if attributes:
                    match_result = self.cv_obj_compare(obj_, destination_obj[0], attributes=attributes)
                else:
                    match_result = True
                    self.log.debug("object is matched")
            else:
                raise ADException("cvaad", "501", f"found {destination_obj}")
        self.log.debug(f"objects compare result is {match_result}")
        return match_result

    def cv_obj_compare(self, source_obj, dest_obj, attributes=None):
        """ find the matching objects and compare with source obj
        args:
            source_obj    list    azure ad object
        return:
            obj_match    Boolean    return compare result state
        """
        match_result = []
        for _ in attributes:
            self.log.debug(f"check attribute {_} between two objects ")
            if source_obj[_] == dest_obj[_]:
                match_result[_] = True
            else:
                match_result[_] = (source_obj[_], dest_obj[_])

        final_result = True
        for _ in match_result:
            if isinstance(match_result[_], tuple):
                final_result = False
            else:
                del match_result[_]

        if final_result:
            match_result = True
        return match_result

    def cv_obj_browse_check(self, objs, job_ins):
        """ check backup job result and source obj
        args:
            obj             list    azure ad objects list of source data to check
            job_ins        ins      the latest backup job instance
        """
        browse_time = job_ins.summary['lastUpdateTime']
        browse_restore_time = job_ins.end_time
        jobinfo = {}
        jobinfo['totalobjs'] = job_ins.summary['totalNumOfFiles']
        jobinfo['totalsize'] = job_ins.summary['sizeOfApplication']
        self.log.info(f"here is the backup job info: {jobinfo}")
        self.log.debug(f"Backup job {job_ins.job_id} with browse time {browse_time}")
        for type_ in objs.keys():
            browse_option = {
                "to_time" : browse_time,
                "folder" : type_,
                "show_deleted" : False}
            sleep(30)
            self.log.debug("wait 30 seconds to check browse result")
            count, result = self.subclient.browse(browse_option)
            self.log.debug(f"browse {type_} has {count} objects and top result are {result}")
            if count == len(objs[type_]):
                self.log.debug(f" Browse return {count}, it match objects in azure AD {result}")
            else:
                self.log.debug(f"Browse object count {count} is not match AD object count {len(objs)}")
                self.log.debug(f"will check particular object {objs}")
                browse_option = {
                    "to_time": browse_time,
                    "folder": type_,
                    "show_deleted": False,
                    "search" : {
                        "obj_id" : objs[type_]['id']
                    }}
                count, result = self.subclient.browse(browse_option)

                if count:
                    self.log.debug(f"found the {objs[type_]} in browse {result}")
                else:
                    raise ADException("cvaad", 302, f"browse doesn't return {objs[type_]}")
