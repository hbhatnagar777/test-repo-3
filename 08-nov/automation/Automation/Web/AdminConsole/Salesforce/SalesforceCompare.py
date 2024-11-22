# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on a Salesforce Compare page

CompareRecords: class to hold Compare Records for Compare page

SFCompare: class to hold data from Compare page

SalesforceCompare:

    __set_compare_config()  --   Method to set compare details

    object_compare()        --   Method to perform object comparison

    metadata_compare()      --   Method to perform metadata comparison

    access_overview_tab()   --   Method to click on overview tab


"""

from Web.AdminConsole.Components.core import CalendarView
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Salesforce.constants import CompareType, CompareChangeType
from Web.Common.page_object import PageService
from dataclasses import dataclass
from datetime import datetime, timezone
from Web.Common.exceptions import CVWebAutomationException


def timestamp_to_dict(timestamp):
    out = {
        'year': timestamp.year,
        'month': timestamp.strftime("%B"),
        'day': timestamp.day,
        'minute': timestamp.minute
    }
    hour = timestamp.hour
    if hour > 12:
        hour -= 12
        session = "PM"
    elif hour == 12:
        session = "PM"
    else:
        session = "AM"
    out["hour"] = hour if hour != 0 else 12
    out["session"] = session
    return out


@dataclass(frozen=False)
class CompareRecords:
    """class to hold Compare Records for Compare page"""
    nums: int = 0
    records: list = None


@dataclass(frozen=False)
class SFCompare:
    """class to hold data from Compare page"""
    sobject: str
    added: CompareRecords = None
    deleted: CompareRecords = None
    modified: CompareRecords = None
    total_first: CompareRecords = None
    total_sec: CompareRecords = None


class SalesforceCompare:
    """Class for Compare page"""

    def __init__(self, admin_console):
        """
        Init method for this class

        Args:
            admin_console (Web.AdminConsole.Helper.AdminConsoleBase.AdminConsoleBase): Object of AdminConsoleBase class

        Returns:
            None:
        """
        self.__admin_console = admin_console
        self.__page_container = PageContainer(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__calendar = CalendarView(self.__admin_console)

    @PageService()
    def __set_date_and_time(self, time, is_job_id, dropdown_id):
        """
            Args:
                time: dict/timestamp or job id to fill in source/destination compare dropdown
                is_job_id: boolean to represent whether passed time is a job or timestamp
                dropdown_id: dropdown to fill the time/job
            Returns:
                  None
        """
        if not isinstance(time, dict) and not is_job_id:
            time = timestamp_to_dict(time)

        if not is_job_id:
            self.__rdropdown.select_drop_down_values(values=[self.__admin_console.props["label.chooseCustomDate"]],
                                                     drop_down_id=dropdown_id)
            self.__calendar.set_date_and_time(time)
        else:
            self.__rdropdown.select_drop_down_values(values=[time], drop_down_id=dropdown_id, partial_selection=True)

    @PageService()
    def __set_compare_config(self, compare_type, first_time, sec_time, compare_options):
        """
            Method to set compare details

            Args:
                compare_type: object of type CompareType
                first_time: dict containing datetime details for first time selector
                sec_time: dict containing datetime details for second time selector
                compare_options: dict having additional options
                    des_org: destination org for metadata compare
                    is_job_id: boolean to represent whether passed time is a job or timestamp

            Returns:
                None:
                """

        self.__rdropdown.select_drop_down_values(values=[compare_type.value], drop_down_id="compareTypeDropdown")
        if des_org := compare_options.get('des_org', False):
            self.__rdropdown.select_drop_down_values(values=[des_org], drop_down_id="destinationDropdown")
        self.__set_date_and_time(first_time, compare_options.get('is_job_id', False), "left")
        self.__set_date_and_time(sec_time, compare_options.get('is_job_id', False), "right")

    @PageService()
    def object_compare(self, first_time, sec_time, objects, fields=None, **compare_options) -> list[SFCompare]:
        """
            Method to perform object comparison

            Args:
                first_time: dict containing datetime details for first time selector
                sec_time: dict containing datetime details for second time selector
                objects: list of objects to compare
                fields: field to collect data
                compare_options:
                    des_org: destination org
                    is_job_id: boolean to represent whether passed time is a job or timestamp

            Returns:
                list of Compare objects
                        """
        self.__set_compare_config(CompareType.OBJECT, first_time, sec_time, compare_options)
        self.__admin_console.click_button_using_text(self.__admin_console.props["action.compare"])
        compare_list = list()
        for object_name in objects:
            self.__rtable.search_for(object_name)

            compare_row = self.__rtable.get_table_data()

            if len(compare_row.get(self.__admin_console.props["label.sfObjectName"])) == 0:
                raise CVWebAutomationException("Both Backups have Identical Content")
            first_time_utc = datetime.fromtimestamp(first_time.timestamp(), tz=timezone.utc)
            sec_time_utc = datetime.fromtimestamp(sec_time.timestamp(), tz=timezone.utc)
            first_time_str = [key for key in compare_row.keys() if
                              any(x for x in [datetime.strftime(first_time, "%#I:%M %p").upper(),
                                              datetime.strftime(first_time_utc, "%#I:%M %p").upper()]
                                  if x in key.upper())
                              ][0]
            sec_time_str = [key for key in compare_row.keys() if
                            any(x for x in [datetime.strftime(sec_time, "%#I:%M %p").upper(),
                                            datetime.strftime(sec_time_utc, "%#I:%M %p").upper()]
                                if x in key.upper())
                            ][0]
            compare = SFCompare(sobject=compare_row.get(self.__admin_console.props["label.sfObjectName"])[0],
                                added=CompareRecords(nums=int(compare_row.get("Added")[0])),
                                deleted=CompareRecords(nums=int(compare_row.get("Deleted")[0])),
                                modified=CompareRecords(nums=int(compare_row.get("Modified")[0])),
                                total_first=CompareRecords(
                                    nums=int(compare_row.get(first_time_str)[0]),
                                    records=list()),
                                total_sec=CompareRecords(
                                    nums=int(compare_row.get(sec_time_str)[0]),
                                    records=list()))

            for title, itr in (
                    (CompareChangeType.ADDED, compare.added),
                    (CompareChangeType.DELETED, compare.deleted),
                    (CompareChangeType.MODIFIED, compare.modified)):
                if itr.nums > 0:
                    self.__rtable.access_link_by_column_title(object_name, title.value, itr.nums)
                    self.__admin_console.wait_for_completion()
                    if fields:
                        self.__rtable.display_hidden_column(fields)
                    records = self.__rtable.get_table_data(all_pages=True)
                    itr.records = [dict(zip(records.keys(), row_data)) for row_data in zip(*records.values())]
                    self.__admin_console.select_hyperlink(
                        self.__admin_console.props["label.sfcompare.objectCompare.summaryTitle"])
            compare_list.append(compare)
        return compare_list

    @PageService()
    def metadata_compare(self, first_time, sec_time, objects, **compare_options) -> list[SFCompare]:
        """
        Method to perform metadata compare

        Args:
            first_time: dict containing datetime details for first time selector
            sec_time: dict containing datetime details for second time selector
            objects: list of objects to compare
            compare_options:
                des_org: destination org
                is_job_id: boolean to represent whether passed time is a job or timestamp

        Returns:
            list of Compare objects

        """
        self.__set_compare_config(CompareType.METADATA, first_time, sec_time, compare_options)
        self.__admin_console.click_button_using_text(self.__admin_console.props["action.compare"])
        compare_list = list()
        for object_name in objects:
            self.__rtable.search_for(object_name)

            compare_row = self.__rtable.get_table_data()

            if len(compare_row.get("Folder")) == 0:
                raise CVWebAutomationException(self.__admin_console.props["error.sfcompare.metadataCompare.identical"])

            compare = SFCompare(sobject=compare_row.get("Folder")[0],
                                added=CompareRecords(nums=int(compare_row.get("Added")[0])),
                                deleted=CompareRecords(nums=int(compare_row.get("Deleted")[0])),
                                modified=CompareRecords(nums=int(compare_row.get("Modified")[0])))

            for title, itr in (
                    (CompareChangeType.ADDED, compare.added),
                    (CompareChangeType.DELETED, compare.deleted),
                    (CompareChangeType.MODIFIED, compare.modified)):
                if itr.nums > 0:
                    self.__rtable.access_link_by_column_title(object_name, title.value, itr.nums)
                    self.__admin_console.wait_for_completion()
                    records = self.__rtable.get_table_data(all_pages=True)
                    itr.records = [dict(zip(records.keys(), row_data)) for row_data in zip(*records.values())]
                    self.__admin_console.select_hyperlink(
                        self.__admin_console.props["label.sfcompare.metadataCompare.mdSummary"])
            compare_list.append(compare)
        return compare_list

    @PageService()
    def access_overview_tab(self):
        """
        Clicks on overview tab

        Returns:
            None:
        """
        self.__page_container.select_tab(self.__admin_console.props['label.tab.overview'])
