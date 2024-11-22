# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    run()                           --  run function of this test case

    tear_down()                     --  tear down function of this test case

    validate_create_tags()          --  Creates tagset & tags and verifies it got created or not

    validate_modify_tags()          --  Modifies tagset & tags and verifies it got modified or not

    validate_share_tags()           --  Shares tagset and verifies it got shared or not

    validate_delete_tags()          --  Deletes tagset and verifies it got deleted or not

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase

from cvpysdk.activateapps.entity_manager import EntityManagerTypes
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Basic Tag Manager validation for CvpySDK"
        self.tcinputs = {
            "ShareUserName": None,
            "ShareUserPassword": None
        }
        self.tag_mgr = None
        self.tag_set_name = "Integration TagSet_cvpysdkTest"
        self.tag_name = "Integration tag_cvpysdkTest"
        self.unicode_tag_set_name = "गणित का इतिहास_cvpysdkTest"
        self.unicode_tag_name = "गणित_cvpysdkTest"
        self.tag_set_obj = None
        self.unicode_tag_set_obj = None
        self.tag_obj = None
        self.unicode_tag_obj = None

    def validate_delete_tags(self):
        """Deletes tagset and verifies it got deleted or not"""
        self.log.info(f"Deleting Tagset : {self.tag_set_name}")
        self.tag_mgr.delete(tag_set_name=self.tag_set_name)
        if self.tag_mgr.has_tag_set(tag_set_name=self.tag_set_name):
            raise Exception("Tagset exists even after deletion")
        self.log.info(f"Deleting Tagset : {self.unicode_tag_set_name}")
        self.tag_mgr.delete(tag_set_name=self.unicode_tag_set_name)
        if self.tag_mgr.has_tag_set(tag_set_name=self.unicode_tag_set_name):
            raise Exception("Tagset exists even after deletion")

    def validate_share_tags(self):
        """Shares tagset and verifies it got shared or not"""
        self.log.info(f"Get commcell object for new shared user : {self.tcinputs['ShareUserName']}")
        share_user_commcell_obj = Commcell(
            self.inputJSONnode['commcell']['webconsoleHostname'],
            self.tcinputs['ShareUserName'],
            self.tcinputs['ShareUserPassword'])
        share_user_tag_mgr = share_user_commcell_obj.activate.entity_manager(EntityManagerTypes.TAGS)
        if share_user_tag_mgr.has_tag_set(
                tag_set_name=self.tag_set_name) or share_user_tag_mgr.has_tag_set(
                tag_set_name=self.unicode_tag_set_name):
            raise Exception("Shared user is able to see Tagsets from admin without sharing")

        self.log.info(f"Sharing Tags : {self.tag_name} inside Tagset : {self.tag_set_name} with View permission")
        self.tag_set_obj.share(user_or_group_name=self.tcinputs['ShareUserName'])
        self.log.info(
            f"Sharing Tags : {self.unicode_tag_name} inside Tagset : {self.unicode_tag_set_name} with Edit Permission")
        self.unicode_tag_set_obj.share(user_or_group_name=self.tcinputs['ShareUserName'], allow_edit_permission=True)
        self.log.info("Sharing completed")
        self.log.info("Shared user logging out and doing relogin again")
        share_user_commcell_obj.logout()
        share_user_commcell_obj = Commcell(
            self.inputJSONnode['commcell']['webconsoleHostname'],
            self.tcinputs['ShareUserName'],
            self.tcinputs['ShareUserPassword'])
        share_user_tag_mgr = share_user_commcell_obj.activate.entity_manager(EntityManagerTypes.TAGS)
        self.log.info("Relogin success. Proceed with Shared entity check")
        if not share_user_tag_mgr.has_tag_set(
                tag_set_name=self.tag_set_name) or not share_user_tag_mgr.has_tag_set(
                tag_set_name=self.unicode_tag_set_name):
            raise Exception("Shared user is not able to see Tagsets shared by admin")
        self.log.info("Validate Tag creation error for view only user")
        try:
            tag_set_obj = share_user_tag_mgr.get(tag_set_name=self.tag_set_name)
            tag_set_obj.add_tag(tag_name="View only permission tag")
        except Exception as exp:
            if 'User does not have Edit access' not in exp.exception_message:
                raise Exception("Tagset delete operation by User with only view permission Failed!!!")
            self.log.info("Tag creation failed for view only Tagset")
        unicode_tag_set_obj = share_user_tag_mgr.get(tag_set_name=self.unicode_tag_set_name)
        unicode_tag_set_obj.add_tag(tag_name="Edit permission tag")
        self.log.info("Tag creation succeed for View/Edit only Tagset")
        if not unicode_tag_set_obj.has_tag(tag_name="Edit permission tag"):
            raise Exception("Created tag is not visible inside Tagset shared with Edit Permission")
        self.log.info("Deleting shared tagset with Edit Permission")
        try:
            share_user_tag_mgr.delete(tag_set_name=self.unicode_tag_set_name)
        except Exception as exp:
            if 'User does not have Delete access' not in exp.exception_message:
                raise Exception("Tagset delete operation by User with Edit permission Failed")
            self.log.info("Tagset deletion failed for Tagset with Edit permission for User")
        self.log.info("Sharing validation done")

    def validate_modify_tags(self):
        """Modifies tagset & tags and verifies it got modified or not"""
        self.log.info(f"Modifying Tags : {self.tag_name} inside Tagset : {self.tag_set_name}")
        self.tag_obj = self.tag_set_obj.get(tag_name=self.tag_name)
        self.tag_name = f"{self.tag_name}_modified"
        self.tag_obj.modify(new_name=self.tag_name)
        self.log.info(f"Modifying Tags : {self.unicode_tag_name} inside Tagset : {self.unicode_tag_set_name}")
        self.unicode_tag_obj = self.unicode_tag_set_obj.get(tag_name=self.unicode_tag_name)
        self.unicode_tag_name = f"{self.unicode_tag_name}_modified"
        self.unicode_tag_obj.modify(new_name=self.unicode_tag_name)
        self.log.info("Modification completed for Tags")
        self.tag_set_obj.refresh()
        self.unicode_tag_set_obj.refresh()
        self.log.info(f"Tags[{self.tag_set_obj.tags}] are there in Tagset[{self.tag_set_name}]")
        self.log.info(f"Tags[{self.unicode_tag_set_obj.tags}] are there in Tagset[{self.unicode_tag_set_name}]")
        if self.tag_name.lower() not in self.tag_set_obj.tags or self.unicode_tag_name.lower() not in self.unicode_tag_set_obj.tags:
            raise Exception("Modified tags are not present in commcell")
        self.log.info(f"Modifying Tagset : {self.unicode_tag_set_name}")
        self.unicode_tag_set_name = f"{self.unicode_tag_set_name}_modified"
        if self.tag_mgr.has_tag_set(tag_set_name=self.unicode_tag_set_name):
            self.log.info(f"Deleting Older Tagset as it exists already with same name ; {self.unicode_tag_set_name}")
            self.tag_mgr.delete(tag_set_name=self.unicode_tag_set_name)
        self.unicode_tag_set_obj.modify(new_name=self.unicode_tag_set_name)
        self.log.info("Modification completed for Tagset")
        self.tag_mgr.refresh()
        if not self.tag_mgr.has_tag_set(tag_set_name=self.unicode_tag_set_name):
            raise Exception("Unable to find Tagset with modified name")
        self.log.info("Modify validation done")

    def validate_create_tags(self):
        """Creates tagset & tags and verifies it got created or not"""
        self.log.info(f"Creating TagSet : {self.tag_set_name}")
        if self.tag_mgr.has_tag_set(tag_set_name=self.tag_set_name):
            self.log.info("Deleting Tagset as it exists already")
            self.tag_mgr.delete(tag_set_name=self.tag_set_name)
        self.tag_set_obj = self.tag_mgr.add(tag_set_name=self.tag_set_name)
        self.log.info(f"Creating TagSet : {self.unicode_tag_set_name}")
        if self.tag_mgr.has_tag_set(tag_set_name=self.unicode_tag_set_name):
            self.log.info("Deleting Tagset as it exists already")
            self.tag_mgr.delete(tag_set_name=self.unicode_tag_set_name)
        self.unicode_tag_set_obj = self.tag_mgr.add(tag_set_name=self.unicode_tag_set_name)
        self.log.info(f"Creating Tags : {self.tag_name} inside Tagset : {self.tag_set_name}")
        self.tag_set_obj.add_tag(tag_name=self.tag_name)
        self.log.info(f"Creating Tags : {self.unicode_tag_name} inside Tagset : {self.unicode_tag_name}")
        self.unicode_tag_set_obj.add_tag(tag_name=self.unicode_tag_name)
        if not self.tag_mgr.has_tag_set(
                tag_set_name=self.tag_set_name) or not self.tag_mgr.has_tag_set(
                tag_set_name=self.unicode_tag_set_name):
            raise Exception("Tagset not created in commcell")
        if not self.tag_set_obj.has_tag(
                tag_name=self.tag_name) or not self.unicode_tag_set_obj.has_tag(
                tag_name=self.unicode_tag_name):
            raise Exception("Tags not created properly inside TagSet")

        if self.tag_set_obj.owner_alias_name.lower() != self.commcell.commcell_username.lower():
            raise Exception(
                f"Owner info not set properly in Tagset. "
                f"Expected:{self.commcell.commcell_username} Actual:{self.tag_set_obj.owner_alias_name}")
        self.log.info(f"Owner info check passed. Value : {self.tag_set_obj.owner_alias_name}")
        self.log.info("Create validation done")

    def setup(self):
        """Setup function of this test case"""
        self.tag_mgr = self.commcell.activate.entity_manager(EntityManagerTypes.TAGS)

    def run(self):
        """Run function of this test case"""
        try:
            self.validate_create_tags()
            self.validate_modify_tags()
            self.validate_share_tags()
            self.validate_delete_tags()

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
