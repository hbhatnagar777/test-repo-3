"""Service URLs for VMware REST API operations.

SERVICES_DICT:  A python dictionary for holding all the API services endpoints.

get_services(web_service):  updates the SERVICES_DICT with the Vmware API URL

"""


SERVICES_DICT_TEMPLATE = {
    'LOGIN': '{}com/vmware/cis/session',
    'GET_ALL_VMS': '{}vcenter/vm?filter.power_states.1=POWERED_ON',
    'GET_ALL_DATASTORES': '{}vcenter/datastore',
    'GET_ALL_ESX': '{}vcenter/host'
}


def get_services(web_service):
    """Initializes the SERVICES DICT with the web service for APIs.

        Args:
            web_service     (str)   --  web service string for APIs

        Returns:
            dict    -   services dict consisting of all APIs
    """
    services_dict = SERVICES_DICT_TEMPLATE.copy()
    for service in services_dict:
        services_dict[service] = services_dict[service].format(web_service)

    return services_dict
