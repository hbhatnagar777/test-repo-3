from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.AdminConsolePages.network_store import NetworkStore
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import PanelInfo
from AutomationUtils.machine import Machine

class NetworkStoreHelper:
    """Helper class for network store page"""

    def __init__(self, admin_console):

        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.log = self.__admin_console.log
        self.__table = Rtable(self.__admin_console)

        self._network_store_obj = NetworkStore(self.__admin_console)
        self._network_store_name = None
        self._nfs_server = None
        self._plan = None
        self.__admin_console.load_properties(self)

    @property
    def network_store_name(self):
        """Method to get network store name"""
        return self._network_store_name

    @network_store_name.setter
    def network_store_name(self, value):
        """Method to set the network store name"""
        self._network_store_name = value

    @property
    def nfs_server(self):
        """Method to get nfs server"""
        return self._nfs_server

    @nfs_server.setter
    def nfs_server(self, value):
        """Method to set nfs server"""
        self._nfs_server = value

    @property
    def plan(self):
        """Method to get plan associated with network store"""
        return self._plan

    @plan.setter
    def plan(self, value):
        """Method to set plan to associate with network store"""
        self._plan = value

    def navigate_to_network_store(self):
        """Method to navigate to network stores page"""

        self.__navigator.navigate_to_infrastructure()
        self.__admin_console.access_tile("tileMenuSelection_networkStore")

    def create_network_store(self,commcell,cache_path=None,idx_path=None):
        """Method to create network store"""

        self.navigate_to_network_store()
        nfs_server_machine = Machine(machine_name=self.nfs_server,commcell_object=commcell)

        if nfs_server_machine.os_info.lower() == 'windows':
            protocol = "SMB"
        else:
            protocol = "NFS"
        
        if cache_path and nfs_server_machine.check_directory_exists(cache_path):
            nfs_server_machine.clear_folder_content(cache_path)
        elif cache_path :
            nfs_server_machine.create_directory(cache_path)
        
        if idx_path and  nfs_server_machine.check_directory_exists(idx_path):
            nfs_server_machine.clear_folder_content(idx_path)
        elif idx_path :
            nfs_server_machine.create_directory(idx_path)

        self._network_store_obj.add_network_store(self.network_store_name,
                                                  [self.nfs_server],
                                                  [self.plan],
                                                  [protocol],cache_path,
                                                  idx_path)

    def remove_network_store(self):
        """Method to delete network store"""

        self.navigate_to_network_store()
        self._network_store_obj.delete_network_store(self.network_store_name)

    def validate_network_store_creation(self):
        """Method to confirm if the network store is created with given details"""

        self.navigate_to_network_store()
        self.__table.apply_filter_over_column(self.__admin_console.props['label.networkStore.store'], self.network_store_name)
        network_store_details = self.__table.get_table_data()

        expected_details = {
            "Hybrid file store": self.network_store_name,
            # "Status": "Ready", # we had removed it from listing page from sp29
            "Plan": self.plan,
            "File server": self.nfs_server
        }

        for key, value in expected_details.items():
            if value == network_store_details[key][0]:
                self.log.info(f"Expected value for {key} matches displayed value")
            else:
                raise Exception(f"Expected value for {key} does not match displayed value")

    def validate_delete(self):
        """Method to verify if network store has been deleted"""

        self.navigate_to_network_store()
        self.__table.apply_filter_over_column(self.__admin_console.props['label.networkStore.store'], self.network_store_name)
        if self.__admin_console.check_if_entity_exists("link", self.network_store_name):
            raise Exception(f"Network store {self.network_store_name} not deleted successfully")
        else:
            self.log.info(f"Network store {self.network_store_name} deleted successfully")

    def validate_general_tile(self,hfs_helper_obj):
        """Method to verify general tile settings

        Args:
            hfs_helper_obj (obj): NFSServerHelper object 
        """
        panel = PanelInfo(self.__admin_console, 'General').get_details()
        backend_data = hfs_helper_obj.show_nfs_objectstore(self.network_store_name)

        general_tile_data = {'Mount path':backend_data['Share path to mount'].split(':')[1],
                            'File server':backend_data['ObjectStore Server'],
                            'Allowed network clients':backend_data['Allowed clients'],
                            'Access type':backend_data['Access Permission'],
                            'Squash type':backend_data['Squash Type'],
                            'Supported protocols':backend_data['Supported Protocols']
                            }
        unmatched_field = []
        for key in general_tile_data:
            if general_tile_data[key] == panel[key] :
                self.log.info(f"Expected value for {key} matches displayed value")
            else:
                self.log.error(f"Expected value for {key} didn't matched displayed value {panel[key]}")
                unmatched_field.append({key,panel[key]})
        if unmatched_field:
            CVWebAutomationException(f"Expected value for one or multiple keys didn't matched displayed value")

    def validate_retention_tile(self,hfs_helper_obj):
        """Method to verify retention tile settings

        Args:
            hfs_helper_obj (obj): NFSServerHelper object 
        """
        panel = PanelInfo(self.__admin_console, 'Retention').get_details()
        backend_data = hfs_helper_obj.show_nfs_objectstore(self.network_store_name)

        retention_tile = {
                        'Version Interval':int(backend_data['Version Interval']),
                        'Number of older versions to retain':int(backend_data['Retention Max Versions'].replace(':','')),
                        'Retention period for deleted files' :int(backend_data['Retention Deleted Item Days'].replace(':','')),
                        'Retention period for older versions':int(backend_data['Retention Max Days'].replace(':',''))
                        }
        panel_info = {
                        'Version Interval':int(panel['Version interval'].replace(' Minutes','')),
                        'Number of older versions to retain':int(panel['Number of older versions to retain']) + 1,
                        'Retention period for deleted files': self.__convert_in_days(panel['Retention period for deleted files']),
                        'Retention period for older versions':self.__convert_in_days(panel['Retention period for older versions'])
                     }
        for key in retention_tile:
            if retention_tile[key] == panel_info[key]:
                self.log.info(f"Expected value for {key} matches displayed value")
            else:
                CVWebAutomationException(f"Expected value for {key} didn't matched displayed value {panel_info[key]}")


    def __convert_in_days(self,time):
        """Converting all time in days

        Args:
            time (string): any time in days
        """
        days_dict = {'days':1,'weeks':7,'months':30,'years':365}
        if time.split()[1].lower() not in days_dict:
            CVWebAutomationException('Time not correct')
        new_time = int(time.split()[0])*days_dict[time.split()[1].lower()]
        return new_time

    def add_pit_view(self,date_time,name=None,allowed_network_client=None):
        """This method is for creating PIT view in HFS

        Args:
            date_time (str): this object is gets the string format of date time.
            name (str, optional): name of PIT. Defaults to None.
            allowed_network_client (str, optional): comma seperated Allowed clients. Defaults to None.
        """
        self.navigate_to_network_store()
        self._network_store_obj.access_hfs(self.network_store_name)
        self._network_store_obj.add_pit_view(date_time,name,allowed_network_client)

    def delete_pit_view(self,name):
        """This method will delete the point in time restore.

        Args:
            name (str): name of PIT view.
        """
        self.navigate_to_network_store()
        self._network_store_obj.access_hfs(self.network_store_name)
        self._network_store_obj.delete_pit_view(name)
    def edit_general_tile(self,general_settings):
        """This function is used to edit the general tile info for the HFS client

        Args:
            general_settings (dict): the key value pair for the props you want to change
        """
        self.navigate_to_network_store()
        self._network_store_obj.access_hfs(self.network_store_name)
        self._network_store_obj.edit_general_settings(general_settings)

    def edit_retention_settings(self,retention_settings):
        """This function is used to edit retention tile info for the HFS client

        Args:
            general_settings (dict): the key value pair for the props you want to change
        """
        self.navigate_to_network_store()
        self._network_store_obj.access_hfs(self.network_store_name)
        self._network_store_obj.edit_retention_settings(retention_settings)
