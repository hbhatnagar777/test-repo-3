# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing string formatting and executing DB queries.

        Only **admin** user can perform below operations


format_string()     --      Formats the provided string and returns the actual required string

execute_query()     --      Executes the requested COMMSERV/WFENGINE query on server and returns
the query result


"""

import base64


def _process_output(output):
    """Validate the response received

        Args:
            output     --     response received from the request

        Returns:
            (str)    -    processed output

        Raises:
            Exception:
                if invalid request was made

                if user doesn't have admin rights

                if failed to process request

    """
    if output == '-1':
        raise Exception("Invalid request")

    elif output == '1':
        raise Exception("User: {0} doesn't have rights to perform this operation")

    elif output.startswith('-2'):
        raise Exception("Failed to process request with error: " + output.lstrip('-2'))

    try:
        return base64.b64decode(output).decode('utf-8')
    except base64.binascii.Error:
        return output


def _process_request(commcell, workflow_name, request_json):
    """Process the request to be sent to the server.

        Args:
            commcell        (object)    --  commcell object for connection to the CommServ

            workflow_name   (str)       --  name of the workflow to execute

            request_json    (str)       --  JSON body for the POST HTTP request to the server

        Returns:
            str     -   formatted response from server

        Raises:
            Exception:
                if response was not success

                if response received is empty

                if failed to get response

    """
    url = '{0}wapi/{1}'.format(commcell._web_service, workflow_name)
    flag, response = commcell._cvpysdk_object.make_request('POST', url, request_json)

    if flag:
        if response.json():
            if 'output' in response.json():
                return _process_output(response.json()['output'])
            elif "errorCode" in response.json():
                if response.json()['errorCode'] != 0:
                    o_str = (
                        'Executing Workflow failed\n'
                        'Error Code: "{0}"\n'
                        'Error Message: "{1}"'
                    ).format(response.json()['errorCode'], response.json()['errorMessage'])

                    raise Exception(o_str)
            else:
                response.raise_for_status()
        else:
            raise Exception("Response received is empty")
    else:
        raise Exception("Response was not success")


def format_string(commcell, input_string):
    """Returns the formatted DB String

        Args:
            commcell    (object)     --     commcell object on which the operations are
                                                to be performed

            input_string    (str)   --  input string which is to be formatted

        Returns:
            (str) 	 - 	formatted string

    """
    request_json = {
        'inputString': input_string,
        'user': commcell._user
    }

    return _process_request(commcell, 'Format String', request_json)


def execute_query(commcell, db_name, query):
    """Executes the DB query and returns the output

        Args:
            commcell    (object)     --     commcell object on which the operations are
                                                to be performed

            db_name     (str)       --  database name on which the query is to be executed

            query       (str)       --  query to be executed

        Returns:
            (list)     - containing table details
    """
    if str(db_name).upper() not in ['COMMSERV', 'WFENGINE']:
        raise Exception("Executing query on {0} database is not supported".format(db_name))

    request_json = {
        "dbName": db_name,
        "query": query,
        "user": commcell._user
    }

    result_set = _process_request(commcell, 'Execute Query', request_json)

    result_set = result_set.split('\n')

    result = []

    for row in result_set:
        result.append(row.split('##!Sep##'))

    return result
