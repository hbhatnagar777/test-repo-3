# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    main file for validating all the options for restores

Class:
    CVD365Restore - class defined for validating  all Dynamics 365 restores options

        CVD365Restore:

        compare_table_prop()                --  Compare before and after backup properties for a particular table
        validate_records()                  --  Validate the before and after restore properties for a record
"""

import re
from .d365web_api.d365_rec import Record


class CVD365Restore(object):
    """Class for performing Restore related operations."""

    def __init__(self, d365_object):
        """Initializes the Restore object.
            Args:
                d365_object  (Object)  --  instance of CVDynamics365 module

            Returns:
                object  --  instance of CVD365Restore class
        """
        self.tc_object = d365_object.tc_object
        self.log = self.tc_object.log
        self.valid_folders = set()
        if self.tc_object.tcinputs.get("Relationships"):
            self.table_level = self.create_table_level_hash(self.tc_object.tcinputs.get("D365_Tables"))

    @staticmethod
    def create_table_level_hash(d365_tables):
        """
            Args:
                d365_tables     <dict>:     All the tables associated to a level

            Returns:
                A dict with table as keys and which level it belongs to as value
        """

        table_level = {}
        for level in d365_tables:
            for table in d365_tables.get(level).split(','):
                table_level[table] = int(level.split(' ')[1])

        return table_level

    def compare_table_prop(self, before_backup: dict, after_restore: dict, restore_level: str = None):
        """Compare table properties
            Args:

                before_backup (dict)            --  Table Properties before backup object

                after_restore (dict)            --  Table properties after backup object

                restore_level (str)             --  Related Restore level to be triggered
            Raises:
                Exception:
                    If comparison fails
        """
        try:
            self.log.info(
                "*********************************************************************")

            self.log.info("Validating restore for tables")
            for table in before_backup:
                self.log.info(f"Verifying properties for table {table}")
                if not len(after_restore[table]):
                    if not restore_level:
                        current_level = 0
                    else:
                        current_level = int(restore_level.split(" ")[1])
                    if self.table_level[table] > current_level:
                        self.log.info(f"Skipping this table as restore level is {current_level} and table belongs to "
                                      f"{self.table_level[table]} level")
                        continue
                    else:
                        self.log.exception(f"Verification Failed, values are empty for {table} but it shouldn't be")
                for entity_id in before_backup[table].keys():
                    before_backup_obj = before_backup[table].get(entity_id)
                    if entity_id not in after_restore[table].keys():
                        self.log.exception(
                            "Entity ID: {} not in After Restore Entities considering Related Records".format(entity_id))
                    after_restore_obj = after_restore[table].get(entity_id)
                    status = self.validate_records(before_backup_obj, after_restore_obj, table, restore_level)
                    if status is False:
                        self.log.info("After Restore: {}".format(after_restore_obj))
                        self.log.info("Before Backup: {}".format(before_backup_obj))
                        raise Exception("Record Properties did not match")
                    self.log.info(f"Properties Comparison Successful for record {entity_id}")
                self.log.info(f"Table {table} comparison successful")

        except Exception as excp:
            self.log.exception('An error occurred while validating record')
            raise excp

    def validate_records(self, before_backup_record: Record, after_restore_record: Record, table: str,
                         restore_level: str):
        """Validate record restore
            Args:
                before_backup_record    --  Record object for record before backup
                after_restore_record    --  Record object for record after restore
            Returns:
                  record_matched        (bool)  Whether the record properties matched before and after restore
        """
        try:
            skip_fields = ("createdon", "@odata.etag", "openrevenue_date", "opendeals_date", "versionnumber",
                           "modifiedon", "_modifiedby_value", "_createdonbehalfby_value", "_modifiedonbehalfby_value")
            if not restore_level:
                skip_regex = '.*value|.*date|.*base'
            else:
                skip_regex = '.*date|.*base'
            skip_pattern = re.compile(skip_regex)
            before_backup_data = before_backup_record.record_data
            after_restore_data = after_restore_record.record_data
            flag = False
            for attribute in before_backup_data.keys():
                if attribute not in skip_fields and not skip_pattern.search(attribute):
                    before_restore = before_backup_data.get(attribute)
                    after_restore = after_restore_data.get(attribute)
                    if before_restore != after_restore:
                        if restore_level and re.compile('.*value').search(attribute) and after_restore is None:
                            current_level = int(restore_level.split(" ")[1])
                            if self.table_level[table] >= current_level:
                                self.log.info(f"Relationship of {table} doesn't exist as restore level is "
                                              f"{restore_level} and table belongs to Level"
                                              f"{self.table_level[table]}")
                                continue
                            else:
                                flag = True
                        else:
                            flag = True

                    if flag:
                        self.log.info("Before and After Restore values do not match")
                        self.log.info(f"Attribute {attribute} didn't match, before restore :{before_restore}, "
                                      f"after_restore: {after_restore}")
                        self.log.info("Before Restore: {}".format(before_backup_data))
                        self.log.info("After Restore: {}".format(after_restore_data))
                        return False
            return True
        except Exception as excp:
            self.log.exception('An error occurred while validating record')
            raise excp
