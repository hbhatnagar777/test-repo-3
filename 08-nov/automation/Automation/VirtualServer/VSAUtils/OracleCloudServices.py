"""Service URLs for Oracle Cloud REST API operations.

SERVICES_DICT:  A python dictionary for holding all the API services endpoints.

VM_SERVICES_DICT_TEMPLATE:  A python dictionary for holding all the VM services endpoints.

VM_OPERATIONS_DICT_TEMPLATE:    A python dictionary for holding all the VM operation endpoints.

get_services():  updates the SERVICES_DICT with the Oracle Cloud API URL

get_vm_services():  updates the VM_SERVICES_DICT with the Oracle Cloud API URL

get_vm_operation_services():    updates the VM_OPERATION_DICT with the Oracle Cloud API URL

"""


SERVICES_DICT_TEMPLATE = {
    'LOGIN': '{}authenticate/',
    'CONTAINER': '{}account/'
}

VM_SERVICES_DICT_TEMPLATE = {
    'GET_INSTANCES': '{0}instance/{1}/',
    'GET_SECLIST': '{0}seclist/{1}/',
    'GET_SHAPES': '{0}shape/',
    'GET_SSHKEYS': '{0}sshkey/{1}/',
    'GET_IPNETWORKS': '{0}network/v1/ipnetwork/{1}/',
    'GET_STORAGE_ATTACHMENTS': '{0}storage/attachment/{1}/',
    'GET_STORAGE_VOLUME': '{0}storage/volume'
}

VM_OPERATIONS_DICT_TEMPLATE = {
    'START_VM': '/action/start',
    'STOP_VM': '/action/stop',
    'RESTART_VM': '/action/reboot'
}


def get_vm_operation_services(vrm_service, vm_url):
    """
    get the VM services URL

    Args:
        vrm_service     (str)    --  web service string for APIs

        site_url:       (str)    --  URL for Sites from which VM url can be configured

    Returns:
        vm_op_services_dict     (dict)  --  dict with the updated VM operation service URLs

    """

    vm_op_services_dict = VM_OPERATIONS_DICT_TEMPLATE.copy()
    vm_site_url = '{0}{1}'.format(vrm_service, vm_url)
    for service in vm_op_services_dict:
        vm_op_services_dict[service] = vm_op_services_dict[service].format(vm_site_url)

    return vm_op_services_dict


def get_vm_services(endpoint_url, identity_domain):
    """
    get the VM services URL

    Args:
        endpoint_url         (str)   --  web service string for APIs

        identity_domain:     (str)   --  URL for Sites from which VM url can be configured

    Returns:
        vm_services_dict    (dict)  --  dict containing the updated services URL for any VM

    """

    vm_services_dict = VM_SERVICES_DICT_TEMPLATE.copy()
    vm_site_url = endpoint_url
    for service in vm_services_dict:
        vm_services_dict[service] = vm_services_dict[service].format(vm_site_url, identity_domain)

    return vm_services_dict


def get_services(endpoint_url):
    """Initializes the SERVICES DICT with the web service for APIs.

        Args:
            endpoint_url     (str)   --  web service string for APIs

        Returns:
            services_dict   (dict)  --  services dict consisting of all APIs

    """
    services_dict = SERVICES_DICT_TEMPLATE.copy()
    vrm_service_url = endpoint_url
    for service in services_dict:
        services_dict[service] = services_dict[service].format(vrm_service_url)

    return services_dict
