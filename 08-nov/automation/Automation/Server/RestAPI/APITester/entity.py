import re
import json
import copy
import traceback
import inspect
import requests as req
from Server.RestAPI.APITester import api_tester as at
from AutomationUtils import logger


class Entity:

    """

    => this class handles the entity and entity related operation

    => it creates combined object out of swagger and dependency file for each api and pass it to them.

    => it also resolve schema of swagger object send it with other attributes

    """

    def __init__(self, entity_config_json, swagger_json, server_base_url, payload_values_json):
        """

        => this initialization method creates the combined object with required swagger specification fetched and with
        the details in dependency file.

        => it creates the list of api_tester instances and store it in a list while build process.

        => it modifies the rule and join all of them with " and " and creates a single rule.

        => it also resolve the schema that is used with $ref.

        """

        try:
            self.server_base_url = server_base_url
            self.entity_config_json = entity_config_json
            self.log = logger.get_log()
            # if payload_rules are there then we need to replace symbols to words
            if "PayloadRules" in entity_config_json and len(entity_config_json["PayloadRules"]) > 0:
                self.rules = copy.deepcopy(entity_config_json["PayloadRules"])
                arr = list()
                for rule in self.rules:
                    modified_rule = "(" + rule + ")"
                    arr.append(modified_rule)
                self.payload_rules = arr

                # creating large_rule and replacing symbols

            assert "APIstoCall" in self.entity_config_json, "'APIstoCall' parameter is required!"

            self.ap_is = list(entity_config_json["APIstoCall"])

            # sorting order for sorting ap_is
            sort_order = ["POST", "PUT", "GET", "DELETE"]

            # sorting ap_is according to method of ap_is with custom sorting order
            self.ap_is.sort(key=lambda api: sort_order.index(api["RequestAPI"].split()[0].upper()))

            self.api_config_arr = list([])
            self.api_test_arr = list([])

            # for each api we will combine required things and pass them to api_tester
            for api in self.ap_is:

                copied_swagger_json = copy.deepcopy(swagger_json)
                assert "RequestAPI" in api, "'RequestAPI' parameter not found in ap_isto_call !"

                # getting swagger object and path from swagger
                api_config = self.get_swagger_object(copied_swagger_json, api["RequestAPI"])

                # if swagger object is None it will to raise Exception
                if api_config is None:
                    raise Exception("swagger object not found for given api!")

                assert api_config is not None, "no swagger object found for request_api : " + str(api["RequestAPI"])
                api_config["entityName"] = self.entity_config_json["entityName"]
                # api_config["path"] = path
                api_config["path"] = api["RequestAPI"].split()[1]
                api_config["type"] = str(api["RequestAPI"]).split()[0].upper()

                # if payload_rules are there then it attaches the final_rule that it created
                if "PayloadRules" in self.entity_config_json:
                    #api_config["final_rule"] = copy.deepcopy(self.final_rule)
                    api_config['payloadValues'] = copy.deepcopy(self.payload_rules)

                # if validate_resp_payload is there it attaches the corresponding things to object
                if "validateRespPayload" in self.entity_config_json:
                    if self.entity_config_json["validateRespPayload"]:
                        assert "validationAPI" in self.entity_config_json, "'validationAPI' is required!"
                        api_config["validationAPI"] = self.entity_config_json["validationAPI"]
                        if "validationMapping" in self.entity_config_json:
                            api_config["validationMapping"] = self.entity_config_json["validationMapping"]
                        if "validationIdParams" in self.entity_config_json:
                            api_config["validationIdParams"] = self.entity_config_json["validationIdParams"]
                        if "ignoreValidation":
                            api_config["ignoreValidation"] = self.entity_config_json["ignoreValidation"]

                # if fetch_id_from_resp is True it will add it to object
                if "fetchIdFromResp" in self.entity_config_json:
                    if self.entity_config_json["fetchIdFromResp"]:
                        assert "idParams" in self.entity_config_json, "'idParams' is required!"
                        api_config["idParams"] = self.entity_config_json["idParams"]

                # if request_body is there it resolcve the schema and attaches to object
                if "requestBody" in api_config:
                    api_config["requestBody"]["resolvedSchema"], payload_value_check = self.get_resolved_schema(
                        api_config["requestBody"]["content"]["application/json"]["schema"], copied_swagger_json)

                # if response has any schema it resolves it and add it to object
                if "responses" in api_config:
                    for resp_code in api_config["responses"]:
                        if "content" in api_config["responses"][resp_code]:
                            if "application/json" in api_config["responses"][resp_code]["content"]:
                                api_config["responses"][resp_code]["resolvedSchema"], payload_value_check = \
                                    self.get_resolved_schema(
                                    api_config["responses"][resp_code]["content"]["application/json"]["schema"],
                                        copied_swagger_json)

                # it passes all properties to swagger object and replace if the key is there
                for key in api:
                    if key == "RequestAPI":
                        continue
                    api_config[key] = api[key]

                # saving the object
                self.api_config_arr.append(api_config)

                # creating api_test object
                tester = at.ApiTest(api_config, server_base_url, payload_values_json)

                # appending it for further use
                self.api_test_arr.append(tester)

        except Exception as exp:
            self.log.info("error : " + str(exp) + str(traceback.format_exc()))
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(exp)))

    def get_resolved_schema(self, schema_object, swagger_json, path=""):
        """

        => this method resolve the schema $ref and return the whole schema with no $ref

        """

        payload_value_check = list([])
        if not isinstance(schema_object, dict):
            return schema_object, payload_value_check

        # $ref is there then it calles sub method to fetch schema object and put it here
        if "$ref" in schema_object:
            schema_object, flag = self.get_schema_ref(schema_object["$ref"], swagger_json)
            if flag:
                # this is to check special case like id_name
                payload_value_check.append(path)
            schema_object, sub_payload_value_check = self.get_resolved_schema(schema_object, swagger_json, path)
            payload_value_check.extend(sub_payload_value_check)

        # just resolve and put if $erf is there otherwise it will replace directly
        elif "type" in schema_object:
            if schema_object["type"] == "object":
                if "$ref" in schema_object["properties"]:
                    schema_object["properties"], sub_payload_value_check = self.get_resolved_schema(
                        schema_object["properties"], swagger_json, path)
                    payload_value_check.extend(sub_payload_value_check)
                else:
                    for key in schema_object["properties"]:
                        if path == "":
                            sub_path = key
                        else:
                            sub_path = path + "." + key
                        schema_object["properties"][key], sub_payload_value_check = self.get_resolved_schema(
                            schema_object["properties"][key], swagger_json, sub_path)
                        payload_value_check.extend(sub_payload_value_check)
            elif schema_object["type"] == "array":
                if "$ref" in schema_object["items"]:
                    schema_object["items"], sub_payload_value_check = self.get_resolved_schema(
                        schema_object["items"], swagger_json, path)
                    payload_value_check.extend(sub_payload_value_check)
                else:
                    for key in schema_object["items"]:
                        schema_object["items"][key], sub_payload_value_check = self.get_resolved_schema(
                            schema_object["items"][key], swagger_json, path)
                        payload_value_check.extend(sub_payload_value_check)
        return schema_object, payload_value_check

    def get_schema_ref(self, refstring, swagger_json):
        """

        => returning the schema object from the refstring

        """

        ref_arr = refstring.split('/')
        if "IdName" in ref_arr:
            flag = True
        else:
            flag = False
        temp_obj = swagger_json[ref_arr[1]]
        for i in range(2, len(ref_arr)):
            temp_obj = temp_obj[ref_arr[i]]
        return temp_obj, flag

    def get_swagger_object(self, swagger_json, request_api):
        """

        => this method fatches swagger object for given request_api

        """

        req = str(request_api).split()
        match_path = re.sub(r'\{[^}]*\}', '{}', req[1]).lower()
        method = req[0].lower()
        assert "paths" in swagger_json, "no paths found in swagger documantation!"
        for path in swagger_json["paths"]:
            swagger_match_path = re.sub(r'\{[^}]*\}', '{}', path).lower()
            for api_type in swagger_json["paths"][path]:
                if swagger_match_path == match_path and api_type.lower() == method:
                    return swagger_json["paths"][path][api_type]
        return None

    def del_key(self, path, chunk, edited_chunk, explored_path=""):
        """

        => this method deletes the given path from dict

        """

        if not isinstance(chunk, dict):
            return edited_chunk
        if "type" in chunk:
            if chunk["type"] == "object":
                for key in chunk["properties"]:
                    if explored_path == "":
                        sub_path = key
                    else:
                        sub_path = explored_path + "." + key
                    if sub_path == path:
                        if "properties" in edited_chunk:
                            if key in edited_chunk["properties"]:
                                del edited_chunk["properties"][key]
                        return edited_chunk
                    else:
                        if path.startswith(sub_path):
                            edited_chunk["properties"][key] = self.del_key(
                                path, chunk["properties"][key], edited_chunk["properties"][key], sub_path)
                        else:
                            continue
            elif chunk["type"] == "array":
                for key in chunk["items"]:
                    edited_chunk["items"] = self.del_key(path, chunk["items"], edited_chunk["items"], explored_path)
        return edited_chunk

    def build(self):
        """

        => this method builds the schema set of all saved api_tester object

        """

        for tester in self.api_test_arr:
            tester.build()

    def get_entity_name(self):

        # return entity name
        if "entityName" in self.entity_config_json:
            return self.entity_config_json["entityName"]
        else:
            return None

    def run_entity_test(self, auth_token):
        """

        => it runs the entity cases by calling all the saved api_tester.

        => if fetch_id_from_resp is True then, if api type is post it receives id_params from the api_tester.run(),else
        it passes the id_params to run method of api_tester

        """

        if "fetchIdFromResp" in self.entity_config_json:
            if self.entity_config_json["fetchIdFromResp"]:
                assert "idParams" in self.entity_config_json, "'idParams' is required!"
                for tester in self.api_test_arr:
                    api_type = tester.get_api_type()
                    if api_type == "POST":
                        self.id_params = tester.run(
                            auth_token=auth_token, id_params_path=self.entity_config_json["idParams"])
                    else:
                        tester.run(auth_token=auth_token, id_params_dict=self.id_params)
            else:
                for tester in self.api_test_arr:
                    tester.run(auth_token=auth_token)
            if self.id_params:
                self.cleanup(auth_token)
        else:
            for tester in self.api_test_arr:
                tester.run(auth_token=auth_token)

    def cleanup(self, auth_token):
        """

        => this method runs after the testing is done.

        => it is used to clean entity created while testing.

        => only fixed payload is allowed for now.

        """

        if "CleanupPhase" not in self.entity_config_json:
            return None
        req_headers = {
            'connection': 'keep_alive',
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authtoken': auth_token
        }
        self.log.info("<=====================================================================>")
        self.log.info("cleanup phase...")
        for param_id_dict in self.id_params:
            self.log.info("_______________________________________________________________________")
            self.log.info("IdParams:")
            self.log.info(json.dumps(param_id_dict, indent=4))
            for api_config in self.entity_config_json["CleanupPhase"]:
                api = api_config["RequestAPI"]
                api_type = api.split()[0]
                api_path = api.split()[-1]
                replace_server_url = copy.copy(self.server_base_url) + api_path
                for key in param_id_dict:
                    query = r"\{" + str(key) + r"\}"
                    value = param_id_dict[key]
                    replace_server_url = re.sub(query, value, replace_server_url)
                self.log.info("request url : " + api_type.upper() + " " + replace_server_url)
                if "Payload" in api_config:
                    req_payload = json.dumps(api_config["Payload"])
                    clean_resp = req.request(
                        method=api_type,
                        data=req_payload,
                        url=replace_server_url,
                        headers=req_headers)
                else:
                    clean_resp = req.request(method=api_type, url=replace_server_url, headers=req_headers)
                self.log.info("response status code : " + str(clean_resp.status_code))
            self.log.info("_______________________________________________________________________")
        self.log.info("<=====================================================================>")
