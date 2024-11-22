# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be used to run
basic operations on identity servers page.

Class:

    SamlHelperMain:

    __init__()                      --Initializes the SAML servers helper module

    _parse_idpMetadata()            -- parse idp metadata xml file and forms idp metadata dict

    _generate_spmetadata()          -- generate sp metadata dict

    _companies_info()               --  gets company id and company name of companies

    _domains_info()                 -- gets domain id and domain name of domains

    _usergroups_info()              -- gets usergroup id and usergroup name of usergroups

    _usergroups_company_info()      -- gets company id and company name of company

    _get_samlapp_domainid()         -- gets saml app domain id from UMDSProviders table

    _get_user_authid()              -- gets auth id of a user

    create_saml_app()				-- Helper method for creating SAML app in admin console

    modify_saml_general_settings()  -- Edit the options present in general tab in SAML app

    validate_saml_general_settings()-- Validates the options present in general tab in SAML app

    modify_attribute_mappings()     -- edits the attribute mapping of saml app

    validate_attribute_mappings()   -- validates attribute mappings in saml app

    modify_idp_metadata()           -- modifies idp metadata of saml app

    modify_sp_metadata()            -- modifies sp metadata of saml app

    validate_sp_and_idp_metadata    -- validates sp and idp metadata of saml app

    modify_associations()           -- modifies associations of a saml app

    validate_associations()         -- validates associations of a saml app

    validate_authid()               -- validates the auth id of a user

    delete_saml_app()				-- Deletes the given SAML app

    is_saml_app_exist()             -- checks if saml app is present in commcell / company

    is_company_saml_app()           -- verifies if saml app is created for a company

    validate_samluser_properties()	-- validates saml user properties

    samluser_redirect_url()         -- get redirect url of user via api

    samlapp_redirect_url()          -- get redirect url of saml app from db

SamlHelperMain instance Attributes
============================

    **spmetadata**                  --  returns spmetadata as a dict

"""
import xml.etree.ElementTree as et
from AutomationUtils import logger
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.options_selector import OptionsSelector


class SamlHelperMain:
    """Helper class for SAMl operations"""

    def __init__(self, commcell, appname=None):
        """Initialize object of SAMLHelperMain class.

            Args:
                commcell    (object)    --  instance of the Commcell class
                appname     (string)    --  saml app name
                            Default value : None

            Returns:
                object - instance of SAMLHelperMain class
        """
        self._commcell = commcell
        self.log = logger.get_log()
        self.csdb = CommServDatabase(commcell)
        self.utility = OptionsSelector(commcell)
        self._appname = None
        self._samlapp = None
        self._samlapp_domainId = None
        self._samlapp_redirect_url = None
        if appname:
            self._appname = appname
            self._samlapp = self._commcell.identity_management.get_saml(appname)

    def _parse_idpMetadata(self, file_path):
        """Parse Idp metadata and forms a dict with required values
            Args:
                file_path       (string)       metadata file path

            Returns:
                                (dict) ex      idp_metadata = {
                                                    'entityId': string,
                                                    'SAMLProtocolVersion': string,
                                                    'certificateData': string,
                                                    'redirectUrl': string,
                                                    'logoutUrl': string
                                                }
        """
        tree = et.parse(file_path)
        root = tree.getroot()

        idp_metadata = {
            'entityId': root.attrib['entityID'],
            'SAMLProtocolVersion': root.tag.split('}')[0].strip('{')
        }
        idpsso = None
        for child in root.iter():
            if 'IDPSSODescriptor' in child.tag:
                idpsso = child
                break

        for Child in idpsso.iter():
            if Child.get('use') == 'signing':
                for child in Child.iter():
                    if 'Certificate' in child.tag:
                        idp_metadata['certificateData'] = child.text
            elif 'SingleSignOnService' in Child.tag:
                idp_metadata['redirectUrl'] = Child.get('Location')
            elif 'SingleLogoutService' in Child.tag:
                idp_metadata['logoutUrl'] = Child.get('Location')

        return idp_metadata

    def _generate_spmetadata(self, auto_generate_sp_metadata, entity_id=None):
        """Generate SP Metadata in required dict format
            Args:
                auto_generate_sp_metadata    (bool)      True for auto generation of certificates
                entity_id                    (string)   new sp entity id

            Returns:
                dict        sp_metadata = {
                                'serviceProviderEndpoint': string,
                                'autoGenerateSPMetaData': string,
                                'jksFileContents': []
                            }
        """
        if entity_id:
            webconsole_url = entity_id
        else:
            webconsole_url = 'https://' + self._commcell.webconsole_hostname + ':443/identity'

        sp_metadata = {
            'serviceProviderEndpoint': webconsole_url,
            'autoGenerateSPMetaData': auto_generate_sp_metadata
        }
        if auto_generate_sp_metadata:
            sp_metadata['jksFileContents'] = []

        return sp_metadata

    def _companies_info(self, companies):
        """Get company id  of a company
            Args:   companies       (list)      list of company names

            Returns:
            company id and company name of given company names
                                (list)      ex  company_info = [
                                                    { 'id': string, 'name': string}
                                                ]
        """
        company_info = []
        for company in companies:
            company_obj = self._commcell.organizations.get(company)
            company_info.append({'id': company_obj.organization_id, 'name': company_obj.organization_name})
        return company_info

    def _domains_info(self, domains):
        """Get domain id of a domain
            Args:   domains       (list)      list of domain names

            Returns:
            domain id and domain name of given domains
                                (list)      ex  domain_info = [
                                                    { 'id': string, 'name': string}
                                                ]
        """
        domain_info = []
        for domain in domains:
            domain_obj = self._commcell.domains.get(domain)
            domain_info.append({'id': domain_obj.domain_id, 'name': domain_obj.domain_name})
        return domain_info

    def _usergroups_info(self, usergroups):
        """Get usergroup id of given usergroup names
            Args:   usergroups       (list)      list of usergroups

            Returns:
            usergroup id and usergroup name of given user groups
                                (list)      ex  usergroup_info = [
                                                    { 'id': string, 'name': string}
                                                ]
        """
        usergroup_info = []
        for grp in usergroups:
            grp_ob = self._commcell.user_groups.get(grp)
            usergroup_info.append({'id': grp_ob.user_group_id, 'name': grp_ob.user_group_name})
        return usergroup_info

    def _usergroups_company_info(self, usergroups):
        """Get usergroup company id and usergroup company name

        Args:   usergroups      (list)          list of usergroup names

        Returns:
         company id and company name of given user groups
                                (list)      ex  company_info = [
                                                    { 'id': string, 'name': string}
                                                ]
        """
        company_info = []
        for grp in usergroups:
            grp_obj = self._commcell.user_groups.get(grp)
            company_name = grp_obj.company_name
            company_id = grp_obj.company_id
            if company_name == '':
                company_name = 'Commcell'
            company_info.append({'id': company_id, 'name': company_name})
        return company_info

    def _get_samlapp_domainid(self):
        """
        Get id of saml app domain from UMDSProviders table

        Returns                     (string)       saml app domain id
        """
        if not self._samlapp_domainId:
            self.log.info('Fetching saml app domain id')
            query = """select componentId from APP_ComponentProp where longVal in (select id from App_ThirdPartyApp 
                    where appname = '{0}')""".format(self._appname)
            self.csdb.execute(query)
            self.log.info('saml app domain id fetched successfully')
            self._samlapp_domainId = self.csdb.fetch_one_row()[0]

        return self._samlapp_domainId

    def _get_user_authid(self, user_email):
        """ Get auth id of user
            Args:
                 user_email         (string)        user email

            Returns:
                                    (string)        auth id of user
        """
        self.log.info('Fetching auth id for {0} from database'.format(user_email))
        query = """select attrVal from UMUsersProp where attrName = 'AuthenticatorId' and componentNameId in 
                (select id from umusers where login not like '%deleted%' and 
                (email = '{0}' or upn = '{0}'))""".format(user_email)
        self.csdb.execute(query)
        self.log.info('auth id fetched successfully')
        return self.csdb.fetch_one_row()[0]

    def create_saml_app(self, appname, description, idpmetadata_xml_path,
                        auto_generate_sp_metadata=True, email_suffixes=None, companies=None,
                        domains=None, usergroups=None):

        """
        Creates a saml app
        Args :
            appname                 (string)   saml app name
            description             (string)  saml app description
            idpmetadata_xml_path    (string)   path of idp metadata xml file
            auto_generate_sp_metadata(bool)    True for automatic generation of certificates
            email_suffixes          (list)    list of email suffixes to be associated
            companies               (list)    list of company names to be associated
            domains                 (list)    list of domain names to be associated
            usergroups              (list)    list of usergroup names to be associated

        """
        self.log.info('parsing idp metadata')
        idp_metadata = self._parse_idpMetadata(idpmetadata_xml_path)

        self.log.info('generating sp metadata')
        sp_metadata = self._generate_spmetadata(auto_generate_sp_metadata)
        associations = {}
        if email_suffixes is not None:
            self.log.info('Adding email suffixes')
            associations.update({'emailSuffixes': email_suffixes})
        if companies is not None:
            self.log.info('Adding companies')
            associations.update({'companies': self._companies_info(companies)})
        if domains is not None:
            self.log.info('Adding domains')
            associations.update({'domains': self._domains_info(domains)})
        if usergroups is not None:
            self.log.info('Adding usergroups')
            associations.update({'userGroups': self._usergroups_info(usergroups)})

        self._appname = appname.lower()
        self.log.info('Creating Saml app with associations : ')
        self.log.info(associations)
        self._samlapp = self._commcell.identity_management.configure_saml_app(self._appname, description, idp_metadata,
                                                                              sp_metadata, associations)
        self.log.info('saml app [{0}] created successfully'.format(self._appname))

    def modify_saml_general_settings(self, description=None, enabled=None, autocreate=None,
                                     default_usergroups=None, nameid=None):
        """
        Modifies general settings of saml app
        Args :
            description         (string)        saml app description
            enabled             (bool)          enabled flag : True for enabing the saml app
            autoCreateUser      (bool)          auto create user flag : True for enabling auto create user flag
            default_usergroups  (list)          list of default user groups of saml app
            nameid              (string)        NameId attribute value either Email or User Principal Name
        """

        req_body = {}
        if description:
            req_body.update({'description': description})

        if enabled is not None:
            req_body.update({'enabled': enabled})

        if autocreate is not None:
            req_body.update({'autoCreateUser': autocreate})

        if nameid:
            req_body.update({'nameIDAttribute': nameid})

        if default_usergroups:
            company_info = self._usergroups_company_info(default_usergroups)
            usergroup_info = self._usergroups_info(default_usergroups)

            default_groups = []
            for idx in range(len(default_usergroups)):
                temp = {
                    'companyInfo': {
                        'id': company_info[idx]['id'],
                        'name': company_info[idx]['name']
                    },
                    'userGroupInfo': {
                        'id': usergroup_info[idx]['id'],
                        'name': usergroup_info[idx]['name']
                    }

                }
                default_groups.append(temp)
            req_body.update({'userGroups': default_groups})

        self.log.info('request body for modify saml general settings ')
        self.log.info(req_body)
        self._samlapp.modify_saml_app(req_body)
        self.log.info('general settings modified successfully')

    def validate_saml_general_settings(self, description=None, enabled=None, autocreate=None,
                                       default_usergroups=None, nameid=None):
        """
        Validates general settings of saml app
        Args :
            description         (string)        saml app description
            enabled             (bool)          enabled flag : True for enabing the saml app
            autoCreateUser      (bool)          auto create user flag : True for enabling auto create user flag
            default_usergroups  (list)          list of default user groups of saml app
            nameid              (string)        NameId attribute value either Email or User Principal Name
        """
        failed = ' validation failed'
        if description:
            self.log.info('Validate description ' + '[' + description + ']')
            if self._samlapp.saml_app_description != description:
                self.log.info('description from saml app : ' + self._samlapp.saml_app_description)
                raise Exception(description + failed)
            self.log.info('Valid')

        if enabled is not None:
            self.log.info('Validate enabled flag')
            if self._samlapp.is_saml_app_enabled != enabled:
                raise Exception(f'enabled' + failed)
            self.log.info('Valid')

        if autocreate is not None:
            self.log.info('Validate autocreate user flag')
            if self._samlapp.is_auto_create_user != autocreate:
                raise Exception(f'autocreate' + failed)
            self.log.info('Valid')

        if nameid:
            self.log.info('Validate nameId attribute ' + '[' + nameid + ']')
            if self._samlapp.saml_app_nameid_attribute != nameid:
                self.log.info('NameId from saml app : ' + self._samlapp.saml_app_nameid_attribute)
                raise Exception(nameid + failed)
            self.log.info('Valid')

        if default_usergroups:
            self.log.info('Validate default user groups')
            for grp in default_usergroups:
                if not list(filter(lambda ug: ug['userGroupInfo']['name'].lower() == grp.lower(),
                                   self._samlapp.saml_app_default_user_groups)):
                    self.log.info('Given default user group : ' + grp)
                    self.log.info('Default user groups of saml app : ')
                    all_grps = []
                    for g in self._samlapp.saml_app_default_user_groups:
                        all_grps.append(g['userGroupInfo']['name'])
                    self.log.info(all_grps)
                    raise Exception(grp + failed)
            self.log.info('Valid')

    def modify_attribute_mappings(self, attr_mappings, is_add=True):
        """
        Modifies attribute mappings of saml app
        Args:
            attr_mappings       (dict)          Attr mappings in dict format
                                ex              {
                                                    'Email': 'mail',
                                                    'user groups': 'ug'
                                                }
            is_add              (bool)          True to add given attr mappings
                                                False to remove given attr mappings
        Raises:
              Exception         if is_add is True but any of given mappings is already present in saml app
                                if is_add is False and any of given mappings is not present in saml app
        """
        old_mappings = self._samlapp.saml_app_attribute_mappings
        req_body = {}
        if is_add:
            for key, value in attr_mappings.items():
                self.log.info('Adding ' + key + ' --> ' + value + ' mapping')
                if list(filter(lambda m: m['customAttribute'] == key or m['SAMLAttribute'] == value, old_mappings)):
                    raise Exception(key + ' or ' + value + ' already present in saml app')
                old_mappings.append({'customAttribute': key, 'SAMLAttribute': value})
        else:
            for key, value in attr_mappings.items():
                self.log.info('Removing ' + key + ' --> ' + value + ' mapping')
                if not list(filter(lambda m: m['customAttribute'] == key and m['SAMLAttribute'] == value, old_mappings)):
                    raise Exception(key + ' and ' + value + ' is not present in saml app')
                old_mappings[:] = [d for d in old_mappings if d.get('customAttribute') != key and
                                   d.get('SAMLAttribute') != value]

        req_body.update({'attributeMappings': old_mappings})
        self.log.info('req body for modify attribute mapping')
        self.log.info(req_body)
        self._samlapp.modify_saml_app(req_body)
        self.log.info('modified attribute mappings successfully')

    def validate_attribute_mappings(self, mappings):
        """Validates attribute mappings
            Args:
                mappings        (dict)          dict of custom attr and saml attr
                                        mappings = {
                                            'Email': 'email',
                                            'username': 'un'
                                        }
            Raises:
                Exception if any given mapping is not present in saml app
        """
        old_mappings = self._samlapp.saml_app_attribute_mappings

        for key, value in mappings.items():
            self.log.info('Validate [' + key + ' --> ' + value + '] mapping')
            if not list(filter(lambda m: m['customAttribute'] == key and m['SAMLAttribute'] == value, old_mappings)):
                raise Exception(key + ' ' + value + ' is not present in saml app')
            self.log.info('Valid')

    def modify_idp_metadata(self, idpmetadata_file_path):
        """
        Modifies the idp metadata of saml app
        Args:
            idpmetadata_file_path           (string)        metadata xml file path

        """

        idpmetadata = self._parse_idpMetadata(idpmetadata_file_path)
        req_body = {
            'identityProviderMetaData': idpmetadata
        }
        self.log.info('req_body for for modify idp metadata')
        self.log.info(req_body)
        self._samlapp.modify_saml_app(req_body)
        self.log.info('modified idp metadata successfully')
        self._samlapp_redirect_url = None  # reset this variable as redirect url of saml app has been changed

    def modify_sp_metadata(self, auto_generate_sp_metadata, entity_id):
        """
        Modifies sp metadata of saml app
        Args:
            auto_generate_sp_metadata   (bool)          True for automatic generation of certificates
            entity_id                   (string)        new sp entity id in proper format
                                        ex              https:\\hostname:port\webconsole
        """

        sp_metadata = self._generate_spmetadata(auto_generate_sp_metadata, entity_id)

        req_body = {
            'serviceProviderMetaData': sp_metadata
        }
        self.log.info('req body for modify sp metadata ')
        self.log.info(req_body)
        self._samlapp.modify_saml_app(req_body)
        self.log.info('modified sp metadata successfully')

    def validate_sp_and_idp_metadata(self, spmetadata=None, idpmetadata=None):
        """Validates SP and IDP Metadata of saml app
            Args:
                spmetadata          (dict)      spmetadata = {
                                                    'entityId': string,
                                                    'singleSignOnUrl': string,
                                                    'singleLogoutUrl': string,
                                                    'spAliases': []
                                                }
                idpmetadata         (dict)      idpmetadata = {
                                                    'entityId': string,
                                                    'redirectUrl': string,
                                                    'logoutUrl': string
                                                }
            Raises:
                Exception if spmetadata or idpmetdata does not match with saml app
        """
        if spmetadata:
            sp = self._samlapp.saml_app_service_provider_metadata
            for key in ['entityId', 'singleSignOnUrl', 'singleLogoutUrl']:
                self.log.info('Validate ' + key)
                if key in spmetadata and spmetadata[key] != sp[key]:
                    raise Exception(key + ' of spmetadata does not match with saml app')

            if 'spAliases' in spmetadata:
                for alias in spmetadata['spAliases']:
                    if alias not in sp['spAliases']:
                        raise Exception(alias + ' does not match with saml app')

        if idpmetadata:
            idp = self._samlapp.saml_app_identity_provider_metadata
            for key in ['entityId', 'redirectUrl', 'logoutUrl']:
                self.log.info('Validate ' + key)
                if key in idpmetadata and idpmetadata[key] != idp[key]:
                    raise Exception(key + ' of idpmetadata does not match with saml app')

    def modify_associations(self, entity_type, entity_value, is_add):
        """Modifies saml app associations
            Args:
                entity_type         (string)    type of entity to be modified
                                    ex          'emailSuffixes', 'companies', 'domains', 'userGroups'
                entity_value        (string)    value to entity
                is_add              (bool)      True for adding the association
                                                False to removing the association
            Raise:
                Exception           if is_add is True but given association is already present in saml app
                                    if is_add is False and given associations is not present in saml app
        """
        present = ' already exists'
        absent = ' does not exists'
        associations = self._samlapp.saml_app_associations
        req_body = {}
        if entity_type == 'emailSuffixes':
            old_email = associations[entity_type]
            if is_add:
                if entity_value in old_email:
                    raise Exception('email suffix ' + entity_value + present)
                else:
                    old_email.append(entity_value)
            else:
                if entity_value not in old_email:
                    raise Exception('email suffix ' + entity_value + absent)
                else:
                    old_email.remove(entity_value)

            associations[entity_type] = old_email
            req_body.update({'associations': associations})

        else:
            old_entity = associations[entity_type]
            if entity_type == 'companies':
                entity_info = self._companies_info([entity_value])
            elif entity_type == 'domains':
                entity_info = self._domains_info([entity_value])
            elif entity_type == 'userGroups':
                entity_info = self._usergroups_info([entity_value])

            if is_add:
                if entity_value.lower() in [element['name'].lower() for element in old_entity]:
                    raise Exception(entity_value + present)
                else:
                    old_entity.append(entity_info[0])
            else:
                if entity_value.lower() not in [element['name'].lower() for element in old_entity]:
                    raise Exception(entity_value + absent)
                else:
                    old_entity[:] = [d for d in old_entity if d.get('name').lower() != entity_value.lower()]

            associations[entity_type] = old_entity
            req_body.update({'associations': associations})

        self.log.info('req body for modify associations ')
        self.log.info(req_body)
        self._samlapp.modify_saml_app(req_body)
        self.log.info('successfully modified associations')

    def validate_associations(self,  props):
        """Validates associations of saml app
            Args:
                props               (dict)         saml app associations
                                    ex   props = {
                                            'emailSuffixes': [''],
                                            'companies': [''],
                                            'domains': [''],
                                            'userGroups': ['']
                                        }
            Raise:
                Exception           if any given association is not present in saml app
        """
        associations = self._samlapp.saml_app_associations
        absent = ' not associated to saml app'
        for key, value in props.items():
            if key == 'emailSuffixes':
                for email in value:
                    self.log.info('Validating email suffix [' + email + ']')
                    if email not in associations['emailSuffixes']:
                        self.log.info('email suffixes associated to saml app : ')
                        self.log.info(associations['emailSuffixes'])
                        raise Exception(email + absent)
            else:
                for entity in props[key]:
                    x = []
                    [[x.append(item['name'].lower()) for item in l] for k, l in associations.items()
                     if k != 'emailSuffixes']
                    self.log.info('Validating [' + entity + ']')
                    if entity.lower() not in x:
                        self.log.info('All associations of saml app : ')
                        self.log.info(x)
                        raise Exception(entity + absent)

    def validate_authid(self, user_email):
        """Validates the auth id of a user
            Args:
                user_email      (string)       user's email
            Raise:
                Exception if user auth id does not match with samlapp domain id
        """
        self.log.info('Validating auth id of {0}'.format(user_email))
        authid = self._get_user_authid(user_email)
        samlapp_domainid = self._get_samlapp_domainid()
        self.log.info('Auth id of user [%s]', authid)
        self.log.info('Saml app domain id [%s]', samlapp_domainid)
        if authid != samlapp_domainid:
            raise Exception('Auth id of {0} and {1} didnt match'.format(user_email, self._appname))
        self.log.info('Auth id is valid')

    def delete_saml_app(self):
        """Deletes a saml app"""
        if self.is_saml_app_exist():
            self.log.info('Deleting Saml app ' + self._appname)
            self._commcell.identity_management.delete_saml_app(self._appname)

    def is_saml_app_exist(self):
        """ Checks if saml app is present in commcell
            return:
                (bool)          True is saml app is present, Else False
        """
        if self._commcell.identity_management.has_identity_app(self._appname):
            self.log.info('{0} exists in commcell/company'.format(self._appname))
            return True

        self.log.info('{0} does not exist in commcell/company'.format(self._appname))
        return False

    def is_company_saml_app(self):
        """Check if the saml app is created for a company
            Returns:
                            (bool)      True if saml app is created for a company
                                        Else False
        """
        if self._samlapp.is_company_saml_app:
            self.log.info(self._appname + ' is created for a company')
        else:
            self.log.info(self._appname + ' is created at commcell level')
        return self._samlapp.is_company_saml_app

    def validate_samluser_properties(self, user_email, props):
        """Validates the saml user properties
            Args:
                user_email          (string)        user's email
                props               (dict)          user's prop in dict format
                                    ex        prop = {
                                                'login' : string,
                                                'userGuid':   string,
                                                'usergroups':   [string],
                                                'umdsproviderId': string,
                                                'name': string,
                                                'origUserGuid': string,
                                                'companyId': string,
                                                'upn': string,
                                                'password': string
                                                }
            Raises:
                Exception           if given user is not found in database
                                    if any given prop does not match with database

        """
        self.log.info('Fetching user properties from Database for {0}'.format(user_email))
        query = """select id, name, password, login, userGuid, origUserGuid, umdsproviderId, companyId, upn
                    from umusers where email = '{0}' and login not like '%deleted%'""".format(user_email)
        self.csdb.execute(query)
        db_props = self.csdb.fetch_one_row(True)[0]
        if len(self.csdb.fetch_one_row(True)) > 0:
            self.log.info('User properties fetched successfully')
        else:
            raise Exception(f'Error in getting user groups for user [{user_email}]')

        for key in ['login', 'userGuid', 'name', 'umdsproviderId', 'upn', 'origUserGuid, companyId', 'password']:
            if key in props:
                self.log.info('Validating ' + key)
                if db_props[key].lower() != props[key].lower():
                    self.log.info('DB value ['+db_props[key]+']' + 'Given value ['+props[key]+']')
                    raise Exception(key + ' for user did not match from db')

        if 'usergroups' in props:
            self.log.info('Fetching user group information for {0}'.format(user_email))
            query = """select name, domainName from umgroups g join UMDSProviders u on g.umdsProviderId = u.id
                    where g.id in (select groupid from umusergroup where userid = {0})""".format(db_props['id'])
            self.csdb.execute(query)
            db_props.update({'usergroups': [(row[1].lower() + '\\' + row[0].lower() if row[1] != 'Commcell'
                                             else row[0].lower()) for row in self.csdb.rows]})
            self.log.info('User groups information fetched successfully')

            self.log.info('Validating user groups')
            props['usergroups'] = [ug.lower() for ug in props['usergroups']]
            if sorted(props['usergroups']) != sorted(db_props['usergroups']):
                self.log.info('db_props[usergroups] : ')
                self.log.info(db_props['usergroups'])
                self.log.info('given user group list')
                self.log.info(props['usergroups'])
                raise Exception('Given user group list does not match with db_props[usergroups]')

    def samluser_redirect_url(self, user_email):
        """Get redirect url of given user via api
        Args:
            user_email  (str)   user email

        Returns:
            redirect url of user
        """
        return self._samlapp.get_saml_user_redirect_url(user_email)

    def samlapp_redirect_url(self):
        """Get redirect url of saml app from DB
        Returns :
            redirect url from props column in app_thirdpartyapp table
        """
        query = """declare @myDoc xml -- to store props xml
                set @myDoc = (select props from App_ThirdPartyApp where id in 
                (select id from app_thirdpartyapp where appname = '{0}'))
                declare @redirectUrlXml xml -- to store redirectUrl xml
                set @redirectUrlXml = (select T.C.query('.') from @myDoc.nodes('props/nameValues') T(C) 
                where T.C.value('@name', 'nvarchar(255)') = 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect')
                SELECT P.C.value('@value', 'nvarchar(100)')
                FROM @redirectUrlXml.nodes('nameValues') P(C)""".format(self._appname)

        if self._samlapp_redirect_url is None:
            response = self.utility.update_commserve_db(query)
            self._samlapp_redirect_url = response.rows[0][0]

        return self._samlapp_redirect_url

    @property
    def spmetadata(self):
        """Treats spmetadata as read only attribute
            Returns         dict        {
                                            'entityId': 'string',
                                            'singleSignOnUrl': 'string',
                                            'singleLogoutUrl': string',
                                            'spAliases': []
                                        }
        """
        return self._samlapp.saml_app_service_provider_metadata
    