from enum import Enum
import urllib.parse

class CREDENTIAL_TYPE(Enum):
    USER_ID_PASSWORD = 1
    CLIENT_ID_SECRET = 2


related_records = {
    "Level 0": 20,
    "Level 1": 10,
    "Level 2": 5,
    "Level 3": 3,
    "Level 4": 2
}

"""Authentication Constants"""
AUTH_AUTHORITY = ""
API_VERSION = "v9.0"

# All instates corresponding to authentication
# Redirect URI for the application
REDIRECT_URI = "http://localhost:5000/getAToken"
# Resource for which the token is requested
RESOURCE = "https://globaldisco.crm.dynamics.com"
# Scope for the token
SCOPE = "user_impersonation"
# token authentication endpoint
GLOBAL_DISCOVERY_ACCESS_URL_DEFAULT = "https://globaldisco.crm.dynamics.com/user_impersonation"

GLOBAL_DISCOVERY_ACCESS_ENDPOINT = ("https://globaldisco.crm.dynamics.com/api/discovery/v2.0/Instances?$select="
                                    "TenantId,Id,UniqueName,Url,FriendlyName,UrlName,ApiUrl")

GLOBAL_DISCOVERY_ACCESS_URL_GCC = "https://globaldisco.crm9.dynamics.com/"
# URL for generating access token for querying global discovery

AUTH_AUTHORITY_USERID_PASSWD = "https://login.microsoftonline.com/common"
# The URL to pass in authentication context, for ADAL authentication, if user id and password are supplied

AUTH_AUTHORITY_ENDPOINT = "https://login.microsoftonline.com/%s"
#   The URL to pass in authentication context, for ADAL authentication, if connection attempt is made using App
#   Argument: %s: Tenet ID

"""Error Messages"""
ACCESSIBILITY_ERROR_MESSAGE = 'The user is not a member of the organization.'
ACCESSIBILITY_ERROR_CODE = '0x80072560'

"""Endpoints"""
# all the URLs for CRUD operations

ORG_WEB_API_URL = f"%s/api/data/{API_VERSION}"
"Get the API URL for the Organization"

GLOBAL_DISCOVERY_RESOURCE_URL_DEFAULT = "https://globaldisco.crm.dynamics.com/api/discovery/v2.0/Instances"

GLOBAL_DISCOVERY_RESOURCE_URL_GCC = "https://globaldisco.crm9.dynamics.com/api/discovery/v2.0/Instances"
"""URL to discover the environments in the organization"""

ENVIRONMENT_WHO_AM_I_ENDPOINT = "%s/api/data/v9.0/WhoAmI"
"""URL to get instance accessibility status"""

"""Environment Endpoints"""
GET_ENTITIES_WITH_CHANGE_TRACKING = '%s/api/data/v9.1/EntityDefinitions?$filter=IsIntersect%20eq%20false%20and' \
                                    '%20ChangeTrackingEnabled%20eq%20true '
"""Get the entities for a Dynamics 365 Environment with Change Tracking enabled"""

GET_ENTITIES = '%s/api/data/v9.1/EntityDefinitions'
"""Get the entities in an Dynamics 365 ENVIRONMENT"""

CREATE_RELATIONSHIP = '%s/api/data/v9.2/RelationshipDefinitions'

GET_ENVIRONMENT_PROP = f"/api/data/v9.2/{urllib.parse.quote(
    "RetrieveCurrentOrganization(AccessType=Microsoft.Dynamics.CRM.EndpointAccessType'Default')")}"
"""Get the properties for a Dynamics 365 Environment"""

GET_ENVIRONMENT_PROP_USERID_PASS_DEFAULT = "https://globaldisco.crm.dynamics.com/api/discovery/v2.0/Instances?$filter" \
                                           "=FriendlyName eq '%s' "

GET_ENVIRONMENT_PROP_USERID_PASS_GCC = "https://globaldisco.crm9.dynamics.com/api/discovery/v2.0/Instances?$filter" \
                                       "=FriendlyName eq '%s' "
"""Get the properties for a Dynamics 365 Environment when the access credential type is User ID and Password"""

GET_ENVIRONMENT_ENTITIES = "%s/api/data/v9.2/EntityDefinitions"
"""Get all the entities in the environment"""

GET_ENVIRONMENT_ENTITIES_WITH_CHANGE_TRACKING_ENABLED = "%s?$filter=ChangeTrackingEnabled eq true"
"""Get the entities which have change tracking enabled"""

"""Table/ Entity Endpoints"""

GET_ENTITY_METADATA = "%s//api/data/v9.2/EntityDefinitions(LogicalName='%s')"
"""Get metadata for one particular Entity"""

GET_ALL_RECORDS_FOR_ENTITY = "%s/api/data/v9.2/%s"
"""Get all the records in an Entity/ Table"""

GET_INDIVIDUAL_ENTITY_RECORD = "%s/api/data/v9.2/%s(%s)"
"""Get one individual record from a table"""

CURRENT_SIGNED_IN_USER_INFO = "%s/WhoAmI()"
"""Get the user info for the user account accessing the Dynamics 365 CRM environment"""

ENTITY_ATTRIBUTES_NAME = "%s/EntityDefinitions(LogicalName='%s')/Attributes?$select=LogicalName"
"""Get the Logical Name of all attributes for an entity"""

ENTITY_ATTRIBUTE_METADATA = "%s/EntityDefinitions(LogicalName='%S')/Attributes(LogicalName='%S')"
"""Get the Metadata for a particular attribute belonging to an entity
    Parameters, in order are:
        API URL, Entity Name and Logical Name of the Attribute                                   
"""

"""Record Level Endpoints"""
RECORD_MODIFY_DELETE = "%s/api/data/v9.2/%s(%s)"
"""Delete record from a table endpoint
    Args: environment API URL, Table logical collection name, record id"""

CREATE_RECORD = "%s/api/data/v9.2/%s"
"""Create a record in a table
    Args: environment API URL, Table collection name"""

"""Attribute Endpoints"""
ATTRIBUTE_METADATA = "%s/EntityDefinitions(LogicalName='%s')/Attributes(LogicalName='%s')"
"""Sample Value: EntityDefinitions(LogicalName='contact')/Attributes(LogicalName='emailaddress1')"""

"""Picklist Option Set"""
PICKLIST_OPTION_SET = "/EntityDefinitions(LogicalName='%S')/Attributes(LogicalName='%S')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$select=LogicalName&$expand=OptionSet"
"""Sample Value: {{WebAPIUrl}}/EntityDefinitions(LogicalName='account')/Attributes(LogicalName='accountcategorycode')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$select=LogicalName&$expand=OptionSet"""

"""StatusAttributeMetadata"""
GET_OPTION_SET_VALUE = "/EntityDefinitions(LogicalName='%s')/Attributes(LogicalName='%s')/%s?$select=LogicalName&$expand=OptionSet"
"""Sample Value: /EntityDefinitions(LogicalName='account')/Attributes(LogicalName='statuscode')/Microsoft.Dynamics.CRM.StatusAttributeMetadata?$select=LogicalName&$expand=OptionSet"""

USERS = {
    'CREATE_USER': {

        'url': "https://graph.microsoft.com/v1.0/users",

        'data': '{{'
                '"accountEnabled": true,'
                '"displayName": "{name}",'
                '"mailNickname": "{nick_name}",'
                '"userPrincipalName": "{email}",'
                '"passwordProfile": {{ '
                '"forceChangePasswordNextSignIn": false,'
                '"password": "{pwd}" '
                '}},'
                '"usageLocation": "US"'
                '}}'
    },

    "GET_USER": {'url': "https://graph.microsoft.com/v1.0/users/{user_principal_name}"},

    "ASSIGN_LICENSE": {

        'url': "https://graph.microsoft.com/v1.0/users/{user_id}/assignLicense",

        'data': '{{'
                '"addLicenses" : {add_license},'
                '"removeLicenses": [{remove_licenses_id}]'
                '}}'
    },

    "DELETE_USER": {'url': "https://graph.microsoft.com/v1.0/users/{user_id}"}
}