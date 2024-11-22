# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
 Module to manage License Summary report.

 LicenseHelper:

     __init__()

     goto_commcellgroup()                        -- naviagtes to commcell group

     create_commcell_group()                     -- creates commcell group

     delete_commcell_group()                     -- deletes commcell group

     validate_clientgroup()                      -- validates number of commcells in group with given commcell count

     access_clientgroup()                        -- accesses group Current Capacity Usage report

     dashboard()                                 -- creates Dashboard object

     lic_summary()                               -- creates LicenseSummary object

     close_windowhandles()                        -- close browser tabs if it is more than one

     manage_commcells()                          -- creates ManageCommcells object

     get_allindividual_commcell_tabledata()      -- returns individual commcell data

     generate_summary_and_validate()                          -- generates group data and individual commcell data

     __validate_allvalues()                      -- validates group data values with individual commcell data values


"""

from Web.WebConsole.Reports.Metrics.commcellgroup import CommcellGroup, ColumnNames
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.WebConsole.Reports.Metrics.licensesummary import LicenseSummary
from Web.WebConsole.Reports.monitoringform import ManageCommcells
from Web.WebConsole.Reports.navigator import Navigator


class LicenseHelper:

    """
    Activity report operation on metrics
    """

    def __init__(self, groupname, commcellist, webconsole, log):
        """
                Args:
                     webconsole: WebConsole object
        """
        self.webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self.log = log
        self._navigator = None
        self.commcell_group_name = groupname
        self.commcell_group = None
        self.commcelllist = commcellist
        self._lic_summary = None
        self._manage_commcells = None
        self._dashboard = None

    def goto_commcellgroup(self):
        """
        navigates to commcell group
            Args:
                none

            Returns:
                none

        """
        self.webconsole.goto_commcell_dashboard()
        self.navigator.goto_commcell_group()
        self.commcell_group = CommcellGroup(self.webconsole)

    def create_commcell_group(self):
        """
        creates a new commcell group
            Args:
                none

            Returns:
                none

        """
        """create commcell group pages"""

        self.log.info("Creating [%s] commcell group", self.commcell_group_name)
        self.delete_commcell_group()
        self.commcell_group.create(self.commcell_group_name, self.commcelllist)

    def delete_commcell_group(self):
        """
        deletes the commcell group
            Args:
                none

            Returns:
                none

        """

        if self.commcell_group.is_group_exist(self.commcell_group_name):
            self.commcell_group.delete(self.commcell_group_name)

    def validate_clientgroup(self):
        """
        checks whether the group commcell count equals the specified commcell count
            Args:
                none

            Returns:
                none

        """

        commcell_count = self.commcell_group.commcell_count_of_group(self.commcell_group_name)
        if int(commcell_count) != int(len(self.commcelllist)):
            raise Exception(
                f"Client group count {commcell_count} and commcell list count {len(self.commcelllist)} is not same")

    def access_clientgroup(self):
        """
        accesses group's Current Capacity Usage report
            Args:
                none

            Returns:
                none

        """
        self.commcell_group.apply_filter(ColumnNames.GROUP_NAME,
                                         self.commcell_group_name)
        self.webconsole.wait_till_load_complete()
        self.commcell_group.access_commcell_group(self.commcell_group_name)
        self.dashboard.view_detailed_report("Current Capacity Usage")

    @property
    def dashboard(self):
        """
        creates new Dashboard object
            Args:
                none

            Returns:
                Dahsboard obj

        """
        if self._dashboard is None:
            self._dashboard = Dashboard(self.webconsole)
        return self._dashboard

    @property
    def navigator(self):
        """
        creates new navigator object
            Args:
                none

            Returns:
                navigator obj

        """
        if self._navigator is None:
            self._navigator = Navigator(self.webconsole)
        return self._navigator

    @property
    def lic_summary(self):
        """
        creates new LicenseSummary object
            Args:
                none

            Returns:
                LicenseSummary obj

        """
        if self._lic_summary is None:
            self._lic_summary = LicenseSummary(self.webconsole)
        return self._lic_summary

    @property
    def manage_commcells(self):
        """
        creates new ManageCommcells object
            Args:
                none

            Returns:
                ManageCommcells obj

        """
        if self._manage_commcells is None:
            self._manage_commcells = ManageCommcells(self.webconsole)
        return self._manage_commcells

    def close_windowhandles(self):
        """
        close browser tabs if it is more than one
        """
        log_windows = self._driver.window_handles
        for window in log_windows[1:]:
            self._driver.switch_to.window(window)
            self._driver.close()
        self._driver.switch_to.window(log_windows[0])
        self.webconsole.wait_till_load_complete()

    def get_allindividual_commcell_tabledata(self, moreinfo=False, ual=False, spu=False):
        """
        returns dict of license data for each commcell in the group
            Args:
                moreinfo    (bool)    -- true if More Info needs to be validated

                ual         (bool)    -- true if Usage by and Agents and Licenses needs to be validated

                spu         (bool)    -- true if Subclient Peak Usage needs to be validated

            Returns:
                commcells_data (dict) -- Returns Commcell license summary tables data

        """

        self.navigator.goto_commcells_in_group()
        self.webconsole.wait_till_load_complete()
        list_commells = self.manage_commcells.get_column_values("CommCell Name")
        if self.commcelllist != list_commells:
            self.log.info(f"{self.commcelllist} : {list_commells}")
            raise Exception(f"Group commcells {list_commells} and list provided {self.commcelllist} are different")
        currenturl = self._driver.current_url
        self.lic_summary.group = False
        commcells_data = {}
        for commcell in list_commells:
            self.manage_commcells.access_commcell(commcell)
            self.webconsole.wait_till_load_complete()
            self.dashboard.view_detailed_report("Current Capacity Usage")
            if moreinfo:
                self.lic_summary.access_moreinfo()
                commcells_data[commcell] = self.lic_summary.get_table_data('moreinfo')
            elif ual:
                self.lic_summary.access_moreinfo()
                self.lic_summary.access_usage_by_agents()
                commcells_data[commcell] = self.lic_summary.get_table_data('ual')
            elif spu:
                self.lic_summary.access_subclientpeak()
                commcells_data[commcell] = self.lic_summary.get_table_data('spu')
            else:
                commcells_data[commcell] = self.lic_summary.get_alltables_data()
            self.close_windowhandles()
            self._driver.get(currenturl)
            self.webconsole.wait_till_load_complete()
        return commcells_data

    def generate_summary_and_validate(self, moreinfo=False, ual=False, spu=False):
        """
        generates group and commcell cells license summary data values and validates the values
            Args:
                moreinfo    (bool)    -- true if More Info needs to be validated

                ual         (bool)    -- true if Usage by and Agents and Licenses needs to be validated

                spu         (bool)    -- true if Subclient Peak Usage needs to be validated

            Returns:
                None

        """
        self.lic_summary.group = True
        validate_grp = False
        if moreinfo:
            self.lic_summary.access_moreinfo()
            group_data = self.lic_summary.get_table_data('moreinfo')
            self.close_windowhandles()
            commcells_data = self.get_allindividual_commcell_tabledata(moreinfo=True)
        elif ual:
            self.lic_summary.access_moreinfo()
            self.lic_summary.access_usage_by_agents()
            group_data = self.lic_summary.get_table_data('ual')
            self.close_windowhandles()
            commcells_data = self.get_allindividual_commcell_tabledata(ual=True)
        elif spu:
            self.lic_summary.access_subclientpeak()
            group_data = self.lic_summary.get_table_data('spu')
            self.close_windowhandles()
            commcells_data = self.get_allindividual_commcell_tabledata(spu=True)
        else:
            group_data = self.lic_summary.get_alltables_data()
            commcells_data = self.get_allindividual_commcell_tabledata()
            validate_grp = True
        chartdata = False
        if spu:
            chartdata = True
        self.__validate_allvalues(group_data, commcells_data, chartdata,validate_grp)

    def __validate_allvalues(self, groupdata, commcells_data, chartdata=False, validate_grp=False):
        """
        compares group license summary with individual commcell license summary values
            Args:
                groupdata      (dict)    -- group data values
                commcell_data  (dict)    -- individual commcell data values                
                Chartdata      (bool)    -- True if values are cahrt data
                validate_grp   (bool)    -- True if groupvalues itself needs validation

            Returns:
                dict

        """
        if chartdata:
            group_specificdata, ccsum, licenses, keystocheck = {}, {}, [], {}
            for key, value in groupdata.items():
                licenses.append(key)
                group_specificdata[key] = {}
                ccsum[key] = {}
                keystocheck[key] = []
                for skey, sval in value.items():
                    keystocheck[key].append(skey)
                    ccsum[key][skey] = []
                    group_specificdata[key][skey] = sval[0]['height']

            commcells = list(commcells_data.keys())

            for key, value in commcells_data.items():
                index = commcells.index(key) + 1
                for skey, sval in value.items():
                    for title, data in sval.items():
                        ccsum[skey][title].append(data[index]['height'])

            for key, value in ccsum.items():
                for skey, sval in value.items():
                    ccsum[key][skey] = [float(x) + float(y) for x, y in zip(sval[0], sval[1])]

            for lic in licenses:
                for key in keystocheck[lic]:
                    group = [float(i) for i in group_specificdata[lic][key]]
                    ccval = ccsum[lic][key]
                    if(len(group) == len(ccval) and len(group) == sum(
                            [1 for i, j in zip(group, ccval) if round(float(i), 2) == round(float(j), 2)])):
                        pass
                    else:
                        raise Exception(
                            f"Group chart values {group} and commcells chart values {ccval} are not same for key {key}")
        else:
            for key in groupdata.keys():
                if key == 'commcells':
                    groupcells = groupdata[key]
                    continue
                if not key:
                    continue
                group_specificdata = groupdata[key]
                if not group_specificdata:
                    continue
                keystocheck, grouptotalsold, groupused = [], [], []
                for newk, newv in groupdata[key].items():
                    if newk == 'License':
                        keystocheck = newv
                    if newk in self.lic_summary.column_values:
                        grouptotalsold = newv
                    if newk in self.lic_summary.row_values:
                        groupused = newv
                ccavailable, ccused, cckeys = [], [], []
                for ckey, cvalue in commcells_data.items():
                    for cnewk, cnewv in cvalue[key].items():
                        if cnewk == 'License':
                            cckeys.append(cnewv)
                        if cnewk in self.lic_summary.column_values:
                            ccavailable.append(cnewv)
                        if cnewk in self.lic_summary.row_values:
                            ccused.append(cnewv)
                for ckey in cckeys:
                    if 'Backup' in ckey:
                        ckey[ckey.index('Backup')] = 'Commvault Backup and Recovery'
                    if 'Archive' in ckey:
                        ckey[ckey.index('Archive')] = 'Commvault Backup and Recovery'
            
                convert = lambda xval : xval.split(" ")[0]
                for ckey, value in zip(keystocheck, grouptotalsold):
                    total = 0.0
                    for i in range(len(cckeys)):
                        valuekeys = cckeys[i]
                        indexes = [idx for idx, k in enumerate(valuekeys) if k == ckey]
                        prev = -1
                        # for available quantity if Backup, archieve is same then use only backup quantity.
                        try:
                            if ccavailable:
                                for j in indexes:
                                    if prev == -1:
                                        prev = float(convert(ccavailable[i][j]))
                                    elif prev == float(convert(ccavailable[i][j])):
                                        continue
                                    total += prev
                        except Exception as err:
                            pass
                    if round(float(convert(value)), 2) == round(float(total), 2):
                        continue
                    else:
                        raise Exception(
                            f"Group data {groupdata} values not matched with commcells data {commcells_data}")
            
                for ckey, value in zip(keystocheck, groupused):
                    total = 0.0
                    for i in range(len(cckeys)):
                        valuekeys = cckeys[i]
                        indexes = [idx for idx, k in enumerate(valuekeys) if k == ckey]
                        for j in indexes:
                            total += float(convert(ccused[i][j]))
                    if round(float(convert(value)), 2) == round(float(total), 2):
                        continue
                    else:
                        raise Exception(
                            f"Group data {groupdata} values not matched with commcells data {commcells_data}")
                
                if validate_grp and key in ['capacity','oi']:
                    for ckey, value in zip(keystocheck, grouptotalsold):
                        total = 0.0
                        keys = [ckey + ' Sold (TB)', ckey + ' Sold', ckey]
                        for nkey in keys:            
                            if nkey in groupcells:
                                total = sum([float(val)for val in groupcells[nkey]])
                                if total == float(value):
                                    continue
                                else:
                                    raise Exception(f"values are not matching {groupcells} {grouptotalsold}")
                    for ckey, value in zip(keystocheck, groupused):
                        total = 0.0
                        keys = [ckey + ' Used (TB)', ckey + ' Used', ckey]
                        for nkey in keys:            
                            if nkey in groupcells:
                                total = sum([float(val)for val in groupcells[nkey]])
                                if total == float(value):
                                    continue
                                else:
                                    raise Exception(f"values are not matching {groupcells} {groupused}")
