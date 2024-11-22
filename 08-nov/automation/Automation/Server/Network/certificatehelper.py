# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing certificate operations

CertificateHelper: Helper class to perform certificate operations
"""

from cvpysdk.certificates import Certificate
from AutomationUtils.machine import Machine


class CertificateHelper:
    def __init__(self, testcase_object):
        self.testcase = testcase_object
        self.commcell = testcase_object.commcell
        self.certificate = Certificate(testcase_object.commcell)

    def get_certificate_ids(self, client_names):
        """
        Fetch all the active certificate id's for the client name

        Args:
            client_names (List(str)): List of client names
        
        Resturn:
            dict: Dictionary of active certificate id's for clients

        Example:
            get_certificate_ids(["MyClient1", "MyClient2"])
        """
        return_dict = {}
        for client_name in client_names:
            self.testcase.csdb.execute(f"SELECT id FROM APP_Client WHERE name = '{client_name}'")
            client_id = self.testcase.csdb.fetch_one_row()[0]

            self.testcase.csdb.execute(f"SELECT certid FROM App_ClientCerts WHERE clientId = {client_id} AND status = 2")
            cert_id = self.testcase.csdb.fetch_all_rows()

            try:
                cert_ids = []
                for outer in cert_id:
                    for inner in outer:
                        if inner.isdigit():
                            cert_ids.append(int(inner))
                return_dict[client_name] = cert_ids
            except:
                return -1
        return return_dict

    def renew(self, client_names):
        """
        Perform renew operation on client

        Args:
            client_names (List(str)): List of client names

        Return:
            bool: Status of operation

        Example:
            renew(["MyClient1", "MyClient2"])
        """
        cert_ids = []
        for client_name in client_names:
            cert_ids.extend(self.get_certificate_ids([client_name])[client_name])

        try:
            resp = self.certificate.renew(cert_ids)
        except Exception as e:
            self.testcase.log.error(str(e))
            return False

        new_cert_ids = []
        for client_name in client_names:
            new_cert_ids.extend(self.get_certificate_ids([client_name])[client_name])

        if len(new_cert_ids) != 2*len(cert_ids):
            raise Exception(f"All certificate does not get renewed.")
        return True

    def revoke(self, client_names):
        """
        Perform revoke operation on client

        Args:
            client_names (List(str)): List of client names

        Return:
            bool: Status of operation

        Example:
            revoke(["MyClient1", "MyClient2"])
        """
        cert_ids = []
        for client_name in client_names:
            cert_ids.extend(self.get_certificate_ids([client_name])[client_name])

        try:
            resp = self.certificate.revoke(cert_ids)
        except Exception as e:
            self.testcase.log.error(str(e))
            return False

        return cert_ids

    def force_client_authentication(self, operation):
        """
        Enable or disable the lockdown mode

        Args:
            operation (bool): Turn ON/OFF the lockdown mode. 

        Return: 
            bool: if request processed successfully

        Example:
            force_client_authentication(True)
            force_client_authentication(False)
        """
        return self.certificate.force_client_authentication(operation)

    def check_crl(self, cert_ids):
        """
        Check if the certificate id get revoked or not

        Args:
            cert_ids (List[int]): List of certificate id

        Return: 
            bool: True if all the id's get revoked else return false
        
        Example:
            check_crl([10, 11, 12, 13])
        """
        cs_obj = self.commcell.clients.get(self.commcell.commserv_name)
        ma_obj = Machine(cs_obj)

        folders = ma_obj.get_folders_in_path(cs_obj.install_directory+"\\base\\certificates", False)
        crl_data = ''
        for folder in folders:
            if ma_obj.check_file_exists(folder+"\\crl.txt"):
                crl_data = ma_obj.read_file(folder+"\\crl.txt")
                crl_data = crl_data.split()

        if crl_data == '':
            raise Exception("crl.txt Not Found")
        else:
            found  = False
            for id in cert_ids:
                for revoked_id in crl_data:
                    if '-' in revoked_id:
                        start, end  = revoked_id.split("-")
                        if int(start) <= id <= int(end):
                            found = True
                    elif id == int(revoked_id):
                        found = True
        if not found:
            raise Exception(f"{id} Not found in crl list.\nCRL: {crl_data}")
        return True

    def client_certificate_rotation(self, months):
        """
        Modify certificate rotation period.

        Args:
            months (int): Number of months.

        Return: 
            bool: if request processed successfully

        Example:
            client_certificate_rotation(12)
        """
        self.certificate.client_certificate_rotation(months)
        return True

    def ca_certificate_rotation(self, years):
        """
        Modify certificate rotation period.

        Args:
            years (int): Number of years.

        Return: 
            bool: if request processed successfully

        Example:
            ca_certificate_rotation(1)
        """
        self.certificate.ca_certificate_rotation(years)
        return True
    
    def make_temp_certificate(self, client_id):
        """
        Args:
            client_id (int): Client Id to generate certificate.

        Return: 
            str: Temp certificate for the client.

        Example:
            make_temp_certificate(5)
        """
        return self.certificate.make_temp_certificate(client_id)

