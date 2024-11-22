"""
    utils file for Dynamics 365
"""
from AutomationUtils import constants
from AutomationUtils.machine import Machine


def create_azure_app(tc_object):
    """
        Method to create an Azure app for running backups
    """
    passwd, user_id = _fetch_login_creds_from_json(tc_inputs=tc_object.tcinputs)
    script_data = {
        "HostName": tc_object.commcell.webconsole_hostname,
        "LoginPassword": passwd,
        "LoginUser": user_id
    }
    machine = Machine()
    # use local controller itself
    _az_app_details = machine.execute_script(script_path=constants.CREATE_D365_AZURE_APP, data=script_data)

    if _az_app_details.exit_code != 0:
        raise Exception("Error in creation Azure App for Automation")
    _process_created_azure_app_info(tc_object, app_details=_az_app_details.formatted_output)
    # need to rn on the local machine


def _fetch_login_creds_from_json(tc_inputs):
    """
        Method to fetch the credentials from the input JSON to create an Azure app
    """
    d365_online_user = tc_inputs.get("TokenAdminUser", tc_inputs.get("GlobalAdmin"))
    d365_online_password = tc_inputs.get("TokenAdminPassword", tc_inputs.get("Password"))
    return d365_online_password, d365_online_user


def _process_created_azure_app_info(tc_object, app_details: str):
    """
        Method to process the app details of the newly created Azure app
    """
    _app_details = app_details.split("\r\n")
    tc_object.log.info("Created Azure App Details are: {}".format(_app_details))
    tc_object.tcinputs["application_id"] = _app_details[0]
    tc_object.tcinputs["application_key_value"] = _app_details[1]
    tc_object.tcinputs["azure_directory_id"] = _app_details[2]

    return _app_details
