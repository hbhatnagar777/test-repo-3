# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module is use to setup shared LDAP related operations

Class:
    ldap_basic            --    Basic ldap connection to all ldap servers

        __init__()        --    initial ldap class

        assign_fields()   --    assign necessary properties

        get_server_info() --    collect server basic info. detect server type

        connect()         --     connect ldap server
"""
__all__ = ["LdapBasic"]


from ldap3 import Server, Connection, ALL, NTLM
from ldap3.core.exceptions import LDAPSocketOpenError,\
                                LDAPUnknownAuthenticationMethodError,\
                                LDAPBindError
from .exceptions import ADException


class LdapBasic():
    """ ldap basic operation"""

    def __init__(self, **kwargs):
        """ initial ldap class objects"""
        required_fields = ['server']
        if "log" in kwargs:
            self.log = kwargs['log']
        else:
            raise ADException('ldap', 1, "add log object")
        optional_fields = ['user', 'password', 'port', 'basedn']
        self.log.debug("start to assign all attributes for ldap instance")
        self.assign_fields(kwargs, required_fields, optional_fields)
        self.log.debug("ldap instance is created")

    def assign_fields(self, kwargs, required_fields, optional_fields):
        """ assign class level properties
        Args:
            kwargs            (dict)    parameter passed when class is initialed

            required_fields    (list)    mondatory properties

            optional_fields    (list)    operation proerpties, will set to None if not passed
        Return:
            None:
        Exception:
            None
        """
        for field in required_fields:
            setattr(self, field, kwargs[field])
            self.log.debug("attribute {0} value is {1}".format(field,
                                                               kwargs[field]))
        for field in optional_fields:
            try:
                setattr(self, field, kwargs[field])
                self.log.debug("attribute {0} value is {1}".format(field,
                                                                   kwargs[field]))
            except KeyError:
                self.log.debug("{0} attribute is not set".format(field))

    def get_server_info(self):
        """ Check LDAP server information to separate server type"""
        self.log.debug("start to collect Ldap server information")
        ldap_server_info = {}
        s_ins = Server(self.server, get_info=ALL)
        try:
            Connection(s_ins, auto_bind=True)
        except LDAPSocketOpenError as ldaperror:
            raise ADException("ldap", 101, f"""
connect to server {self.server} receive error {ldaperror}""")
        ldap_server_info = s_ins.info.raw
        if "vendorname" in ldap_server_info.keys():
            if ldap_server_info['vendorname'][0] == b'IBM Lotus Software':
                ldap_server_info['vendorname'] = "IBM Domino"
                self.log.debug("This is a Domino server")
        elif "vendorName" in ldap_server_info.keys():
            if "dsServiceName" in ldap_server_info.keys():
                dsservicename = str(ldap_server_info['dsServiceName'][0]).split(",")[0]
                if dsservicename.split("=")[1] == "NTDS Settings":
                    ldap_server_info['vendorname'] = "Microsoft AD"
                    self.log.debug("This is Microsoft ad server")
        return ldap_server_info

    def connect(self):
        """ Connect LDAP server with parameters"""
        self.log.debug("Prepare LDAP server connection")
        info = self.get_server_info()
        self.log.debug("LDAP server basic information is {0}".format(info))
        ldap_info = {}
        s_ins = Server(self.server)

        if info['vendorname'] == "Microsoft AD":
            self.log.debug("Start to setup AD connection")
            # it seem not working with child domain
            ldap_info['basedn'] = info['defaultNamingContext'][0].decode('utf-8')
            ldap_info['config'] = "CN=Configuration,%s" % ldap_info['basedn']
            ldap_info['schema'] = "CN=Schema,%s" % ldap_info['config']
            ldap_info['namingContexts'] = []
            for entry in info['namingContexts']:
                if entry.decode('utf-8')  not in list(ldap_info.values()):
                    ldap_info['namingContexts'].append(entry.decode('utf-8'))

            try:
                ldap_conn = Connection(s_ins,
                                       self.user,
                                       self.password,
                                       authentication=NTLM,
                                       auto_bind=True)
            except LDAPUnknownAuthenticationMethodError as ldaperror:
                raise ADException('ldap', 103, ldaperror)
            except LDAPBindError as ldaperror:
                raise ADException('ldap', 102,
                                  f"""
error is {ldaperror},user is {self.user}, password is {self.password}""")
        else:
            ldap_conn = Connection(s_ins,
                                   user=self.user,
                                   password=self.password,
                                   auto_bind=True)
        try:
            ldap_conn.bind()
        except:
            self.log.warning("There is a ldap bind issue")
            ldap_conn = None
        ldap_conn.lazy =True
        return ldap_conn, ldap_info, self.log
