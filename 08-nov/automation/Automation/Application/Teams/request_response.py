# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import requests
import json
import time
from Application.Teams.token import Token

source_token = Token()

cross_tenant_token = Token(True)


def get_token(cross_tenant_details, delegated):
    """ To get the token for the respective tenant.
        Args:
            cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
            delegated   (bool)  -- Whether the API call is delegated or not
    """
    if cross_tenant_details:
        if delegated:
            if not cross_tenant_token.delegated_token:
                cross_tenant_token.delegated_token = cross_tenant_token._generate_delegated_token(cross_tenant_details)
            return cross_tenant_token.delegated_token
        else:
            if not cross_tenant_token.token:
                cross_tenant_token.token = cross_tenant_token._generate_token(cross_tenant_details)
            return cross_tenant_token.token
    else:
        if delegated:
            return source_token.delegated_token
        else:
            return source_token.token


def prepare_request(request_type):
    """To be used for MS GRAPH API calls ONLY.
        Args:
            request_type    --  Request to be made.

    """

    def wrapper(*args, **kwargs):
        """Wrapper method for executing request.
            Args:
                \\*\\*kwargs  (dict)  --  Optional arguments.
                    Available kwargs Options:
                        url             (str)   --  URL or API to call.
                        delegated       (bool)  --  If true, will use delegated token.
                        content_type    (str)   --  Value of Content-Type in header.
                        data            (dict)  --  data also known as payload for the request.

            Returns:
                tuple   (bool, obj)   --  bool, True if request was successful, False otherwise and Response object.

            Raises:
                N/A

        """
        tmp_token = get_token(kwargs.get("cross_tenant_details"), kwargs.get("delegated"))

        args = {
            'url': args[0] if len(args) else kwargs['url'],
            'headers': {
                'Authorization': f'Bearer {tmp_token}',
                'Content-Type': kwargs.get('content_type', 'application/json')
            }
        }

        if kwargs.get('data', False):
            args['data'] = json.dumps(kwargs['data']) if not isinstance(kwargs['data'], bytes) else kwargs['data']

        for i in range(3):
            time.sleep(10)
            response = request_type()(**args)
            if response.status_code in [400, 401]:
                if kwargs.get("cross_tenant_details"):
                    cross_tenant_token.refresh(kwargs.get("cross_tenant_details"))
                else:
                    source_token.refresh()
                tmp_token = get_token(kwargs.get("cross_tenant_details"), kwargs.get("delegated"))
                args['headers'][
                    'Authorization'] = f'Bearer {tmp_token}'
                continue
            break
        return (True, response) if response.status_code == kwargs.get('status_code', 200) else (False, response)

    return wrapper


@prepare_request
def get_request():
    """Get request."""
    return requests.get


@prepare_request
def post_request():
    """Post request."""
    return requests.post


@prepare_request
def put_request():
    """Put request."""
    return requests.put


@prepare_request
def patch_request():
    """Patch request."""
    return requests.patch


@prepare_request
def delete_request():
    """Delete request."""
    return requests.delete
