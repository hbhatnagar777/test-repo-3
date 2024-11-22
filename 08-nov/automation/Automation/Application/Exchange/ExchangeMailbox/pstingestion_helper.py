# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Helper file for PSTIngestion related tasks

PSTIngestion:
    set_mbx_details()               -- Populate the mbx_details value

    get_file_list()                 -- Get all file list and its machine object,
                                        pst ingestion input details

    get_all_pst_owners()            --  Gets the pst owner for file list based on the owner order
                                        specified

    get_specific_pst_owner()        --  Gets the owner for a specific pst file based on the
                                        owner order specified

    get_owner_by_smtp()             --  Gets the the pst owner based on smtp in file path

    get_owner_by_file()             --  Gets the the pst owner based on owner of the file

    get_owner_by_alias()            --  Gets the the pst owner based on alias name in file path

    merge_backup_properties()       --  Merge the properties of pst with their corresponding
                                        user's email properties

    merge_specific_backup_props()   --  Merge mailbox properties of specific user

    merge_messages()                --  Merge messages from two list of folders
                                        (Ignore duplicate msgs)

    does_folder_exists()            --  Check if folder exists in the given lists of folders

    get_exchange_powershell_obj()   --  Create and return exchange powershell object for proxy
                                        machine

"""
import time
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.machine import Machine
from Application.Exchange.ExchangeMailbox.exchangelib_helper import CVFolder
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell


class PSTIngestion:
    """PST Ingetsion Helper class"""
    def __init__(self, exchange_obj, test_data, fix_mbx=None, fs_file_list=None):
        """Initializes the PSTIngestion object
            Args:
                exchange_obj(object)        -- instance of the exchange object

                test_data(object)           -- instance of the testdata object

                fix_mbx (list)              -- List of file owner and Laptop owner
                                                (users must be part of commcell)

                fs_file_list(dict)          -- Dictionary of files present in fs backup and its
                                                properties

        """

        self.ex_object = exchange_obj
        self.log = exchange_obj.tc_object.log
        self.mbx_details = self.set_mbx_details(test_data, fix_mbx)
        self.fs_file_list = {}
        self.default_owner_order = [1, 2, 4, 3]
        self.file_list = self.get_file_list(fs_file_list)

    def set_mbx_details(self, test_data, fix_mbx=None):
        """Populate the mbx_details value
            Args:
                test_data(object)           -- instance of the testdata object

                fix_mbx (list)              -- List of file owner and Laptop owner

            Returns:
                dictionary with mailbox name, smtp, alias, database

        """
        try:
            mbx_details = {}
            for item in test_data.json_value.Mailbox:
                disp_name = f'{item.DISPLAYNAME}_{test_data.testcase_id}'.lower()
                alias = f'{item.ALIASNAME}_{test_data.testcase_id}'.lower()
                smtp = f'{alias}@{self.ex_object.domain_name}'.lower()
                database = (f'{item.DATABASE}_{self.ex_object.exchange_server[0]}'
                            f'_{test_data.testcase_id}'.lower())
                mbx_details[alias] = [disp_name, alias, smtp, database]
            if fix_mbx:
                users_dict = self.ex_object.commcell.users.service_commcell_users_space
                users_dict = {user.lower(): details for user, details in users_dict.items()}
                for item in fix_mbx:
                    alias = item.split("\\")[-1].lower()
                    item = item.lower()
                    mbx_details[alias] = [users_dict[item]["fullName"].lower(),
                                          alias, users_dict[item]["email"].lower(), None]
                    mbx_details[item] = [users_dict[item]["fullName"].lower(),
                                         alias, users_dict[item]["email"].lower(), None]
            return mbx_details
        except Exception as excp:
            self.log.error("Error in setting mailbox details")
            raise excp

    def get_file_list(self, fs_file_list=None):
        """Get all file list and its machine object, pst ingestion input details
            Returns:
                dictionary with all file path as key and rest as details
        """
        try:
            file_list_dict = {}
            for item in self.ex_object.tc_object.tcinputs['pstIngestionDetails']['details']:
                if not fs_file_list and 'folders' in item:
                    for folder in item['folders']:
                        self.log.info("-------------------------- READING FILES UNDER FOLDER %s"
                                      "--------------------------" % str(folder))
                        machine_name = folder.split("\\")[2]
                        service_acc = self.ex_object.service_account_dict[0]
                        machine = Machine(machine_name, username=service_acc["Username"],
                                          password=service_acc["Password"])
                        file_list = machine.get_files_in_path(folder)
                        for pst_file in file_list:
                            if str(pst_file).lower()[-4:] != ".pst":
                                continue
                            file_list_dict[pst_file.lower()] = {
                                "type": 1,
                                "machine": machine,
                                "pstOwnerManagement": item["pstOwnerManagement"]}
                elif fs_file_list:
                    machine_obj = {}
                    for machine_name, files in fs_file_list.items():
                        if machine_name in machine_obj:
                            machine = machine_obj[machine_name]
                        else:
                            machine = Machine(machine_name,
                                              commcell_object=self.ex_object.commcell)
                            machine_obj[machine_name] = machine
                        for pst_file in files:
                            if str(pst_file).lower()[-4:] != ".pst":
                                continue
                            file_list_dict[pst_file.lower()] = {
                                "type": 2,
                                "machine": machine,
                                "fsowner": self.ex_object.tc_object.tcinputs[
                                    'pstIngestionDetails']["fsOwnerMbxName"].lower(),
                                "pstOwnerManagement": item["pstOwnerManagement"]}
            return file_list_dict
        except Exception as excp:
            self.log.error("Error in getting file list")
            raise excp

    def get_all_pst_owners(self):
        """Gets the pst owner for file list based on the owner order specified

            Returns:
                Owner alias name of files in file_list

        """
        try:
            self.log.info("========================= GETTING PST OWNERS =========================")
            owner_values = {}
            for pst_file, details in self.file_list.items():
                owner_order = []
                if "ownerSelectionOrder" in details["pstOwnerManagement"]:
                    owner_list = details["pstOwnerManagement"]["ownerSelectionOrder"]
                else:
                    owner_list = self.default_owner_order
                for owners in owner_list:
                    if int(owners) == 1:
                        owner_order.append(0)
                    elif int(owners) == 2:
                        if details["type"] == 2:
                            owner_order.append(1)
                        else:
                            raise Exception("PST Owner by Laptop is not valid for file shares")
                    elif int(owners) == 4:
                        owner_order.append(2)
                    elif int(owners) == 3:
                        owner_order.append(3)
                    else:
                        raise Exception("Invalid option for owner type")
                self.log.info("----- For file %s details are ------ " % str(pst_file))
                owner = self.get_specific_pst_owner(pst_file, owner_order, details)
                owner_values[pst_file] = []
                owner_values[pst_file].append(pst_file.split("\\")[-1])
                if not owner:
                    owner = details["pstOwnerManagement"]["defaultOwner"]
                if "\\" in owner:
                    owner = owner.split("\\")[1]
                owner_values[pst_file].append(owner.lower())
                self.log.info("Owner of file %s determined: %s " % (str(pst_file), str(owner)))
            return owner_values
        except Exception as excp:
            self.log.error("Error in getting all PST Owner")
            raise excp

    def get_specific_pst_owner(self, file_path, owner_order, details):
        """Gets the owner for a pst file based on the owner order specified
            Args:
                file_path(str)          -- Path of the file

                owner_order(list)       -- Order of owner

                details(dict)    		-- input deetails of pst ingestion association

            Returns:
                Owner alias name if present, None if not

        """
        try:
            smtp_list = {}
            alias_list = {}
            for alias_name, mbx_details in self.mbx_details.items():
                smtp_list[mbx_details[2]] = alias_name
                alias_list[alias_name] = alias_name

            owners = [self.get_owner_by_file(file_path, alias_list, details["machine"]),
                      None if details["type"] == 1 else self.get_owner_by_laptop(
                          details["machine"].machine_name, details["fsowner"]),
                      self.get_owner_by_smtp(file_path, smtp_list),
                      self.get_owner_by_alias(file_path, alias_list)]
            if owners[owner_order[0]]:
                return owners[owner_order[0]]
            if len(owner_order) > 1 and owners[owner_order[1]]:
                return owners[owner_order[1]]
            if len(owner_order) > 2 and owners[owner_order[2]]:
                return owners[owner_order[2]]
            if len(owner_order) > 3 and owners[owner_order[3]]:
                return owners[owner_order[3]]
            return None
        except Exception as excp:
            self.log.error("Error in determining PST Owner")
            raise excp

    def get_owner_by_smtp(self, file_path, smtp_list):
        """Gets the the pst owner based on smtp in file path
            Args:
                file_path(str)          -- Path of the file

                smtp_list(dictionary)  -- Dictionary of smtp address as key and alias names as val

            Returns:
                Owner alias name if present

        """
        names = file_path.split("\\")
        for smtp in names:
            if smtp in smtp_list:
                self.log.info("Owner by smtp is: %s" % str(smtp))
                return smtp_list[smtp]
        self.log.info("No owner by smtp found")

    def get_owner_by_laptop(self, client, owner_name):
        """Gets the owner based on the fs client owner
            Args:
                client(obj)     -- Client object of FS client

                owner_name(str) -- FS client owner provided in input

            Returns:
                Owner alias name if present
        """
        client_obj = self.ex_object.commcell.clients.get(client)
        for owner in client_obj.owners:
            if owner_name.lower() == owner.lower():
                return owner

    def get_owner_by_file(self, file_path, alias_list, machine):
        """Gets the pst owner based on owner of the file
            Args:
                file_path(str)          -- Path of the file

                alias_list(dictionary)  -- Dictionary of alias names in lower as key, alias name
                                            as value

                machine(Machine obj)    -- Machine object of the machine where file is located

            Returns:
                Owner alias name if present

        """
        owner = machine.get_file_owner(file_path)
        temp_res, o_domain, alias = True, None, None
        if isinstance(machine, WindowsMachine):
            if "\\" in owner:
                temp_res = False
                owner = owner.split("\\")
                o_domain, alias = owner[0].lower(), owner[1].lower()
        if temp_res:
            o_domain = self.ex_object.domain_name.split(".")[0].lower()
            alias = owner.lower()
        domain = self.ex_object.domain_name.split(".")[0].lower()
        if domain == o_domain and alias in alias_list:
            self.log.info("Owner by file is: %s" % str(alias))
            return alias_list[owner[1].lower()]
        self.log.info("No file owner found")

    def get_owner_by_alias(self, file_path, alias_list):
        """Gets the the pst owner based on smtp in file path
            Args:
                file_path(str)          -- Path of the file

                alias_list(dictionary)  -- Dictionary of alias names in lower as key, alias name
                                            as value

            Returns:
                Owner alias name if present

        """
        names = file_path.split("\\")
        for alias in names:
            if str(alias) in alias_list:
                self.log.info("Owner by alias : %s" % str(alias))
                return alias_list[str(alias)]

    def merge_backup_properties(self, backup_props, import_to_mbx, owner_val, db_name,
                                file_list=None):
        """Merge the properties of pst with their corresponding user's email properties
            Args:
                backup_props(object)        -- Backup properties of user mailbox

                import_to_mbx(str)          -- Alias name of mailbox to create (Should be from
                                                the list of mailboxes in test case)

                owner_val(dict)             -- Owner value dictionary(obtained from
                                                get_all_pst_owner method)

                db_name(str)                     -- Database name

                file_list(dict)             -- Dictionary of file name, machine obj, owner_order
                   (Default: None)              and default owner

            Returns:
                dictionary of file path as key, file name and owner as value

        """
        try:
            self.log.info("=================== MERGING BACKUP PROPERTIES ===================")
            exchange_power_shell_obj = self.get_exchange_powershell_obj()
            backup_obj_pst = self.ex_object.exchange_lib
            itr = 0
            if not file_list:
                file_list = self.file_list
            for pst_file, details in file_list.items():
                mbx_detail = [f'{import_to_mbx}_{itr}'.lower(), f'{import_to_mbx}_{itr}'.lower(),
                              f'{import_to_mbx}_{itr}@{self.ex_object.domain_name}'.lower(),
                              db_name]
                backup_obj_pst.mail_users = [mbx_detail[2]]
                if 'pstDestFolder' not in details['pstOwnerManagement']:
                    details['pstOwnerManagement']['pstDestFolder'] = "Archived From Automation"
                if 'createPstDestFolder' not in details['pstOwnerManagement']:
                    details['pstOwnerManagement']['createPstDestFolder'] = True
                exchange_power_shell_obj.create_mailbox(
                    mbx_detail[0], mbx_detail[1], mbx_detail[2], mbx_detail[3])
                exchange_power_shell_obj.import_pst(mbx_detail[1], pst_file)
                time.sleep(120)
                backup_obj_pst.get_mailbox_prop()
                folders = backup_obj_pst.mailbox_prop[mbx_detail[2]].folders
                mbx_prop_folder = backup_props.mailbox_prop[
                    self.mbx_details[owner_val[pst_file][1]][2]]
                mbx_prop_folder = self.does_folder_exists(mbx_prop_folder.folders,
                                                          'Top of Information Store')
                pst_prop_folder = self.does_folder_exists(folders, 'Top of Information Store')
                file_name = owner_val[pst_file][0].split(".pst")[0]
                self.log.info(
                    " ------------- MERGING PROPERTIES OF %s WITH MBX -------------- " % str(
                        pst_file))
                self.merge_specific_backup_props(pst_prop_folder, mbx_prop_folder,
                                                 details["pstOwnerManagement"], file_name)
                itr += 1
        except Exception as excp:
            self.log.error("Error in determining PST Owner")
            self.log.error(excp)
            raise excp

    def merge_specific_backup_props(self, pst_prop_folder, mbx_prop_folder, pst_ingestion_dict,
                                    file_name):
        """Merge mailbox properties of specific user
            Args:
                pst_prop_folder(CVFolder)      --  CVFolder obj of folder to be merged(obtained
                                                    from pst properties)

                mbx_prop_folder(CVFolder)      --  CVFolder obj of folder where to be merged
                                                    (obtained from mailbox properties)

                pst_ingestion_dict(dict)        --  pst Ingestion Details input dictionary

                file_name(str)                 --  Name of the file

        """
        try:
            if "createPstDestFolder" not in pst_ingestion_dict:
                self.log.info("createPstDestFolder value not specified in input. Setting "
                              "the value as True")
                pst_ingestion_dict["createPstDestFolder"] = True
            if pst_ingestion_dict["createPstDestFolder"]:
                pst_prop_folder.folder_name = pst_ingestion_dict["pstDestFolder"]
                if pst_ingestion_dict["usePSTNameToCreateChild"]:
                    temp_sub = pst_prop_folder.sub_folder
                    cvfolder = CVFolder()
                    cvfolder.folder_name = file_name
                    cvfolder.messages = []
                    cvfolder.sub_folder = temp_sub
                    attach_to = self.does_folder_exists(
                        mbx_prop_folder.sub_folder, pst_prop_folder.folder_name)
                    if attach_to:
                        self.log.info("Folder %s present in sub folders of %s. Appending it the "
                                      " list of sub folders of %s"
                                      % (str(cvfolder.folder_name),
                                         str(pst_prop_folder.folder_name),
                                         str(pst_prop_folder.folder_name)))
                        attach_to.sub_folder.append(cvfolder)
                    else:
                        self.log.info("Folder %s not present. Appending it to %s list of folders"
                                      % (str(pst_prop_folder.folder_name),
                                         str(mbx_prop_folder.folder_name)))
                        pst_prop_folder.sub_folder = [cvfolder]
                        mbx_prop_folder.sub_folder.append(pst_prop_folder)
                else:
                    self.log.info("Merging folder hierarchy to folder %s" %
                                  str(pst_prop_folder.folder_name))
                    self.merge_messages(mbx_prop_folder.sub_folder, [pst_prop_folder])
            elif pst_ingestion_dict["usePSTNameToCreateChild"]:
                pst_prop_folder.folder_name = file_name
                self.log.info("Appending folder to %s list of sub folders of %s"
                              % (str(pst_prop_folder.folder_name),
                                 str(mbx_prop_folder.folder_name)))
                mbx_prop_folder.sub_folder.append(pst_prop_folder)
            else:
                self.log.info("Merging folder hierarchy to folder %s" %
                              str(mbx_prop_folder.folder_name))
                self.merge_messages(mbx_prop_folder.sub_folder, pst_prop_folder.sub_folder)
        except Exception as excp:
            self.log.exception("Error in merging mailbox properties of PST %s" % str(file_name))
            raise Exception(excp)

    def merge_messages(self, folder_list, folders_to_merge):
        """Merge messages from two list of folders (Ignore duplicate msgs)
            Args:
                folder_list(list)       -- Where merge needs to occur

                folders_to_merge(list)  -- Folders to be merged

        """

        try:
            extra_folders = []
            for folder_to_merge in folders_to_merge:
                org_folder = self.does_folder_exists(folder_list, folder_to_merge.folder_name)
                if org_folder:
                    entry_id = set()
                    for msg in org_folder.messages:
                        entry_id.add(msg.entry_id)
                    for msg in folder_to_merge.messages:
                        if msg.entry_id not in entry_id:
                            org_folder.messages.append(msg)
                    self.merge_messages(org_folder.sub_folder, folder_to_merge.sub_folder)
                else:
                    extra_folders.append(folder_to_merge)
            for folder in extra_folders:
                folder_list.append(folder)
        except Exception as excp:
            self.log.exception("Error in merging mailbox messages")
            raise Exception(excp)

    def does_folder_exists(self, folder_list, folder_name):
        """Check if folder exists in the given lists of folders
            Args:
                folder_list(list)       -- List of the folders

                folder_name(str)        -- Name of folder

            Returns:
                CVFolder object of the found folder

        """
        try:
            for folder in folder_list:
                if str(folder.folder_name).lower() == folder_name.lower():
                    return folder
            return None
        except AttributeError as excp:
            self.log.exception("Exception occurred")
            raise excp

    def verify_owners(self, original_val, computed_val):
        """Verify if the owner from job details is same as owner expected(For PST Ingestion task)
            Args:
                original_val(dict)      -- Dictionary of owner values

                computed_val(list)      -- List of dictionaries from job details

        """
        try:
            for item in computed_val:
                self.log.info("Verifying owner details for file %s " % item['PSTPath'])
                if str(item['PSTOwner'].lower()) != str(
                        original_val[item['PSTPath'].lower()][1].lower()):
                    raise Exception("Owner value for file %s do not match.\nOwner from job %s, "
                                    "owner computed %s" %
                                    (str(item['PSTPath']), str(item['PSTOwner']),
                                     str(original_val[item['PSTPath'].lower()][1])))
        except KeyError as key_excp:
            self.log.exception("Key not present! %s" % str(key_excp))
            raise key_excp

        except Exception as excp:
            raise excp

    def get_exchange_powershell_obj(self):
        """Create and return exchange powershell object for proxy machine
            Returns:
                Exchange Powershell Object

        """
        try:
            return ExchangePowerShell(
                self.ex_object,
                self.ex_object.exchange_cas_server,
                self.ex_object.exchange_server[0],
                self.ex_object.service_account_user,
                self.ex_object.service_account_password,
                self.ex_object.server_name,
                self.ex_object.domain_name
            )
        except AttributeError as excp:
            self.log.exception("Exception occurred while creating exchange powershell obj")
            raise excp

    def file_list_gen_helper(self, file_path, subclient, file_list):
        """Helper method to get list of files in subclient
            Args:
                file_path(str)  -- Absolute path of the file

                subclient(Obj)  -- object of the subclient to check

                file_list(dict) --  Dictionary of client and files on it
        """
        browse, browse_detail = subclient.browse(path=[file_path])
        for key, value in browse_detail.items():
            if value["type"].lower() == "file":
                file_list.append(key)
            else:
                self.file_list_gen_helper(key, subclient, file_list)
