# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Main Module for invoking MSFT Graph API's pertaining to an Exchange Client

    EXMBGraphAuth:  Graph Authentication Object for an Azure app

    CVEXMBGraphOps: Performing MS Graph operations pertaining to Exchange Mailbox client
"""
import json
import time
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError
from Application.Exchange.ExchangeMailbox import constants
from Application.Office365.o365_data_gen import O365DataGenerator
from requests.exceptions import ConnectionError, ChunkedEncodingError


class EXMBGraphAuth:
    """Class for authenticating Microsoft Graph API via application id and secret key."""

    def __init__(self, ex_object):
        """Initializes the Exchange Authentication object with given application id and secret key.

                Args:

                    ex_object (object)  --   instance of Exchange Mailbox class

                Returns:

                    object  -   instance of EXMBGraphAuth class

        """

        self.log = ex_object.log
        self.__application_id = None
        self.api_name = self.__class__.__name__
        self.client_id = ex_object.azure_app_id
        self.client_secret = ex_object.azure_app_key_secret
        self.tenant_id = ex_object.azure_tenant_name
        self.auth_token_url = constants.MS_AUTH_TOKEN_URL % self.tenant_id
        self.scope = constants.EXMB_SCOPE
        self.oauth = None
        self.token = None

    def __repr__(self):
        """Representation string for the instance of the EXMBGraphAuth class."""

        return 'MS Graph Authentication class instance for Azure app ID: %s', self.client_id

    def authenticate_client(self):
        """This method authenticates the Exchange specific Azure Application for MS Graph APIs."""

        try:
            self.log.info('Authenticating the Azure App via the BackendApplicationClient')
            client = BackendApplicationClient(client_id=self.client_id)
            self.oauth = OAuth2Session(client=client)
            self.token = self.oauth.fetch_token(
                token_url=self.auth_token_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scope=self.scope,
                include_client_id=True)
            self.token = self.token.get('access_token')
            self.log.info('Access token fetched from MS Graph')
        except Exception as excp:
            self.log.exception('Error occurred during Graph authentication')
            raise Exception(self.api_name, str(excp))


class CVEXMBGraphOps:
    """
        Class for performing Graph API operations
    """

    def __init__(self, ex_object):
        """Initializes the CVEXMBGraphOps object.

                Args:

                    ex_object  (Object)  --  instance of exchange mailbox object


                Returns:

                    object  --  instance of CVEXMBGraphOps class

        """

        self.tc_object = ex_object.tc_object
        self.log = self.tc_object.log
        self.api_name = self.__class__.__name__
        self.auth_object = EXMBGraphAuth(ex_object)
        self.auth_object.authenticate_client()
        self.headers = {
            'Content-Type': 'application/json',
            'Host': 'graph.microsoft.com',
            'ConsistencyLevel': 'eventual'
        }

    def request(self, url=None, method: str = 'GET', data=None, headers=None):
        """Method to make a request to Graph URL via OAUTH request method

                Args:

                    url (str)       --  API Endpoint to make request to

                    method (str)    --  API call method
                        Valid Values:
                            GET
                            POST
                            PUT
                            DELETE
                            PATCH

                    data (dict)     --  Data to be sent with POST/PUT requests

                    headers (dict)  --  Request headers.
                        Default Value:

                            self._headers

                    Access token is automatically appended by
                    OAuth2Session class request method used in this module.

        """

        try:
            if not self.auth_object.oauth.authorized:
                self.auth_object.authenticate_client()

            time_out = 0

            while time_out <= 3:

                try:
                    if method in ['GET', 'DELETE']:
                        resp = self.auth_object.oauth.request(
                            method=method, url=url, headers=headers)
                    elif method in ['POST', 'PUT', 'PATCH']:
                        self.log.info('This is a %s method', method)
                        self.log.info('data: %s', data)
                        resp = self.auth_object.oauth.request(
                            method=method, url=url, data=data, headers=headers)

                    else:
                        self.log.error('Method %s not supported', method)
                        raise Exception("Method %s not supported {}".format(method))
                    self.log.info('status code: %s', resp.status_code)
                    if not resp.ok:
                        self.log.error('error: %s', resp.json())
                        resp.raise_for_status()
                    else:
                        self.log.info('Got success response code: %s', resp.status_code)
                        try:
                            return resp.json()
                        except Exception:
                            return resp
                except HTTPError as http_excp:
                    # If the error is a rate limit, connection error or backend error,
                    # wait and try again.
                    time_out += 1
                    self.log.error('Encountered HTTP Error: {0}'.format(http_excp))
                    # Handle the error accordingly [400, 404, 429, 500, 503]

                    if resp.status_code == 401:
                        self.log.error('Request unauthorized.Trying to authenticate client..')
                        self.auth_object.authenticate_client()
                        continue
                    if resp.status_code == 404 and method == 'DELETE':
                        self.log.info('Item not found on MS Graph')
                        break
                    elif resp.status_code == 429:
                        self.log.info(
                            'Got throttled from MS server. '
                            'Waiting for few seconds before trying again')
                        time.sleep(time_out * 10)
                        # This is backend error from MS Graph, so we need to retry after waiting
                        continue
                    elif resp.status_code == 500:
                        self.log.info(
                            'This is internal server error from MS Graph. '
                            'Waiting for few seconds before trying again')
                        time.sleep(time_out * 10)
                        # This is backend error from MS Graph, so we need to retry after waiting
                        continue
                    elif resp.status_code == 501:
                        self.log.info('The requested feature isn’t implemented.')
                        raise
                    elif resp.status_code == 503:
                        self.log.info(
                            'Service unavailable currently. '
                            'Waiting as per Retry-After header and try again.')
                        t_value = resp.headers.get('Retry-After')
                        time.sleep(t_value)
                        continue
                    elif resp.status_code == 504:
                        self.log.info('Gateway timeout error. Retry after sometime.')
                        time.sleep(time_out * 10)
                        # This is backend error from MS Graph, so we need to retry after waiting
                        continue
                    elif resp.status_code == 507:
                        self.log.info(
                            'Insufficient Storage. The maximum storage quota has been reached.')
                        raise
                    elif resp.status_code == 509:
                        self.log.info('Bandwidth Limit Exceeded')
                        raise
                except TokenExpiredError:
                    self.log.warning('Token expired. fetching a new token and trying again.')
                    self.auth_object.authenticate_client()
                    continue
                except ConnectionError as exp:
                    time_out += 1
                    self.log.info(f"Connection Error \n Tried {time_out + 1} times out of 3. Retrying....")
                    self.log.error(f"{exp}")
                    time.sleep(45)

            if time_out > 3:
                self.log.error('Maximum retries for Graph request exceeded.')
                raise Exception("Maximum retries for Graph request exceeded.")
        except Exception as excp:
            self.log.exception('Exception while processing graph response.')
            raise Exception("Exception while processing graph response with exception: {}".format(excp))

    def _check_if_group_exists_on_aad(self, group_name: str):
        """
            Method to check if a particular group exists on the AzureAD

        Args:
            group_name        (str):        Name of the group

        Raises
            Exception           :           Exception, if any, while Checking the presence of the group on AAD.
        """
        group_endpoint = "{}{}?$filter=displayName eq '{}'&$count".format(constants.MS_GRAPH_ENDPOINT,
                                                                          constants.MS_GRAPH_GROUPS_ENDPOINT,
                                                                          group_name)
        self.log.info('Checking whether the group: {} exists on Azure AD'.format(group_endpoint))
        response = self.request(url=group_endpoint,
                                method='GET',
                                headers=self.headers)
        self.log.info('Response for check if group exists: %s', response)
        try:
            group = response["value"]
            return False if len(group) == 0 else True
        except Exception as excp:
            self.log.exception("Error in checking if a group exists on Azure AD: {}".format(excp))
            raise Exception("Exception raised while checking if a group exists on Azure AD:")

    def _get_group_id(self, group_name: str):
        """
            Method to get the ID of any Azure group by its group name

        Args:
            group_name      (str):      Group who's ID is to be fetched

        Returns:
            group_id        (str):      Azure ID of the Group

        Raises
            Exception           :       ID not found on Azure AD,
        """
        group_endpoint = "{}{}?$filter=displayName eq '{}'&$select=id".format(constants.MS_GRAPH_ENDPOINT,
                                                                              constants.MS_GRAPH_GROUPS_ENDPOINT,
                                                                              group_name)
        response = self.request(url=group_endpoint,
                                method='GET',
                                headers=self.headers)
        try:
            group_id = response["value"][0]["id"]
        except KeyError:
            self.log.exception("Group ID not found in the response: {}".format(response))
            raise Exception("Group ID not present in the response")
        return group_id

    def _get_user_id(self, user_upn: str):
        """
            Method to get the Object ID of any Azure user ID by its UPN

        Args:
            user_upn      (str):      Group who's ID is to be fetched

        Returns:
            group_id        (str):      Azure ID of the Group

        Raises
            Exception           :       ID not found on Azure AD,
        """
        user_endpoint = "{}{}?$select=id&$filter=userPrincipalName eq '{}'".format(constants.MS_GRAPH_ENDPOINT,
                                                                                   constants.MS_GRAPH_USERS_ENDPOINT,
                                                                                   user_upn)
        response = self.request(url=user_endpoint,
                                method='GET',
                                headers=self.headers)
        try:
            user_id = response["value"][0]["id"]
        except KeyError:
            self.log.exception("User ID not found in the response: {}".format(response))
            raise Exception("User ID not present in the response")

        return user_id

    def create_group(self, group_name: str, group_type: str = "MS365", mail_nickname: str = str()):
        """
            Creates an Microsoft 365 group on AzureAD.

        Args:
            group_name      (str):          Group to be created

            group_type      (str):          Type of the group to be created
                Supported Types:
                    "MS365"     :           Office 365/ Microsoft 365 type group
                    "Security"  :           Security Group
            mail_nickname   (str):          Mail address to be used for the group
        """
        try:
            self.log.info("Creating Group: {} of Type: {}".format(group_name, group_type))
            group_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                              f'{constants.MS_GRAPH_GROUPS_ENDPOINT}')
            if group_type == "MS365":
                data = constants.MS_NEW_MS365_GROUP
            elif group_type == "Security":
                data = constants.MS_NEW_SECURITY_GROUP
            else:
                self.log.error("Unsupported Group Type: {}".format(group_type))
                raise Exception("Group Type not supported")

            if self._check_if_group_exists_on_aad(group_name=group_name):
                self.delete_azure_ad_group(group_name=group_name)

            if not mail_nickname:
                mail_nickname = group_name
            data['displayName'] = group_name
            data['mailNickname'] = f'{mail_nickname}'
            self.log.info('Group Creation Endpoint:%s', group_endpoint)

            response = self.request(url=group_endpoint,
                                    method='POST',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('Response:%s', response)
            self.log.info(f'Successfully created group: {group_name} with type: {group_type}')
            time.sleep(30)
        except Exception as excp:
            self.log.exception('Exception while creating group')
            raise Exception(self.api_name, '101', str(excp))

    def add_group_members(self, group_name: str, members: list):
        """
            Add members to an Azure AD Group

        Args:
            group_name      (str):      Group name to which members are to be added
            members         (list):     List of members' to be added to the group
                Format/ Expected Value:
                    UPN of the user's

        Raises
            Exception           :       Exception, if any while adding members to the group
        """
        try:
            self.log.info("Adding Members: {} to group: {}".format(members, group_name))
            group_id = self._get_group_id(group_name=group_name)
            group_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                              f'{constants.MS_GRAPH_GROUPS_ENDPOINT}/'
                              f'{group_id}')

            data = dict()
            user_ids = list()
            for member in members:
                user_id = self._get_user_id(user_upn=member)
                user_ids.append(user_id)

            user_id_list = list(
                map(lambda u_id: f"{constants.MS_GRAPH_ENDPOINT}{constants.MS_GRAPH_DIRECTORY_OBJECTS}/{u_id}",
                    user_ids))
            data["members@odata.bind"] = user_id_list

            response = self.request(url=group_endpoint,
                                    method='PATCH',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info(f'Successfully added Members {members} to the Group {group_name}')
            time.sleep(30)
        except Exception as excep:
            raise Exception("Exception while adding members to an Azure AD group: {}".format(excep))

    def delete_azure_ad_user(self, user_upn: str):
        """
            Method to delete a User object from the Azure AD

        Args:
            user_upn        (str):      UPN of the user which is to be deleted from Azure

        Raises
            Exception           :       Exception, if any, while deleting the specified user
        """
        try:
            user_id = self._get_user_id(user_upn=user_upn)
            user_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                             f'{constants.MS_GRAPH_USERS_ENDPOINT}/'
                             f'{user_id}')

            response = self.request(url=user_endpoint, method='DELETE', headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully deleted the User: {user_upn} from Azure')
            time.sleep(30)
        except Exception as excp:
            raise Exception("Exception while deleting the User Object from Azure AD: {}".format(excp))

    def delete_azure_ad_group(self, group_name: str):
        """
            Method to delete a Group object from the Azure AD

        Args:
            group_name        (str):        Name of the group which is to be deleted from Azure

        Raises
            Exception           :           Exception, if any, while deleting the specified AD Group
        """
        try:
            user_id = self._get_group_id(group_name=group_name)
            user_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                             f'{constants.MS_GRAPH_GROUPS_ENDPOINT}/'
                             f'{user_id}')

            response = self.request(url=user_endpoint, method='DELETE', headers=self.headers)
            self.log.info('Response:%s', response)
            self.log.info(f'Successfully deleted the Group: {group_name} from Azure')
            time.sleep(30)
        except Exception as excp:
            raise Exception("Exception while deleting the Group Object from Azure AD: {}".format(excp))

    def update_user_smtp(self, user_upn: str, new_mail_address: str):
        """
            Method to update the Mail address and UPN for an Azure AD user.

            Args:
                user_upn            (str):      UPn of the user who's email address has to be changed
                new_mail_address    (str):      New user name that is to be used

        """
        try:
            users_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                              f'{constants.MS_GRAPH_USERS_ENDPOINT}/'
                              f'{user_upn}')
            data = constants.MS_MODIFY_USER
            data['userPrincipalName'] = f'{new_mail_address}'
            data['mail'] = f'{new_mail_address}'
            self.log.info('Modify SMTP Address Endpoint:%s', users_endpoint)

            response = self.request(url=users_endpoint,
                                    method='PATCH',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully updated User: {user_upn}\'s SMTP Address to: {new_mail_address}')
            time.sleep(30)
        except Exception as excp:
            self.log.exception('Exception while updating user: {}'.format(excp))
            raise Exception("Exception raised while updating the User's SMTP Address")

    def get_all_groups(self):
        """
            Fetches all the groups using the Azure Graph API

            Number of groups on AD being large, the method will return an iterator
            using yield through which we can iterate and fetch all groups

        """
        try:
            self.log.info("Fetching Groups from Azure AD ")
            group_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                              f'{constants.MS_GRAPH_GROUPS_ENDPOINT}')

            self.log.info('Fetch All Groups Endpoint: %s', group_endpoint)

            while group_endpoint:
                response = self.request(url=group_endpoint,
                                        method='GET',
                                        headers=self.headers)
                yield from response.get('value')
                group_endpoint = response.get('@odata.nextLink')
                self.log.info("Fetching next page of groups")

        except Exception as excp:
            self.log.exception('Exception while fetching all groups from AD')
            raise Exception(self.api_name, '101', str(excp))

    def update_user(self, user_upn: str, properrty: str, **kwargs) -> str:
        """
            Update the usage location for the user.
            Arguments:
                user_upn        (str):      Email address of the user to be updated
                properrty       (str):      Property name to be updated for the User
        """
        users_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                          f'{constants.MS_GRAPH_USERS_ENDPOINT}/'
                          f'{user_upn}')
        data = dict()
        if properrty == "LOCATION":
            _new_val = kwargs.get("usageLocation", f'{constants.USAGE_LOCATION_IND}')
            data['usageLocation'] = _new_val
        elif properrty == "DISPLAY-NAME":
            _new_val = kwargs.get("displayName", O365DataGenerator.gen_display_name())
            data['displayName'] = _new_val
        else:
            raise Exception("Property not supported")

        self.log.info('Updating {} Endpoint :%s', properrty, users_endpoint)
        response = self.request(url=users_endpoint,
                                method='PATCH',
                                data=json.dumps(data),
                                headers=self.headers)
        self.log.info('response:%s', response)
        self.log.info(f'Successfully set the {properrty} for User: {user_upn}\'s to: {_new_val}')
        time.sleep(45)
        return _new_val

    def modify_user_license(self, user_upn: str, operation: str, **kwargs):
        """
            Method to modify a License for an Online User
            Arguments:
                user_upn    (str):      UPN of the user
                operation   (str):      Operation to be performed
                    assign:             assign license to the user
                    remove:             remove license from the user
                **kwargs    (dict)      dictionary of key-value arguments
                    Supported value:
                        licenseSKU:     SKU of the License to be used
        """
        users_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                          f'{constants.MS_GRAPH_USERS_ENDPOINT}/'
                          f'{user_upn}/'
                          f'assignLicense')
        data = constants.LICENSE_OP_DICT
        _license_sku = kwargs.get("licenseSKU", constants.MS_TEAMS_EXPLORATORY_SKU)

        if operation == "assign":
            self.update_user(user_upn, properrty="LOCATION")
            _lic_info = {
                "skuId": _license_sku
            }
            data["addLicenses"].append(_lic_info)

        elif operation == "remove":
            data["removeLicenses"].append(_license_sku)

        self.log.info('License Modification Endpoint :%s', users_endpoint)
        response = self.request(url=users_endpoint,
                                method='POST',
                                data=json.dumps(data),
                                headers=self.headers)
        self.log.info('response:%s', response)
        self.log.info(f'Successfully performed: {operation} on license for user: {user_upn}')

    def get_group_members(self, group_name: str):
        """Get group members
            group_name  (str): Name of the group
        """
        _group_id = self._get_group_id(group_name=group_name)
        _group_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                           f'{constants.MS_GRAPH_GROUPS_ENDPOINT}/'
                           f'{_group_id}/'
                           f'members')

        response = self.request(url=_group_endpoint,
                                method='GET',
                                headers=self.headers)
        members = response.get("value")
        return members

    def get_all_users(self):
        """
            Fetch all the users from the AD
        """
        try:
            self.log.info("Fetching all users from Azure AD ")
            users_endpoint = (f'{constants.MS_GRAPH_ENDPOINT}'
                              f'{constants.MS_GRAPH_USERS_ENDPOINT}')

            self.log.info('Fetch All Users Endpoint: %s', users_endpoint)
            while users_endpoint:
                response = self.request(url=users_endpoint,
                                        method='GET',
                                        headers=self.headers)
                yield from response.get('value')
                users_endpoint = response.get('@odata.nextLink')
                self.log.info("Fetching next page of users")
        except Exception as excp:
            self.log.exception('Exception while fetching all users from AD')
            raise Exception(self.api_name, '101', str(excp))

    def get_all_member_users(self):
        """
            Fetch all the users have the userType member from the AD
        """
        try:
            self.log.info("Fetching all users have the userType member from Azure AD ")
            users_endpoint = (f'{constants.MS_GRAPH_BETA_ENDPOINT}'
                                      f'{constants.MS_GRAPH_USERS_ENDPOINT}'+"?$filter=mail ne null and userType eq 'member'&$count=true")

            self.log.info('Fetch All Users Endpoint: %s', users_endpoint)
            while users_endpoint:
                response = self.request(url=users_endpoint,
                                        method='GET',
                                        headers=self.headers)
                yield from response.get('value')
                users_endpoint = response.get('@odata.nextLink')
                self.log.info("Fetching next page of users")
        except Exception as excp:
            self.log.exception('Exception while fetching all users from AD')
            raise Exception(self.api_name, '101', str(excp))
