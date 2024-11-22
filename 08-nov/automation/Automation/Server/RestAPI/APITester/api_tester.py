import json
import copy
import inspect
import re
import random
import requests as req
from jsonschema import validate
from tt import BooleanExpression
from jinja2 import Template
from Server.RestAPI.APITester.generator import Generator
from AutomationUtils import logger


class ApiTest:

    """

    => "ApiTest" class handles single api and perform the actual lower level work.

    => it create test case and send the request after checking for schema.

    => then it run the templating engine and get the required values and for other value it generate it randomly.

    => it get the response and verifies it with get request.

    """

    def __init__(self, api_json, server_base_url, payload_values_json):
        """
        => initialize and save class parameters.

        """

        self.basic_data_types = ["string", "boolean", "number", "integer"]
        self.path_params_match_regex = r"\{[^}]*\}"
        self.log = logger.get_log()
        try:
            if api_json is not None:
                self.api_json = copy.deepcopy(dict(api_json))
            else:
                raise Exception("api config object is required!")
            if server_base_url is not None:
                self.server_base_url = server_base_url
            else:
                raise Exception("server base_url is required!")

            if payload_values_json is not None:
                self.payload_values_json = payload_values_json
            else:
                raise Exception("payload values is required!")
        except Exception as exp:
            self.log.info("Exception : ", exp)
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(exp)))

    def build(self):
        """

        => this method calls create_api_set to get the test cases and store it in a class variable.

        """

        if "requestBody" in self.api_json:
            self.api_set = self.create_api_set(self.api_json["requestBody"]["resolvedSchema"])
        else:
            self.api_set = None

    def create_api_set(self, schema):
        """

        => this method defines the flow of generating test cases.

        => first it extracts the required schema from the original schema by calling another method. required schema the
         keys that are reuired in each payload.

        => then it extracts the optional schema from the original schema set by calling another moethod. optional schema
         set is the set of all optional schemas that satisfies the dependency rules.

        => then this method runs a loop and combine required schema and corresponding optional schema from optional
        schema set to create an instance of final schema.

        => then it will send this schema for data generation and the generated data is stored in array and returned.

        """

        # extracting required schema
        required_schema = self.get_required_schema(schema)

        # extracting optional schema
        optional_schema_set = self.get_optional_schema_set(schema)

        final_payload_set = []

        # reading templating engine for all use
        with open(self.payload_values_json) as f:
            str_payload_values = f.read()

        # defining templating engine
        t = Template(str_payload_values)

        # creating final payload according to different cases.
        if required_schema is None:

            # only optional schema set is there in this case.
            for optional_schema in optional_schema_set:
                optional_schema_data = self.generate_data(optional_schema, t)
                final_payload_set.append(optional_schema_data)

        elif optional_schema_set is None:

            # only required schema is there in this case
            required_schema_data = self.generate_data(required_schema, t)
            final_payload_set.append(required_schema_data)

        else:

            # both required and optional schema is present

            # case of only required schema
            only_required = self.generate_data(required_schema, t)
            final_payload_set.append(only_required)

            # combining schemas and then generating payload data
            for optional_schema in optional_schema_set:
                final_schema = self.combine(required_schema, optional_schema)
                final_payload = self.generate_data(final_schema, t)
                final_payload_set.append(final_payload)

        return final_payload_set

    def get_optional_schema_set(self, schema):
        """

        => this method creats the set out of single large schema.

        => it first extract the large optional schema by calling sub method and then it calls another method to chunk
        them. chunk process creates schema for each key in large optional schema with satisfied payloadrules.

        => after calling this sub method it returns this optional schema set.

        """

        # extracting large optional schema
        optional_schema_large = self.get_optional_schema(schema)

        # if large schema is not there no need to chunk it.
        if optional_schema_large is None:
            optional_schema_set = None

        # if it is there then we will call the method for chunking it.
        else:
            optional_schema_set = self.get_optional_schema_chunk(optional_schema_large)
        return optional_schema_set

    def get_optional_schema(self, schema):
        """

        => this method recursively extracts the large optional schema.

        => the key point for recurssion:
           _> if there is an optional property add it directly
           _> else if the property is required explore more for the optional properties in sub structure
           _> combine all sub structure chunks and return it.

        """
        # if the instance is not dictionary it returns None as we have reached to leaf for searching
        if not isinstance(schema, dict):
            return None
        optional_schema_large = None

        # handling the case for object
        if schema["type"] == "object":

            # if required is there then we have to handle recursion case
            if "required" in schema:

                # looping for all key in schema
                for key in schema["properties"]:

                    # if key is in required just recursively search for the optional schema
                    if key in schema["required"]:
                        sub_schema = self.get_optional_schema(schema["properties"][key])
                    # else we will add it directly as whole structure is not required
                    else:
                        sub_schema = schema["properties"][key]
                    # if subschema is not None we will add it with key
                    if sub_schema is not None:
                        # defining it as dictionary if it is not
                        if not isinstance(optional_schema_large, dict):
                            optional_schema_large = dict({})
                        if "type" not in optional_schema_large:
                            optional_schema_large["type"] = "object"
                        if "properties" not in optional_schema_large:
                            optional_schema_large["properties"] = dict({})
                        optional_schema_large["properties"][key] = sub_schema

            # required is not there so no need to handle recursion case just add all of them
            # we can directly copy whole properties object
            else:
                optional_schema_large = dict({})
                optional_schema_large["type"] = "object"
                optional_schema_large["properties"] = schema["properties"]

        # else if the type of object is array we send items for recursive search
        elif schema["type"] == "array":
            sub_schema = self.get_optional_schema(schema["items"])
            if sub_schema is not None:
                optional_schema_large = dict({})
                optional_schema_large["type"] = "array"
                optional_schema_large["items"] = sub_schema
        # else we will return null
        else:
            return None
        # returning the final optional large schema
        return optional_schema_large

    def get_rule_per_chunk_key(self, key, payload_rules, final_rule=None):
        if not final_rule:
            final_rule = []
        rules = key.split(".")
        temp_rules = []
        for i in range(len(rules), 0, -1):
            rule_key = ".".join(rules[:i])
            r = re.compile(f"(?:^|\W){rule_key}(?:$|\W)", re.IGNORECASE)
            temp_rules.extend(list(filter(r.findall, payload_rules)))
        temp_rules = list(set(temp_rules))
        if not temp_rules:
            return final_rule
        else:
            for rule in temp_rules:
                if rule not in final_rule:
                    final_rule.append(rule)
                    payload_rules.remove(rule)
                    matches = re.findall(r"[a-z.A-Z]+", rule)
                    for match in matches:
                        final_rule = self.get_rule_per_chunk_key(match, payload_rules, final_rule)
                return final_rule

    def get_optional_schema_chunk(self, large_schema):
        """

        => this method takes optional large schema and return optional schema set with rules satisfied.

        => it adds extra rule for each sub structure as followings:
            main_key <=> ( subkey1 || sub_key2 || ... || sub_key_n )

        => it calls sub method for getting chunked schema set for each key. then it takes each key as constraint
        and get one of the solution that satisfies all the rules.
        according to the solution we will use add the required things.

        => for boolean variables we will add one case for False and one case for True, if it is in dependency.

        """

        chunks = dict({})

        # we get all the chunks for each possible key in optional large schema
        chunks = self.get_all_chunks(large_schema, "")

        # extra_rules_dict is a dict that has sub_structure's main_key to sub_structure's sub_key
        if self.api_json["payloadValues"]:
            fixed_vals = dict()
            # it takes each key as constraint and make it as True. then it gets one of the solution that follows final
            # rules joined with "and".
            for key in chunks:
                match_key = key.replace('.', '_')
                dependency_rule = None
                if self.api_json["payloadValues"]:
                    dependency_rule = self.get_rule_per_chunk_key(key, copy.deepcopy(self.api_json["payloadValues"]))

                # as module does not support keywords with "." it first replace "." with "_"
                # if "_" is there in actual payload, we need to change this code.
                # one of the solution is to map keys with alphabates like a,b,...,z,aa,ab,...
                if dependency_rule:
                    large_rule = " and ".join(dependency_rule)
                    large_rule = large_rule.replace("!", "not ")
                    large_rule = large_rule.replace("^", "xor")
                    large_rule = large_rule.replace("&&", "and")
                    large_rule = large_rule.replace("||", "or")
                    large_rule = large_rule.replace("<=>", "iff")
                    large_rule = large_rule.replace("=>", "impl")
                    dependency_rule = large_rule
                    dependency_rule_arr = dependency_rule.split('.')
                    dependency_rule = "_".join(dependency_rule_arr)
                    b = BooleanExpression(dependency_rule)
                    key_arr = b.symbols
                    min_sol = dict({})

                    if match_key not in key_arr:
                        # for root items we will choose any one child dependency
                        match_keys = [key_path for key_path in key_arr if match_key + "_" in key_path]
                        if match_keys:
                            match_key = match_keys[0]
                        else:
                            # this is for non dependencies from parent objects for a child key
                            # (status.options is a key for status.options.disabledbackup)
                            match_parent_keys = [key_path for key_path in key_arr if key_path + "_" in match_key]
                            if match_parent_keys:
                                match_key = match_parent_keys[0]
                            else:
                                match_key = random.choice(key_arr)

                    constr = dict()

                    # setting constraints
                    """
                    if flag == True:
                        constr[match_key] = int(rand_bool)
                    else:
                        constr[match_key] = 1
                    """
                    constr[match_key] = 1
                    with b.constrain(**constr):
                        min_sol = b.sat_one()._asdict()
                        for sol_key in min_sol:
                            # actual path
                            dotted_key = ".".join(sol_key.split('_'))
                            # if key in solution is True it will combine it
                            if bool(min_sol[sol_key]):
                                if dotted_key in chunks:
                                    # add value to fix them according to dependency
                                    if self.get_var_type(dotted_key, chunks[dotted_key]) == "boolean":
                                        if key not in fixed_vals:
                                            fixed_vals[key] = dict()
                                        fixed_vals[key][dotted_key] = True
                                    if not key.startswith(dotted_key):
                                        chunks[key] = self.combine(chunks[key], chunks[dotted_key])
                            elif not bool(min_sol[sol_key]):
                                chunks[key] = self.del_key(dotted_key, chunks[key], copy.deepcopy(chunks[key]))

                # if key is boolean then we need to preset the value
                type_of_key = self.get_var_type(key, chunks[key])
                if type_of_key == "boolean":
                    rand_bool = random.choice([True, False])
                    if key not in fixed_vals:
                        fixed_vals[key] = dict()
                    fixed_vals[key][key] = rand_bool
                    flag = True
                else:
                    flag = False

            # fixing the values
            for fixed_val_key in fixed_vals:
                for sub_fixed_val_key in fixed_vals[fixed_val_key]:
                    #chunks[fixed_val_key] = self.set_value(chunks[fixed_val_key],sub_fixed_val_key,
                    # fixed_vals[fixed_val_key][sub_fixed_val_key])
                    chunks[fixed_val_key] = self.set_value(chunks[fixed_val_key], sub_fixed_val_key, True)

        chunk_arr = []
        # creates array of these chunks and returns it
        for key in chunks:
            chunk_arr.append(chunks[key])
        return chunk_arr

    def set_value(self, schema, path, value, explored_path="", type_of_var=None):
        """

        => it set the value of parameter with given path in schema

        => this can be used for dependency depending on values

        """
        if not isinstance(schema, dict) or not isinstance(schema, list):
            return schema
        if "type" in schema:
            if schema["type"] == "object":
                for key in schema["properties"]:
                    self.log.info(key)
                    if explored_path == "":
                        sub_path = key
                    else:
                        sub_path = explored_path + "." + key
                    if sub_path == path:
                        if type_of_var is not None:
                            if "type" in schema["properties"][key] and schema["properties"][key]["type"] == type_of_var:
                                schema["properties"][key] = value
                            else:
                                return schema
                        else:
                            schema["properties"][key] = value
                            return schema, True
                    elif path.startswith(sub_path):
                        schema["properties"][key] = self.set_value(
                            schema["properties"][key], path, value, sub_path, type_of_var=type_of_var)
            elif schema["type"] == "array":
                schema["items"] = self.set_value(schema["items"], path, value, explored_path, type_of_var=type_of_var)
            else:
                if explored_path == path:
                    return value
        else:
            return schema

    def get_var_type(self, path, schema):
        """

        => it returns the variable type of path in schema

        """

        path_arr = path.split('.')
        counter = 0
        while_counter = 0
        while counter < len(path_arr) and while_counter < 20:
            if not isinstance(schema, dict):
                return None
            if "type" in schema:
                if schema["type"] == "object":
                    for key in schema["properties"]:
                        if key == path_arr[counter]:
                            schema = schema["properties"][key]
                            counter += 1
                            break
                elif schema["type"] == "array":
                    schema = schema["items"]
                else:
                    return None
            else:
                return None
            while_counter += 1
        if not isinstance(schema, dict):
            return None
        elif "type" in schema:
            return schema["type"]
        else:
            return None

    def del_key(self, path, chunk, edited_chunk, explored_path=""):
        """

        => it delete the given path from chunk and returns the schema.

        => it should be call like this:
            self.del_key(path,chunk,copy.deepcopy(chunk))

        => deepcopy of chunk is required as we are iterating over chunk

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
                        del edited_chunk["properties"][key]
                        return edited_chunk
                    else:
                        if path.startswith(sub_path + "."):
                            edited_chunk["properties"][key] = self.del_key(
                                path, chunk["properties"][key], edited_chunk["properties"][key], sub_path)
                        else:
                            continue
            elif chunk["type"] == "array":
                # for key in chunk["items"]:
                edited_chunk["items"] = self.del_key(path, chunk["items"], edited_chunk["items"], explored_path)
        return edited_chunk

    def combine(self, dict1, dict2):
        """

        => it combines two dictionaries.

        => it recursively combine the keys that are present in both dict.

        """

        final_dict = dict({})
        for key in dict1:
            if not isinstance(dict1[key], dict):
                final_dict[key] = dict1[key]
            elif key in dict2:
                final_dict[key] = self.combine(dict1[key], dict2[key])
            else:
                final_dict[key] = dict1[key]
        for key in dict2:
            if key in final_dict:
                continue
            else:
                final_dict[key] = dict2[key]
        return final_dict

    def get_all_chunks(self, large_schema, path):
        """

        => it takes large schema and creates schema for each key.

        => for keys that has sub_structure it will one seprate schema for it with no key in it. this is to find
        solution without worrying about sub structure dependency.

        """

        chunks = dict({})
        if "type" in large_schema:

            # if object is there it will add that object with empty sub structure and
            # recurrsively gives chunks and combine them.

            if large_schema["type"] == "object":
                for key in large_schema["properties"]:
                    if path == "":
                        subpath = key
                    else:
                        subpath = path + "." + key
                    chunk = dict({})
                    chunk["type"] = "object"
                    chunk["properties"] = dict({})
                    chunk["properties"][key] = large_schema["properties"][key]
                    chunks[subpath] = chunk
                    sub_chunks = self.get_all_chunks(large_schema["properties"][key], subpath)
                    for subpath_chunk in sub_chunks:
                        chunk = dict({})
                        chunk["type"] = "object"
                        chunk["properties"] = dict({})
                        chunk["properties"][key] = sub_chunks[subpath_chunk]
                        chunks[subpath_chunk] = chunk

            # else if array is there it will run for for its item
            elif large_schema["type"] == "array":
                for key in large_schema["items"]:
                    sub_chunks = self.get_all_chunks(large_schema["items"], path)
                    for subpath in sub_chunks:
                        chunk = dict({})
                        chunk["type"] = "array"
                        chunk["items"] = sub_chunks[subpath]
                        chunks[subpath] = chunk

            # else we will return it as it hit base case
            else:
                chunks[path] = large_schema
        else:
            chunks[path] = large_schema
        return chunks

    def get_required_schema(self, schema, is_sub_structure=False):
        """

        => this method recursively extracts the required schema.

        => the key point for recurssion:
           _> for all the non_required properties, it will not add it.
           _> if there is required proeprty, it recursively find the required thing

        """

        if not isinstance(schema, dict):
            return schema
        required_schema = None

        # handling the object case
        if schema["type"] == "object":

            # if required is there we will recursively find from the schema and add them
            if "required" in schema:
                required_schema = dict({})
                required_schema["type"] = "object"
                required_schema["properties"] = dict({})
                for key in schema["required"]:
                    required_schema["properties"][key] = self.get_required_schema(schema["properties"][key], True)

            # if required is not there but it was called by upper function and it is
            # an object we will add them directly, is_sub_structure is a flag to
            # indicate that it is a subcall of method
            elif is_sub_structure:
                required_schema = dict({})
                required_schema["type"] = "object"
                required_schema["properties"] = schema["properties"]

        # if it is an array it will pass items to substructure and add it
        elif schema["type"] == "array":
            sub_schema = self.get_required_schema(schema["items"], True)
            if sub_schema is not None:
                required_schema = dict({})
                required_schema["type"] = "array"
                required_schema["items"] = sub_schema

        # else we will return it
        else:
            return schema
        return required_schema

    def generate_data_helper(self, schema, parent_key="", ref_dict=None):
        if not isinstance(schema, dict) and not isinstance(schema, list):
            return schema
        test_case = None
        if "enum" in schema:
            if ref_dict:
                return ref_dict
            return random.choice(schema["enum"])
        elif "type" in schema:
            if schema["type"] == "object":
                test_case = dict({})
                for key in schema["properties"]:
                    if ref_dict is not None and key in ref_dict:
                        sub_test_case = self.generate_data_helper(
                            schema["properties"][key], parent_key=key, ref_dict=ref_dict[key])
                    else:
                        sub_test_case = self.generate_data_helper(schema["properties"][key], parent_key=key)
                    if sub_test_case is not None:
                        test_case[key] = sub_test_case
            elif schema["type"] == "array":
                test_case = list([])
                if ref_dict is not None:
                    assert isinstance(ref_dict, list), "expected list for key " + parent_key + " !"
                    maxlen = len(ref_dict)
                else:
                    maxlen = random.randrange(1, 6)
                for i in range(0, maxlen):
                    if ref_dict is not None:
                        sub_test_case = self.generate_data_helper(
                            schema["items"], parent_key=parent_key, ref_dict=ref_dict[i])
                    else:
                        sub_test_case = self.generate_data_helper(schema["items"], parent_key=parent_key)
                    if sub_test_case is not None:
                        if sub_test_case not in test_case:
                            test_case.append(sub_test_case)
            elif schema["type"] in self.basic_data_types:
                if ref_dict is not None:
                    if ref_dict:
                        return ref_dict
                    else:
                        etype = schema["type"]
                        key = parent_key
                        if etype == "string":
                            capital_key = key[0].upper() + key[1:]
                            data_string = "test" + capital_key + str(random.randint(10000, 99999))
                            return data_string
                        elif etype == "boolean":
                            rand_bool = random.choice([False, True])
                            return rand_bool
                        elif etype == "number":
                            rand_num = random.randrange(0, random.randint(1, 99))
                            return rand_num
                        elif etype == "integer":
                            rand_num = random.randrange(0, random.randint(1, 99))
                            return rand_num
                        else:
                            capital_key = key[0].upper() + key[1:]
                            data_string = "test" + capital_key + str(random.randint(10000, 99999))
                            return data_string
                else:
                    etype = schema["type"]
                    key = parent_key
                    if etype == "string":
                        capital_key = key[0].upper() + key[1:]
                        data_string = "test" + capital_key + str(random.randint(10000, 99999))
                        return data_string
                    elif etype == "boolean":
                        rand_bool = random.choice([False, True])
                        return rand_bool
                    elif etype == "number":
                        rand_num = random.randrange(0, random.randint(1, 99))
                        return rand_num
                    elif etype == "integer":
                        rand_num = random.randrange(0, random.randint(1, 99))
                        return rand_num
                    else:
                        capital_key = key[0].upper() + key[1:]
                        data_string = "test" + capital_key + str(random.randint(10000, 99999))
                        return data_string
            else:
                key = parent_key
                capital_key = key[0].upper() + key[1:]
                data_string = "test" + capital_key + str(random.randint(10000, 99999))
                return data_string
        else:
            key = parent_key
            capital_key = key[0].upper() + key[1:]
            data_string = "test" + capital_key + str(random.randint(10000, 99999))
            return data_string
        return test_case

    def generate_data(self, schema, t):
        """

        => this method generates the data of schema passed to it.

        => it renders the template and take the json object corresponding to entity name in file. templating
        engine has globals as "__gen" parameter that is used to have different facilities to make the process easier.

        """

        if t is not None:
            g = Generator()

            # setting generator
            t.globals['__gen'] = g

            # passing with payload values data
            if "PayloadValuesData" in self.api_json:
                data = self.api_json["PayloadValuesData"]
                ref_dict = json.loads(t.render(**data))
                if "entityName" in self.api_json and self.api_json["entityName"] in ref_dict:
                    ref_dict = ref_dict[self.api_json["entityName"]]
                else:
                    ref_dict = None

            # passing without payload values data
            else:
                ref_dict = json.loads(t.render())
                if "entityName" in self.api_json and self.api_json["entityName"] in ref_dict:
                    ref_dict = ref_dict[self.api_json["entityName"]]
                else:
                    ref_dict = None
            return self.generate_data_helper(schema, ref_dict=ref_dict)
        else:
            return self.generate_data_helper(schema)

    def run(self, auth_token, id_params_path=None, id_params_dict=None):
        """

        => this method takes auth_token and other optional parameters to either collect the id_params or use the
        collected id_params.

        => it sends the request from created test set. it replace parameters in url by either from saved ones or by
        selecting the randomly from provided one.

        => first it validates the schema of request payload from the original swagger object and then after receiving
        the ok response it validates the schema of response payload.

        => after that if validation_resp_payload is set True it will do the additional get request and validate the
        request of test case to response of get api.

        => it keeps track of all failed cases.

        """

        self.failed_cases = list([])

        # url to use
        server_url = self.server_base_url + self.api_json["path"]

        # headers
        req_headers = {
            'connection': 'keep_alive',
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'authtoken': auth_token
        }
        if self.api_json.get("apiHeaders"):
            req_headers = {**req_headers, **self.api_json.get("apiHeaders")}
        self.id_params_path = list([])
        total_cases = 0

        # if set is there we want to loop through each payload and do the procedure for testing
        if self.api_set is not None:
            counter = 0
            total_cases = len(self.api_set)

            for api in self.api_set:

                replace_server_url = copy.copy(server_url)
                counter += 1
                self.log.info("_______________________________________________________________________")
                self.log.info("test case "+ str(counter)+ "/"+ str(total_cases))
                try:
                    # for tracking current parameters replaced
                    current_id_params = dict({})

                    # searching for any path parameters in url
                    if re.search(self.path_params_match_regex, replace_server_url):

                        # on match it need reference from where it can fetch payload
                        assert "PathParams" in self.api_json or id_params_dict is not None, "reference needed to " \
                                                                                             "manipulate id params!"

                        # case where we have path parameters from post response
                        if id_params_dict:
                            itr_dict = random.choice(id_params_dict)
                            for key in itr_dict:
                                query = r"\{" + str(key) + r"\}"
                                value = itr_dict[key]
                                current_id_params[key] = value
                                replace_server_url = re.sub(query, str(value), replace_server_url)
                        # case when we have explicitly defined path parameters
                        else:
                            itr = self.api_json["PathParams"]
                            for key in itr:
                                query = r"\{" + str(key) + r"\}"
                                value = random.choice(list(itr[key]))
                                current_id_params[key] = value
                                replace_server_url = re.sub(query, str(value), replace_server_url)
                    req_payload = json.dumps(api)
                    self.log.info("request body : ")
                    self.print_pretty_json(req_payload)

                    # validating the request schema with actual swagger schema
                    self.log.info("validating body...")
                    try:
                        validate(instance=api, schema=self.api_json["requestBody"]["resolvedSchema"])
                        self.log.info("validation successful...")
                    except Exception as e:
                        self.log.info("validation failed....")
                        self.failed_cases.append(counter)
                        continue

                    # sending request
                    self.log.info("sending request...")
                    self.log.info("request url: "+self.api_json["type"].upper()+" "+replace_server_url)
                    resp = req.request(
                        method=self.api_json["type"],
                        url=replace_server_url,
                        data=req_payload,
                        headers=req_headers)

                    # if response is ok then only we will do next steps
                    if resp.ok:
                        self.log.info("status code : "+ str(resp.status_code))
                        self.print_pretty_json(resp.json())
                        if "resolvedSchema" in self.api_json["responses"][str(resp.status_code)]:
                            self.log.info("validating response...")
                            try:
                                validate(instance=resp.json(),
                                         schema=self.api_json["responses"][str(resp.status_code)]["resolvedSchema"])
                                self.log.info("response schema validated...")
                                if id_params_path:
                                    current_id_params_path = dict({})
                                    for key in id_params_path:
                                        id_param_value = self.get_id_param(dict(resp.json()), id_params_path[key])
                                        current_id_params_path[key] = id_param_value
                                        self.id_params_path.append(current_id_params_path)
                            except Exception as e:
                                self.log.info("validation failed...")
                                self.failed_cases.append(counter)
                        try:
                            self.validate_resp(api, dict(resp.json()), auth_token, current_id_params)
                        except Exception as e:
                            self.log.info("Exception : "+str(e))
                            self.log.info("validation failed from api...")
                            self.failed_cases.append(counter)
                    # else we will self.log.info the status code and then append it to failedcases array
                    else:
                        self.log.info("status code : "+str(resp.status_code))
                        self.print_pretty_json(resp.json())
                        self.failed_cases.append(counter)
                except Exception as e:
                    self.log.info("Exception : "+str(e))
                    self.failed_cases.append(counter)
                finally:
                    self.log.info("test case over....")
                    self.log.info("_______________________________________________________________________")

            # self.log.infoing summary after sending all the request
            self.print_summary(total_cases, self.failed_cases)

        # if payload schema is not there we will send the url only once
        else:
            replace_server_url = copy.copy(server_url)
            counter = 1
            total_cases = 1
            self.log.info("_______________________________________________________________________")
            self.log.info("test case "+ str(counter)+ "/"+ str(total_cases))
            try:
                current_id_params = dict({})

                # replacing path parameters
                if re.search(self.path_params_match_regex, replace_server_url):
                    assert "PathParams" in self.api_json or id_params_dict is not None, "reference needed to " \
                                                                                         "manipulate" \
                                                                                         " id params!"
                    if id_params_dict:
                        itr_dict = random.choice(id_params_dict)
                        for key in itr_dict:
                            query = r"\{" + str(key) + r"\}"
                            value = itr_dict[key]
                            current_id_params[key] = value
                            replace_server_url = re.sub(query, str(value), replace_server_url)
                    else:
                        itr = self.api_json["PathParams"]
                        for key in itr:
                            query = r"\{" + str(key) + r"\}"
                            value = random.choice(list(itr[key]))
                            current_id_params[key] = value
                            replace_server_url = re.sub(query, str(value), replace_server_url)
                self.log.info("sending request...")
                self.log.info("request url: " + self.api_json["type"].upper() + " " + replace_server_url)

                # sending request
                resp = req.request(method=self.api_json["type"], url=replace_server_url, headers=req_headers)

                # checking if response if ok or not
                if resp.ok:
                    self.log.info("status code : " + resp.status_code)
                    self.print_pretty_json(resp.json())

                    # if schema is there for this status code, it will validate it
                    if "resolvedSchema" in self.api_json["responses"][str(resp.status_code)]:
                        self.log.info("validating response...")
                        try:
                            validate(instance=resp.json(),
                                     schema=self.api_json["responses"][str(resp.status_code)]["resolvedSchema"])
                            self.log.info("response schema validated...")
                            if id_params_path:
                                current_id_params_path = dict({})
                                for key in id_params_path:
                                    id_param_value = self.get_id_param(dict(resp.json()), id_params_path[key])
                                    current_id_params_path[key] = id_param_value
                                    self.id_params_path.append(current_id_params_path)
                        except Exception as e:
                            self.log.info("validation failed...")
                            self.failed_cases.append(counter)

                    # validate it from api if required
                    try:
                        self.validate_resp(None, dict(resp.json()), auth_token, current_id_params)
                    except Exception as e:
                        self.log.info("Exception : " + str(e))
                        self.log.info("validation failed from api...")
                        self.failed_cases.append(counter)
                else:
                    self.log.info("status code : " + str(resp.status_code))
                    self.print_pretty_json(resp.json())
                    self.failed_cases.append(counter)
            except Exception as e:
                self.log.info("Exception : " + str(e))
                self.failed_cases.append(counter)
            finally:
                self.log.info("test case over....")
                self.log.info("_______________________________________________________________________")

            # self.log.infoing the summary at the end
            self.print_summary(total_cases, self.failed_cases)

        # if we have fetched any parameteres we want to return it to entity
        if id_params_path:
            return self.id_params_path

    def print_summary(self, total_cases, failed_cases):
        """

        => self.log.infos the summary of test.

        """

        passed_cases = total_cases - len(failed_cases)
        self.log.info("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.log.info("________________________________________________________________________")

        self.log.info("total cases : " + str(total_cases)+ "\n")

        self.log.info("passed cases : " + str(passed_cases))
        self.log.info("failed cases : " + str(len(failed_cases)))
        if len(failed_cases) > 0:
            self.log.info(failed_cases)

        self.log.info("________________________________________________________________________")
        self.log.info("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    def print_pretty_json(self, json_data):
        """

        => this method self.log.info json or dictionary in prettier way.

        """

        if isinstance(json_data, str):
            dict_data = json.loads(json_data)
            self.log.info(json.dumps(dict_data, indent=4))
        else:
            self.log.info(json.dumps(json_data, indent=4))

    def validate_resp(self, payload, resp, auth_token, id_params_dict=None):
        """

        => this method validates the api correspondes to its validation api only if it is present in dependency file.

        => for post it get the mapped valuee from response and for put it uses the current one.

        => for other type of request it just returns None.

        """

        if "validationAPI" in self.api_json:
            if self.api_json["type"].upper() == "POST":
                if self.api_json.get("idParams"):
                    id_params_validation = dict({})
                    for key in self.api_json["idParams"]:
                        id_params_validation[key] = self.get_id_param(resp, self.api_json["idParams"][key])
                else:
                    id_params_validation = None
                if "validationMapping" in self.api_json:
                    validation_mapping = self.api_json["validationMapping"]
                else:
                    validation_mapping = None
                self.match_params(payload,
                                  auth_token,
                                  self.api_json["validationAPI"].split()[-1],
                                  id_params_validation,
                                  validation_mapping)
            elif self.api_json["type"].upper() == "PUT":
                if "validationMapping" in self.api_json:
                    validation_mapping = self.api_json["validationMapping"]
                else:
                    validation_mapping = None
                self.log.info(json.dumps(id_params_dict, indent=4))
                self.match_params(payload,
                                  auth_token,
                                  self.api_json["validationAPI"].split()[-1],
                                  id_params_dict,
                                  validation_mapping)
            else:
                return None
        else:
            return None

    def match_params(self, payload, auth_token, path, id_params_dict=None, ref_dict=None):
        """

        => this method send the validation get reuest and check the corresponding mapping by calling sub methods

        """

        server_url = self.server_base_url + path
        req_headers = {
            'connection': 'keep_alive',
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authtoken': auth_token
        }
        if self.api_json.get("validationAPIHeaders"):
            req_headers = {**req_headers, **self.api_json.get("validationAPIHeaders")}
        # searching for path parameters and replacing it
        if re.search(self.path_params_match_regex, server_url):
            assert id_params_dict is not None, "'validationIdParams' is required!"
            for key in id_params_dict:
                query = r"\{" + str(key) + r"\}"
                value = id_params_dict[key]
                server_url = re.sub(query, str(value), server_url)
        self.log.info("validation request : get " + server_url)
        validation_resp = req.get(url=server_url, headers=req_headers)
        self.log.info("status code : "+ str(validation_resp.status_code))
        self.log.info("validating values...")
        self.log.info("response before deserializing : "+ validation_resp.text)
        self.log.info("validation api resp : ")
        self.print_pretty_json(validation_resp.json())
        self.match_params_helper(payload, validation_resp.json(), ref_dict)
        self.log.info("response validated from api...")

    def match_params_helper(self, dict1, dict2, ref_dict, path=""):
        """

        => this method matches the parametes of dict1 with dict2 with the help of ref_dict.

        => ref_dict has all the parameters that path is different in dict1 and dict2

        """

        if not isinstance(dict1, dict) and not isinstance(dict1, list):

            # match direct parameters
            if ref_dict is not None:
                if path in ref_dict:
                    assert dict1 == self.get_value(dict2, ref_dict[path]), "validation failed for " + path
                else:
                    assert dict1 == self.get_value(dict2, path), "validation failed for " + path
            else:
                assert dict1 == self.get_value(dict2, path), "validation failed for " + path
        else:

            # loop through each key of dict1 and match its value with dict2/ref_dict key's value
            for key in dict1:
                if path == "":
                    match_key = key
                else:
                    match_key = path + "." + key
                # if the parameter is there in ignore_validation we will not check it
                if self.api_json.get("ignoreValidation"):
                    if match_key in self.api_json["ignoreValidation"]:
                        continue
                # for dict we will call recursion
                if isinstance(dict1[key], dict):
                    self.match_params_helper(dict1[key], dict2, ref_dict, match_key)

                # for list we need to check whether the item is there in array or not, order doesn't matter.
                # so, it extracts the array from dict2 and check for all element of array
                # in dict1 whether it is in array or not.

                elif isinstance(dict1[key], list):
                    if ref_dict is not None:
                        if match_key in ref_dict:
                            array = self.get_value(dict2, ref_dict[match_key])
                        else:
                            array = self.get_value(dict2, match_key)
                    else:
                        array = self.get_value(dict2, match_key)
                    assert array is not None, "validation failed for " + match_key
                    list_counter = 0
                    for item in dict1[key]:
                        if isinstance(array, dict):
                            self.match_params_helper(item, array, ref_dict, match_key)
                        # check whether key is there in array.
                        else:
                            self.check_item_in_list(item, array, match_key, list_counter, dict2, ref_dict)
                        list_counter += 1

                # else we will validate directly
                else:
                    if ref_dict is not None:
                        if match_key in ref_dict:
                            assert dict1[key] == self.get_value(
                                dict2, ref_dict[match_key]), "validation failed for " + match_key
                        else:
                            assert dict1[key] == self.get_value(dict2, match_key), "validation failed for " + match_key
                    else:
                        assert dict1[key] == self.get_value(dict2, match_key), "validation failed for " + match_key

    def check_item_in_list(self, item, array, path, counter, dict2, ref_dict):
        """

        => this method checks whether given item is present in array or not.

        => array may contain objects that has some value in ref_dict, so for handling that cases we need to check.

        => for other cases we can directly check items.

        """
        # for item is dict we will loop through array and we will validate them
        # using our previous method match_params_helper with modified red_dict.
        path = ''
        if isinstance(item, dict):
            remove_path = ''
            for other_item in array:
                if not isinstance(other_item, dict):
                    continue
                try:
                    modified_ref_dict = copy.deepcopy(ref_dict)
                    for key in ref_dict:
                        if key.startswith(path):
                            remove_path = path + "."
                            modified_ref_dict[key] = modified_ref_dict[key].replace(remove_path, '')
                    self.match_params_helper(item, other_item, modified_ref_dict, path=path)
                    return
                except BaseException:
                    continue
            raise Exception("validation failed for " + path + " and item number(starting from one) : " + str(counter))

        # else we will simply check if item is there in array or not.
        else:
            assert item in array, "validation failed for " + path + \
                " and item number(starting from one) : " + str(counter)

    def get_value(self, dict1, path):
        """

        => it returns the path value from dict1

        """

        # split the keys in array
        path_arr = path.split('.')

        # getting starting tmp_obj
        # this condition is because, the actual key which is a list might be in the main level
        if not path or path=="":
            tmp_obj = dict1
        else:
            tmp_obj = dict1[path_arr[0]]

        for i in range(1, len(path_arr)):

            # if tmp_obj is list we need to loop through each item and then access the next splited key in array
            if isinstance(tmp_obj, list):
                new_tmp_obj = list([])
                for item in tmp_obj:
                    new_tmp_obj.append(item[path_arr[i]])
                tmp_obj = copy.deepcopy(new_tmp_obj)
            else:
                tmp_obj = tmp_obj[path_arr[i]]

        # returns the final value
        return tmp_obj

    def get_api_type(self):

        # returns the type of api
        return self.api_json["type"].upper()

    def get_id_param(self, resp_dict, ref_string):

        # returns id_params from dict with ref_string
        ref_path = ref_string.split('.')
        param_value = resp_dict[ref_path[0]]
        for i in range(1, len(ref_path)):
            if isinstance(param_value, list):
                param_value = param_value[0][ref_path[i]]
            else:
                param_value = param_value[ref_path[i]]
        return param_value
