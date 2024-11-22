# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This library is used to communicate with Microsoft AD

Class:
    ADOps        AD related operations

        __init__()        initial Microsoft AD instance

        attributes_mapper    create mapping to reuse the code

        ugo_search        search UGO (user group and Ou) objects

        search()            basic raw Ldap search

        search1()            Ldap extend search to return paged objects

        search_result_fitler()    filter search result refe and entry

        ugo_attributes_check()    UGO indivdual properties check

        ugo_process()        UGO object clean ,convert attribute to readable value

        ugo_get_attribtue()    collect UGO object properties

        entries_search()        search objects in particular entrypoint

        entries_process()        process search result

        entries_dn_split()        split AD dn to relative path

        entry_category_get_type()    get AD object category types

        ugo_add()            add UGO objects

        ugo_add_user()        add AD user

        ugo_user_attributes()    AD user madatary attribute

        ugo_objs()            convert UGO objects attribute more readable.

        ugo_operation()        predefined ugo operations, like delete , modify

        ugo_list()            list all UGO objects

        cv_ugo_delete()        delete entry for UGO object based on AD subclinet

        cv_ad_objectlist()    create ad objects based on AD subcient content
Function:

    ad_entrypoint_combine        decarator    combine AD Dn with base dn

    cv_ad_objectscompare        compare ad objects between tow ad content list

    cv_conent_convert            convert subclient string to ad string format

    cv_contents                    convert subclient content to AD format

Limitation:

"""
__all__ = []

import sys
from collections import Counter
from ldap3 import SUBTREE, MODIFY_REPLACE
from AutomationUtils import logger

from .ldap_common import LdapBasic
from .adconstants import AD_TYPE_MAPPER, AD_OU_MAPPER, AD_USER_MAPPER,\
                        AD_GROUP_MAPPER, AD_CATEGORY_TYPES,\
                        AD_OBJECT_CLASS_PRE_MAPPER, AD_OBJECT_CLASS_MAPPER,\
                        AD_UGO_ATTRIBUTELIST, AD_USER_OBJECT_CLASS
from .baselibs import tc
from .exceptions import ADException



def ad_entrypoint_combine(func):
    """ decorator to process AD distribution name """
    def wrapper(*args, **kwargs):
        """ use default basedn if not additional entrypoitn defined"""
        if kwargs['entrypoint'] is None:
            kwargs['entrypoint'] = args[0].basedn
        else:
            if kwargs['entrypoint'][:2].lower() in ["ou", "cn"]:
                # if the entrypoint is raw data, just append
                if kwargs['entrypoint'].find(args[0].basedn) > 0:
                    # this is full DN nam passed, skip
                    pass
                else:
                    kwargs['entrypoint'] = f"{kwargs['entrypoint']},{args[0].basedn}"
            else:
                if 'entrytype' in kwargs:
                    # if the entrypint is not ou, it can be
                    #     cn for container or
                    #     other type property.
                    kwargs['entrypoint'] = f"{kwargs['entrytype']}={kwargs['entrypoint']},{args[0].basedn}"
                else:
                    kwargs['entrypoint'] = f"ou={kwargs['entrypoint']},{args[0].basedn}"
        return func(*args, **kwargs)

    return wrapper


class ADOps():
    """ Microsoft AD related operation"""

    def __init__(self, **kwargs):
        """initial AD connection and attribute mapper"""
        ldap_ins = LdapBasic(**kwargs)
        self.conn, self.ldap_info, self.log = ldap_ins.connect()
        if self.conn is not None:
            self.basedn = self.ldap_info['basedn']
            # convert the domain name from dc=jungles,dc=commvault,dc=com to
            # jungels.commvault.com
            self.domainname = "".join(self.basedn.replace(',', '.').lower().split("dc="))
            self.log.debug(f"AD object base DN is {self.basedn}")
            self.log.debug(f"AD object domain name is {self.domainname}")
        else:
            raise ADException("ad", 10, f"input is {kwargs}")
        self.log.debug("start to create AD object mapper")
        self.attributes_mapper()

    def attributes_mapper(self):
        """ Attribute mapper to reduce duplciate code
            most of common case is use UGO to do most of OU, Group and User
            operations.
        """
        # map type to correct DN name
        self.category_mapper = {"Group" : f"CN=Group,{self.ldap_info['schema']}",
                                "User"  : f"CN=Person,{self.ldap_info['schema']}",
                                "OU"    : f"CN=Organizational-Unit,,{self.ldap_info['schema']}",
                                "Computer" : f"CN=Computer,{self.ldap_info['schema']}"}
        # object class for create new user
        self.log.debug("all AD related mapper are created")

    def ugo_search(self, scope="Users", objtype="User",
                   objname=None,
                   searchbase=None):
        """ UGO related search
        Args:

            scope        (string)    OU or containers name for search

            objtype        (string)    choice form User, Group and OU

            objname        (string)    search particular object name

            seaarchbase    (string)    entrypoint for search
        Return:
            (list)    UGO objects in particular entrypoint
        Exceptions:
            None
        """
        if searchbase is None:
            if scope == 'Users':
                searchbase = "cn=Users,"+self.basedn
            else:
                searchbase = self.basedn

            if objtype in self.category_mapper:
                basefilter = f'(objectCategory={self.category_mapper[objtype]})'
            else:
                raise ADException("ad", 201, f"objtype is {objtype}")

            if objname is None:
                filterstring = basefilter
            else:
                filterstring = f"(&{basefilter}(name={objname}))"

            ugo_objs = self.search1(searchbase, filterstring, SUBTREE)
            if ugo_objs:
                ugo_objs = self.search_result_filter(ugo_objs)
                self.log.debug(f"UGO search Found {len(ugo_objs)} results")

            ugo = self.ugo_process(ugo_objs, objtype)

            return ugo

    def search(self, basename, filterstring, pagesize=None, scope=SUBTREE):
        """ basic search , doesn't support page, only 1000 item returned
        Args:
            basename    (string)    entrypoint for search
            filterstring (string)    search filter based on LDAP protocol
            pagesize     (int)    return page size
            scope        (CON)    LDAP defiined constants
        Return:
            serachresult    (list)    search result
        Excpetion:
            None
        """
        searchpara = {'search_base'    : basename,
                        'search_filter'  : filterstring,
                        'search_scope'   : scope,
                        'attributes'     : "*",
                        'size_limit'     : 0}
        if pagesize is not None:
            searchpara['paged_size'] = pagesize
        searchresult = []
        while True:
            self.conn.search(**searchpara)
            if self.conn.response:
                searchresult = self.conn.response
                self.log.debug(f"AD regular search found {len(searchresult)} result")
            else:
                searchresult = None
            break
        return searchresult

    def search1(self, basename, filterstring, scope=SUBTREE):
        """ basic page search
        Args:
            basename    (string)    entrypoint for search

            filterstring    (string)     filterstring based on LDAP protocols

            scope    (string)    LDAP predefinded constants
        Return:
            (list)    search result base don search
        Exception:
            None
        """
        searchpara = {'search_base'    : basename,
                      'search_filter'  : filterstring,
                      'search_scope'   : scope,
                      'attributes'     : "*"}

        searchref = self.conn.extend.standard.paged_search(**searchpara)
        searchresult = []
        for entry in searchref:
            searchresult.append(entry)
        return searchresult

    def search_result_filter(self, adobjs):
        """ remove search related result
        Args:
            adobjs    (list)    list of searhc result
        Return:
            (list)    clean search result
        Excpetion:
            None
        Todo:
            will change to a decoration later
        """
        objs = []
        for obj in adobjs:
            if obj['type'] == "searchResEntry":
                objs.append(obj)
            elif obj['type'] == "searchResRef":
                pass
            else:
                self.log.debug(f"ms object type is unknown: {obj['type']}")
        return objs

    def ugo_process(self, ugo_objs, objtype):
        """ UGO object search result clean up
        Args:
            ugo_objs        (list)    UGO objects to process

            objtype        (string)    pick from User, Group and OU.
        Return:
            (list)        Cleaned objects
        Exceptions:
            None
        Todo:
            will convert to decorator
        """
        clean_objs = []
        ugo_mapper = getattr(self, AD_TYPE_MAPPER[objtype])
        for obj_ in ugo_objs:
            obj_as = {}
            for att in ugo_mapper:
                obj_as[att] = obj_['attributes'][ugo_mapper[att]]

            if objtype == 'OU':
                obj_as['path'] = obj_as['dn'].split(f",{self.basedn}")[0]
                obj_as['category'] = obj_['attributes']['objectCategory'].split(
                    f",{self.basedn}")[0]
            elif objtype == "Group":
                obj_as['path'] = obj_as['cn'].split(f",{self.basedn}")[0]
                obj_as['category'] = obj_['attributes']['objectCategory'].split(
                    f",{self.basedn}")[0]
                try:
                    obj_as['member'] = obj_['attributes']['member']
                except KeyError:
                    pass
            elif objtype == "User":
                obj_as['path'] = obj_as['cn'].split(f",{self.basedn}")[0]
                obj_as['category'] = obj_['attributes']['objectCategory'].split(
                    f",{self.basedn}")[0]
                try:
                    obj_as['mail'] = obj_['attributes']['mail']
                except KeyError:
                    self.log.deubg("no mail attribute for this user")
            clean_objs.append(obj_as)
        return clean_objs

    def entries_search(self, objtype=None, entrypoint=None):
        """ search result with DN and type
        Args:
            objtype     (str)    picked from User,Group and OU

            entrypoint     (str)    entrypoint for ad search
        Return:
            (List)    searchresult
        Exception:
            None
        """
        if entrypoint is None:
            searchbase = self.basedn
        else:
            searchbase = f"{entrypoint},{self.basedn}"
        if objtype is None:
            filterstring = "(objectCategory=*)"
        else:
            filterstring = f"(objectCategory={self.category_mapper[objtype]})"
        scope = SUBTREE
        searchobjs = self.search1(searchbase, filterstring, scope)
        searchresult = self.search_result_filter(searchobjs)
        return searchresult

    def entries_process(self, searchresult, actions=None):
        """ process search entry result
        Args:
            searchresult    (list)    search results of ad objects

            actions        (list)    sequence process actions
        Return:
            None
        Exception:
             None
        """
        if actions is None:
            actions = []
        for entry in searchresult:
            if "category_add_types" in actions:
                self.entry_category_get_types(entry, AD_CATEGORY_TYPES)

    def entry_dn_split(self, entry, entrypoint=None, level=1):
        """ split entry dn to relative path
        Args:
            entry    (string)    AD object DN

            entrypoint    (string)      AD split entrypoint

            level    (int)    how many level will split
        Return:
            string    relative path wihtout base dn
        Exceptions:
            None
        Todo:
            convert to decorator later.
        """
        ad_dn = entry['attributes']['distinguishedName']
        if entrypoint is None:
            dn_ss = ad_dn.split(self.basedn)[0].split(",")
        else:
            dn_ss = ad_dn.split(entrypoint)[0].split(",")

        levelresult = []
        if len(dn_ss) == 2*level:
            levelresult = dn_ss[level-1].split("=")
        return levelresult

    def entry_category_get_types(self, entry, newtypes):
        """ get search entry category
        Args:
            entry    (Instance)    AD object

            newtypes    (lsit)    Get AD object category
        Return:
            (list)     category type
        Except:
            None
        """
        darkobj = []
        if 'objectCategory' not in entry['attributes'].keys():
            darkobj.append(entry)
        else:
            objectcategory = entry['attributes']['objectCategory']
            if objectcategory not in list(self.category_mapper.values())+newtypes:
                newtypes.append(objectcategory.split(self.ldap_info['schema'])[0].split("=")[1])
        return newtypes

    @ad_entrypoint_combine
    def ugo_add(self, objtype, name=None, entrypoint=None, attributes=None):
        """ UGO add new objects
         Args:
             objtype    (string)    pick form User, Group or OU

             name    (string)     object name

             entrypoint    (string)     ad object entrypoint

             attributes    (dict)    ad objects attributes
         Return:
             (Boolean)    objects create result
         Exception:
             None
         """
        if name is None:
            name = f"TS_{tc()}"

        entrydn = f"{AD_OBJECT_CLASS_PRE_MAPPER[objtype]}={name},{entrypoint}"
        if objtype in ['OU', 'Group']:
            self.log.debug(f"will create {objtype} with name {name}")
            if attributes is None:
                operesult = self.conn.add(entrydn, AD_OBJECT_CLASS_MAPPER[objtype])
            else:
                operesult = self.conn.add(entrydn, AD_OBJECT_CLASS_MAPPER[objtype], attributes)
        else:
            # special handle to add user
            self.log.debug("will create a new user")
            if attributes is None:
                self.log.debug("no user information is passed")
                operesult = self.ugo_add_user(username=name, entrypoint=entrypoint)
        return operesult

    @ad_entrypoint_combine
    def ugo_add_user(self,
                     username=None,
                     firstname=None,
                     lastname=None,
                     password=None,
                     entrypoint=None):
        """ special hanlde to create user

        Args:
            username    (string)    username

            firstname    (string)    first name

            lastname    (string)    last name

            password    (string)    user password

            entrypoint    (string)    AD object entrypoint
        Return:
            (Boolean)    oepration result, ture or false
        Exception:
            ad    210     When user create failed.
        """
        if firstname is None:
            firstname = f"TS_{int(tc())}"
            self.log.debug(f"no firstname, use default value {firstname}")
        if lastname is None:
            lastname = "ScriptCreateUser"
            self.log.debug(f"no lastname, use default value {lastname}")

        if username is None or username.startswith("TS_"):
            username = f"SCU_{firstname}"
        self.log.debug(f"will create user with name {username}")
        user_attributes = self.ugo_user_attributes(username, firstname, lastname)
        self.log.debug(f"new user attributes is {user_attributes}")
        if password is None:
            password = "######"
        userdn = f"cn={username},{entrypoint}"
        self.log.debug(f"user dn is {userdn}")
        operesult = self.conn.add(userdn, AD_USER_OBJECT_CLASS,
                                  attributes=user_attributes)
        if operesult:
            self.log.debug("user is created, will enabled this user")
            # We need different call to update user password in python 3.6 and 3.8
            self.conn.extend.microsoft.unlock_account(user=userdn)
            if sys.version_info.minor == 8:
                self.conn.extend.standard.modify_password(userdn, None, password)
            elif sys.version_info.minor == 6:
                self.conn.extend.microsoft.modify_password(user=userdn,
                                                           new_password=password,
                                                           old_password=None)
            self.conn.modify(userdn, changes={"userAccountControl":  (MODIFY_REPLACE, [544])})
        else:
            raise  ADException('ad', 210, f"create user {username} failed")
        return operesult

    def ugo_user_attributes(self, username, firstname, lastname):
        """ set user attribute based on basic information
        Args:
            username    (string)    user name

            firstname    (string)    first name

            lastname    (string)    last name
        Return:
            (dict)    user attribute dict
        Exception:
            None
        Todo:
            will use decarator
        """
        return {
            "displayName": username,
            "sAMAccountName": username,
            "userPrincipalName": f"{username}@{self.domainname}",
            "name": username,
            "givenName": firstname,
            "sn": lastname
        }

    def ugo_objs(self, searchresult, entrypoint=None):
        """ UGO get all UGO objects based on entrypoint
        Args:
            searchresult     (list)    list of AD objects

            entrypoint        (string)    AD object entrypoint
        Return:
            (dict}    UGO predefined objects
        Exceptions:
            None
        """
        if entrypoint is None:
            obj_basedn = self.basedn
        else:
            obj_basedn = entrypoint+","+self.basedn
        objs_entries = {}
        for entry in searchresult:
            if entry['dn'] == obj_basedn:
                pass
            else:
                name = entry['attributes']['name']
                if name in objs_entries:
                    pass
                else:
                    objs_entries[name] = {}
                for attr in AD_UGO_ATTRIBUTELIST:
                    objs_entries[name][attr] = entry['attributes'][attr]

        return objs_entries

    def ugo_operation(self, objtype,
                      name=None,
                      entrypoint=None,
                      operation=None,
                      raw=False):
        """ UGO related operation, include delete
        Args:
            objtype        (string)     picked form User, Group or OU
            name        (string)        AD object name
            entrypoint    (string)    Ad object entry point
            operation    (string)    predefined operation like delete, modify
            raw         (boolean)    If the dn name is rule
        Return:
            None
        Exception:
            None
        """

        if entrypoint is None:
            entrypoint = self.basedn
        else:
            entrypoint = entrypoint+","+self.basedn
        if raw:
            obj_dn = name
        else:
            obj_dn = f"{AD_OBJECT_CLASS_PRE_MAPPER[objtype]}={name},{entrypoint}"
        if operation == "Delete":
            self.conn.delete(obj_dn)

        return None

    def ugo_list(self, entrypoint=None):
        """ UGO list all objects
        Args:
            entrypoint     (string)    AD entrypoint
        Return:
            (list)        a list of AD objects

            (int)        total number or search result
        Exceptoin:
            None
        """
        objlists = self.entries_search(None, entrypoint)
        ad_entries = self.ugo_objs(objlists, entrypoint)
        total_entries = len(ad_entries.keys())
        return ad_entries, total_entries

    @ad_entrypoint_combine
    def ugo_package(self, entrypoint=None, prestring=None, fixname=None):
        """ UGO create a pcakge to include UGO objects
        Args:
            entrypoint    (string)    entrypoint for new objects
            prestring    (string)    prestring for all time based name
            fixname        (string)    UGO fixname for fixname objects
        Return:
            (List)    new ad objects created
        Exception:
            None
        """
        new_ad_objs = []
        if prestring is None:
            prestring = "UGO"
        if fixname is None:
            self.log.debug("NO fixname give, will create object with time")
            ouname = f"{prestring}_OU_{tc(timeformat='ISO')}"
            groupname = f"{prestring}_Group_{tc(timeformat='ISO')}"
            username = f"{prestring}_User_{int(tc())}"
            if len(username) >20: # user name length have 20 limitation
                username = f"{prestring}_User_{str(int(tc()))[-3:]}"
        else:
            self.log.debug("create object with fix name")
            ouname = f"{prestring}_OU_{fixname}"
            groupname = f"{prestring}_Group_{fixname}"
            username = f"{prestring}_User_{fixname}"
        self.ugo_add('OU', name=ouname, entrypoint=entrypoint)
        self.log.debug(f'New OU is created: {ouname}')
        self.ugo_add("Group", name=groupname, entrypoint=entrypoint)
        self.log.debug(f"New group is created: {groupname}")
        self.ugo_add("User", name=username, entrypoint=entrypoint)
        self.log.debug(f"New user is created: {username}")
        new_ad_objs.append(("User", username))
        new_ad_objs.append(("Group", groupname))
        new_ad_objs.append(("OU", ouname))
        return new_ad_objs

    def cv_ugo_delete(self, objlist, ad_content=None, entrypoint=None):
        """ Commvault agnet UGO objects delete
        Args:
            objlist    (list)    AD objects to process

            ad_content    (list)    AD content from commvault subclient instance
            entrypoint    (str)    dn of ad object to do the operation
        Return:
            None
        Exceptiong:
            None
        """
        self.log.debug("will delete all cv create UGO objects")
        for entry in objlist:
            if isinstance(entry[0], dict):
                self.log.debug("entry get from list, will use raw format")
                for ad_obj in entry[0].keys():
                    self.log.debug(f"remove {entry[0][ad_obj]['distinguishedName']}")
                    self.ugo_operation(None,
                                       name=entry[0][ad_obj]['distinguishedName'],
                                       operation="Delete",
                                       raw=True)
            elif isinstance(entry[0], str):
                if not entrypoint:
                    entrypoint = ad_content[0][1]
                self.ugo_operation(entry[0],
                                   entry[1],
                                   entrypoint=entrypoint,
                                   operation="Delete")
            else:
                raise ADException("cvad", 201, entry)

    def cv_ad_objectlist(self, ad_content):
        """ Commvault objects list
        Args:
            ad_content    (list)    ad list from commvault subcleint instance
        Return:
            (list)    ad objects
        Exception:
            None
        """
        ad_objlists = []
        for content in ad_content:
            ad_objlist, ad_objlist_num = self.ugo_list(content[1])
            ad_objlists.append((ad_objlist, ad_objlist_num))
        return ad_objlists

def cv_ad_objectscomapre(source,
                         destination,
                         diff_objs_list=None,
                         judgement_value=None):
    """ Commvault objects properites list

        Args:
            source        (list)    Ad objects list

            destination    (list)    ad objects list

            diff_objs_list    (list)     different obj list

            judgement_value    (Boolean)    True , False or None

        Return:
            (Boolean)     check result based on different

            (list)    cokmpare result
        Exception:
            None
    """
    log = logger.get_log()
    log.info("Start to compare the result")
    obj_diff = []
    attr_diff = []
    diff_objs = []
    diff_check = []
    checkresult = None

    if diff_objs_list is not None:
        log.info("there is different object list, comparing it")
        for entry in diff_objs_list:
            if entry[1] in source[0][0]:
                diff_check.append(True)
            else:
                diff_check.append(False)
        diff_counter = Counter(diff_check)
        diff_count = diff_counter.popitem()
        log.debug(f"diff count is {diff_count}")
        log.debug(f"diff counter is {diff_counter}")
        log.debug(f"diff check is {diff_check}")
        if diff_count[1] != len(diff_check):
            checkresult = None
        else:
            checkresult = diff_count[0]

        if judgement_value is not None:
            if judgement_value == checkresult:
                returnvalue = (True, diff_check)
            else:
                returnvalue = (False, diff_check)
        else:
            returnvalue = (checkresult, diff_check)
    else:
        log.debug("no different list provided")
        if len(source) != len(destination):
            log.debug(f"source and destination have different length.\nsource is {len(source)} and destination is {len(destination)}")
            returnvalue = None
        else:
            for sitem, index_ in enumerate(source):
                src_objlist = sitem[0]
                des_objlist = destination[index_][0]
                src_objlist_len = sitem[1]
                des_objlist_len = destination[index_][1]
                same_objs_key = list(set(src_objlist.keys())&set(des_objlist.keys()))
                diff_objs_key = list(set(src_objlist.keys())^set(des_objlist.keys()))
                if des_objlist_len-src_objlist_len == len(diff_objs_key):
                    log.debug("compare result is same")
                else:
                    log.debug(f"source and destination have different length:\n\
                              source len is {src_objlist_len}, destination len is {des_objlist_len}\n\
                                different is {des_objlist_len-src_objlist_len}\n\
                                we exepcted is {len(diff_objs_key)}")
                log.debug(f"same objects are {same_objs_key}")
                log.debug(f"diff objects are {diff_objs_key}")
                returnvalue = (obj_diff, attr_diff, diff_objs)
    return returnvalue

class CVAD():
    """
    Commvault AD operation

    This class represents the Commvault AD operation. It provides methods for performing backup, restore, and verification
    of Active Directory objects using the Commvault API.

    Args:
        ad_ins (object): The instance of the AD class.
        subclient (object): The instance of the Commvault subclient.
        restore_path (str): The path to restore the AD objects.
        ad_content (list): The list of AD objects to be backed up.

    Attributes:
        ad_ins (object): The instance of the AD class.
        log (object): The logger object for logging.
        subclient (object): The instance of the Commvault subclient.
        restore_path (str): The path to restore the AD objects.
        ad_content (list): The list of AD objects to be backed up.
    """

    def __init__(self, ad_ins, subclient, restore_path, ad_content):
        """
        Initialize the CVAD class.

        Args:
            ad_ins (object): The instance of the AD class.
            subclient (object): The instance of the Commvault subclient.
            restore_path (str): The path to restore the AD objects.
            ad_content (list): The list of AD objects to be backed up.
        """
        self.ad_ins = ad_ins
        self.log = ad_ins.log
        self.subclient = subclient
        self.restore_path = restore_path
        self.ad_content = ad_content

    def backup(self, backuptype="Incremental", incremental_backup=True):
        """
        Perform a backup operation.

        Args:
            backuptype (str, optional): The type of backup to perform. Defaults to "Incremental".
            incremental_backup (bool, optional): Whether to perform an incremental backup. Defaults to True.

        Returns:
            str: The status of the backup job.
        """
        self.log.debug(f"start a {backuptype} backup ")
        job = self.subclient.backup(backup_level=backuptype, incremental_backup=incremental_backup)
        self.log.debug(f"backup is started, job id is {job.job_id}")
        jobresult = job.wait_for_completion()
        self.log.debug(f"backup job {job.job_id} is completed. The status is {jobresult}")

    def restore(self):
        """
        Run restore job.
        """
        self.log.debug("start to restore all objects from latest backup")
        job = self.subclient.restore_in_place(paths=[self.restore_path])
        jobresult = job.wait_for_completion()
        self.log.debug(f"restore job {job.job_id} is completed. The status is {jobresult}")

    def verify_restore(self, objs, judgement_value=True):
        """
        Verify restore result.
        """
        self.log.debug("start to verify restore result")
        restored_objs = self.ad_ins.cv_ad_objectlist(self.ad_content)
        self.log.debug("check restore result")
        result, diff_check = cv_ad_objectscomapre(restored_objs,
                                                    None,
                                                    diff_objs_list=objs,
                                                    judgement_value=judgement_value)
        if result:
            self.log.debug(f"all {len(diff_check)} found in list, the new objects are restored")
        else:
            self.log.debug(f"not all {len(diff_check)} found in list, the new objects are not restored")
            raise Exception("ad", "301", f"restored objects is {restored_objs}, expected objects is {objs}")

    def simple_backup(self, backuptype="Incremental", objs= None, incremental_backup=True):
        """
        Run simple backup and restore.

        Args:
            backuptype (str, optional): The type of backup to perform. Defaults to "Incremental".
            objs (list, optional): The list of objects to backup. Defaults to None.
            incremental_backup (bool, optional): Whether to perform an incremental backup. Defaults to True.

        Returns:
            list: The list of objects that were backed up.
        """
        if backuptype == "Full":
            objs += self.ad_ins.ugo_package(entrypoint=self.ad_content[0][1],
                                            prestring="Base",
                                            fixname="Objs")
        elif backuptype == "synthetic_full":
            objs += self.ad_ins.ugo_package(entrypoint=self.ad_content[0][1],
                                            prestring="Sync")
        else:
            objs += self.ad_ins.ugo_package(entrypoint=self.ad_content[0][1],
                                            prestring="Incr")
        self.log.debug(f"objects to be backup is {objs}")
        self.log.debug(f"start to run simple backup with backup level {backuptype}")
        self.backup(backuptype=backuptype, incremental_backup=incremental_backup)
        if backuptype == "Full":
            self.restore()
            self.log.debug("verify all objects are restored")
            self.verify_restore(objs, judgement_value=True)
        else:
            self.log.debug("start to delete objects from AD")
            self.ad_ins.cv_ugo_delete(objs, self.ad_content)
            self.log.debug("verify all objects are deleted")
            self.verify_restore(objs, judgement_value=False)
            self.restore()
            self.log.debug("verify all objects are restored")
            self.verify_restore(objs, judgement_value=True)
        return objs
