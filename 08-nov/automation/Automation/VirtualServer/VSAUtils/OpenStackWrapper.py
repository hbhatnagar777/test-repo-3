"""Wrapper methods for OpenStack

Endpoints:  All required OpenStack endpoints.



"""
import json


from requests import Session
from AutomationUtils import logger, machine



class OpenStackSDKWrapper():
    """
            Initialization of OpenStackSDKWrapper

            get_openstack_connection()  - Creates open stack connection

            get_cinder_connection()     -Creates cinder connection

            close_openstack_connection()- closes open stack connection

            get_session()               - get the openstack session

            get_creds()                 - gets openstack credentials in json format.

            login()                     - Performs openstack server login

            get_ostack_tokens()         - This mehtod gets the openstack token

            process_post_request()      - Processes the post request

            process_post_request()      - Process the get request

    """

    def __init__(self, servername, username, password, project_name=None, port=None):
        """
        servername              (str) -- OpenstackServer Name
        username                (str) -- OpenStack server user name
        password                  (str) -- OpenStack sever user password
        projectname             (str) -- Openstack project name
        port                    (str) -- OpenStack keystone port to connect

        """
        self.log = logger.get_log()
        self.servername = servername
        self.username = username
        self.password = password
        self.projectName = project_name
        self.auth_url = f"http://{servername}:5000/v3"
        self.username_domain_id = "default"
        self.project_domain_id = "default"
        self._openstack_conn = None


        if port != None:
            self.port = port
        else:
            self.port = self.KEYSTONE_DEFAULT_PORT
        self.connection = None


    ##Required OpenStack endpoints
    KEYSTONE_ENDPOINT_NAME = "keystone"
    NOVA_ENDPOINT_NAME = "nova"
    GLANCE_ENDPOINT_NAME = "glance"
    CINDER_ENDPOINT_NAME = "cinder"
    NEUTRON_ENDPOINT_NAME = "neutron"

    #Project
    DEFAULT_PROJECT = "admin"
    #URL
    AUTH_URL_PREFIX = "http://"
    AUTH_URL_PREFIX_SECURE = "https://"
    AUTH_URL_SUFFIX_V2 = "/v2"
    AUTH_URL_SUFFIX_V20 = "/v2.0"
    AUTH_URL_SUFFIX_V21 = "/v2.1"
    AUTH_URL_SUFFIX_V3 = "/v3"

    #KEYSTONE APIs
    KEYSTONE_DEFAULT_PORT = 5000
    API_KEYSTONE_TENANTS = "/tenants"
    API_KEYSTONE_PROJECTS_V3 = "/projects"
    ## POST APIs
    API_KEYSTONE_TOKENS = "/tokens"
    API_KEYSTONE_TOKENS_V3 = "/auth/tokens"

    #NOVA APIs
    NOVA_DEFAULT_PORT = 8774
    API_NOVA_SERVER_LIST = "/{tenantid}/servers"  # /{tenant_id}/servers
    API_NOVA_SERVER_DETAIL_LIST = "/{tenantid}/servers/detail"  # /{tenant_id}/servers/detail
    API_NOVA_SERVER_ACTION = "/{tenantid}/servers/{serverid}/action"  #

    API_NOVA_AVAILABILITY_ZONE = "/os-availability-zone"  # /{tenant_id}/os-availability-zone

    API_NOVA_ATTACHED_VOLUME_DETAIL = "/servers/%s/os-volume_attachments/%s"  # /{tenant_id}/
    # servers/{server_id}/os-volume_attachments/{attachment_id} */

    API_NOVA_ATTACHED_VOLUME_LIST = "/{tenantid}/servers/{serverid}/os-volume_attachments"
    # /{tenant_id}/servers/{server_id}/os-volume_attachments */

    #CINDER APIs
    CINDER_DEFAULT_PORT = 8776
    API_CINDER_VOLUME_LIST = "/volumes/detail"  # /{tenant_id}/volumes/details
    API_CINDER_VOLUMETYPE = "/types"  # /{tenant_id}/types
    API_CINDER_SNAPSHOT_LIST = "/snapshots"  # /{tenant_id}/snapshots
    API_CINDER_SNAPSHOT_DETAIL_LIST = "/snapshots/detail"  # /{tenant_id}/snapshots/details
    # /v3/{project_id}/types

    #Region API
    API_REGION_LIST = "/regions"  #http://1.1.1.1:5000/v3/regions

    #NEUTRON APIS
    API_DEFAULT_NETWORK_PORT = 9696
    API_NEUTRON_LIST_IPS = "/{tenantid}/servers/{serverid}/ips"
    API_LIST_FLOATING_IPS = "/floatingips"

    HTTP_STATUS_CODES = [200, 201, 202, 203, 204, 205, 206, 206, 207, 208]

    #For now we only support windows platform, as Openstack doesnt have a way to query OS type.
    GUEST_OS = "Windows"
    @property
    def tokenObject(self):
        """
        Get token Object
        :return:
        """
        return self.tokenObj

    @property
    def openstack_conn(self):
        
        """
        Get openstack connection object
        Arg:None
        """
        from openstack import connection
        self._openstack_conn = connection.Connection(auth_url=self.auth_url, project_name=self.projectName,
                                            username=self.username, password=self.password,
                                            user_domain_id=self.username_domain_id,
                                            project_domain_id=self.project_domain_id)
        return self._openstack_conn


    def get_cinder_connection(self):
        
        """
        Creates cinder connection
        Args:None
        return:returns cinder connection object
        """
        from cinderclient import client as cinderclient
        cinder = cinderclient.Client('3', self.username, self.password, self.projectName, self.auth_url)
        return cinder

    @tokenObject.setter
    def tokenObject(self,obj):
        """
        Sets the token object which we get as response from login
        :return:
        """
        self.tokenObj = obj

    def prepare_url(self,server,endpoint,version=None,port=None,prefix=None):
        """Prepares URL with required prefix and keystone version

            Args:
                server   --  OpenStack server name

                endpoint --  Endpoint to execute

                version  --  OpenStack server version

                port     --  Keystone server port if non default port configured

                prefix   --  prefix (default http).

            Returns:
                str    -   returns fully formes url
        """
        try:
            if prefix == None:
                prefix = self.AUTH_URL_PREFIX
            if port == None:
                port = self.KEYSTONE_DEFAULT_PORT
            if version == None:
                version = self.AUTH_URL_SUFFIX_V2

            url = prefix + server + ":" + str(port) + version + endpoint
            #self.log("successfully computed and sending formatted URL {0}".format(url))
            return url
        except Exception as err:
            self.log.exception(
                "An Exception Occurred in preparing URL".format(err))
            return None

    def get_session(self,**kwargs):
        """get session object with args passed in.

            Args:
                kwargs (example)   --  #dHeaders = {"Authtoken":"token","contentType":"application/json"}

            return:
                obj    -   returns Session object
        """
        s = Session()
        if kwargs != None:
            s.headers.update({'Content-Type': 'application/json; charset=utf-8'})
            s.headers.update(kwargs)
            self.log.info("Header content {0}".format(s.headers))
            return s


    @property
    def get_creds(self):
        """get openstack property

            Args:
                None

            return:
                returns the openstack credential in json format
        """
        if self.projectName!=None:
            return  {"auth":{"tenantName":self.projectName,
                            "passwordCredentials":{"username":self.userName,"password":self.passwd}}}

        else:
            return {"auth": {
                             "passwordCredentials": {"username": self.userName, "password": self.passwd}}}



    def login(self):
        """perform openstack login

            Args:
                None

            return:
                returns the GET response of ostack login end point
        """
        try:
            _dcreds = (self.get_creds)
            _url = self.prepare_url(self.serverName,self.API_KEYSTONE_TOKENS,self.AUTH_URL_SUFFIX_V20,self.port,
                                    self.AUTH_URL_PREFIX)

            _session = self.get_session()
            _response = _session.post(_url,data=json.dumps(_dcreds))
            return (_response.status_code,_response.content)
        except Exception as err:
            self.log.exception("Exception occured in openstack server login method ".format(err))

    def get_ostack_tokens(self):
        """get openstack token

            Args:
                None
                None

            return:
                returns the tokens from openstack server login request
        """
        try:
            (status,data) = self.login()
            if status in self.HTTP_STATUS_CODES:
                _parsed_response = json.loads(data)
                self.tokenObj    = _parsed_response["access"]["token"]
                return _parsed_response["access"]["token"] ["id"]

            else:
                self.log.info("Login failure..")
                #self.log("Login request did not succeed got the status code {0}".format(status))
        except Exception as err:
            self.log.exception("Exception occured in get_openstack_tokens method ".format(err))


    
    def process_post_request(self,endpoint,version=None,port=None,headers=None,data=None):
        """get process post request

            Args:
                endpoint    --  Endpoint to be used
                version     --  keystone server version
                port        --  If non default port being used to access openstack server
                headers     --  request headers
                data        --  request payload in json

            return:
                returns the post request response
        """
        try:
            _url = self.prepare_url(self.serverName, endpoint, version, port, self.AUTH_URL_PREFIX)
            _session = self.get_session(**headers)
            if data != None:
                _response = _session.post(_url, data=json.dumps(data))
            else:
                _response = _session.post(_url)

            return (_response.status_code, _response.content)
        except Exception as err:
            self.log.exception("Exception occured in the process_post_request method ".format(err))


    def process_get_request(self,endpoint,version=None,port=None,headers=None,data=None):
        """get process get request

            Args:
                endpoint    --  Endpoint to be used
                version     --  keystone server version
                port        --  If non default port being used to access openstack server
                headers     --  request headers
                data        --  request payload in json

            return:
                returns the get request response
        """
        try:
            _url = self.prepare_url(self.serverName, endpoint, version, port, self.AUTH_URL_PREFIX)
            _session = self.get_session(**headers)
            if data != None:
                _response = _session.get(_url, data=json.dumps(data))
            else:
                _response = _session.get(_url)

            return (_response.status_code, _response.content)
        except Exception as err:
            self.log.exception("Exception occured in process get request method".format(err))



class OpenStackVMops(OpenStackSDKWrapper):
    """
            Initialization of OpenStackVMops

prepare_url()            - prepares the url with port and appropariate prefix
            
            
            
    """
    def __init__(self, server=None, username=None, password=None):
        """
        servername              (str) -- OpenstackServer Name
        username                (str) -- OpenStack server user name
        password                  (str) -- OpenStack sever user password
        projectname             (str) -- Openstack project name
        port                    (str) -- OpenStack keystone port to connect

        """
        super(OpenStackVMops, self).__init__(
            server, username, password, project_name = self.DEFAULT_PROJECT, port = self.KEYSTONE_DEFAULT_PORT)

    def get_instance_list(self):
        """
        Gets all instances in OpenStack server
        Args: None
        return: returns instance as dict
        """
        try:
            servers = self.openstack_conn.compute.servers()
            dict = {}
            for server in servers:
                dict[server.name] = server.id
            return dict
        except Exception as err:
            self.log.exception("Exception occured in getInstance method: " +str(err))
    
    def delete_vm(self,vmname):
        """
        delete instances in OpenStack server
        Args: instancename
        """
        try:
            servers = self.openstack_conn.compute.servers()
            self.openstack_conn.delete_server(vmname)
        except Exception as err:
            self.log.exception("Exception occured in getInstance method: " +str(err))
            
    def set_quota_volume_diff(self,project):
        """
        Gets set instance quota limits for a project if different than current project
        Args: Project name
        return: set instance quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            for key, value in quota.items():
                quota['volumes'] = int((0))
                quota['snapshots'] = int((0))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)
        except Exception as err:
            self.log.error("Exception occured in setvolumequota method: " +str(err))
    
    def delete_volume(self,volumename):
        """
        delete volume for a server
        Args: volumename
        """
        try:
            self.openstack_conn.delete_volume(volumename)
            
        except Exception as err:
            self.log.exception("Exception occured in deleteserver method: " +str(err))
    
    def get_quota_limits(self,project):
        """
        Gets compute quota limits for a project
        Args: Project name
        return: returns quota limits for a project as dict
        """
        try:
            self.openstack_conn.compute.servers()
            quota= self.openstack_conn.get_compute_quotas(project)
            return quota
        except Exception as err:
            self.log.error("Exception occured in getcomputequota method: " +str(err))
    
    def get_volume_limits(self,project):
        """
        Gets volume quota limits for a project
        Args: Project name
        return: returns volume limits for a project as dict
        """
        try:
            quotalimits= self.openstack_conn.get_volume_limits(project)
            return quotalimits
        except Exception as err:
            self.log.error("Exception occured in getvolumequota method: " +str(err))
    
    def set_quota_instance(self,project,vm_name):
        """
        Gets set instance quota limits for a project
        Args: Project name
        return: set instance quota limits for a project 
        """
        try:
            self.openstack_conn.compute.servers()
            quota = self.get_quota_limits(project)
            _listof_instances = self.get_instance_list()
            vmcount = len(_listof_instances)
            for key, value in quota.items():
                quota['instances'] = vmcount
            del quota['id'] 
            
            self.openstack_conn.set_compute_quotas(project,**quota )
        except Exception as err:
            self.log.error("Exception occured in setcomputequota method: " +str(err))
    
    def set_quota_volume_snapshot(self,project):
        """
        sets volume snapshot quota limits for a project
        Args: Project name
        return: set volume snapshot quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            totvolused = self.get_volume_limits(project)
            volsnap = totvolused['absolute']['totalSnapshotsUsed']
            for key, value in quota.items():
                quota['snapshots'] = int((volsnap-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)
        except Exception as err:
            self.log.error("Exception occured in setvolumesnapquota method: " +str(err))
    
    def set_quota_volumesnapshot_size(self,project):
        """
        sets volumesnapshot size quota limits for a project
        Args: Project name
        return: set volume snapshot size quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            totvolused = self.get_volume_limits(project)
            volsnapsize = totvolused['absolute']['totalGigabytesUsed']
            for key, value in quota.items():
                quota['gigabytes'] = int((volsnapsize-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)
        except Exception as err:
            self.log.error("Exception occured in setvolumesnapsizequota method: " +str(err))
            
    def set_quota_volume(self,project):
        """
        Gets set instance quota limits for a project
        Args: Project name
        return: set instance quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            totvolused = self.get_volume_limits(project)
            vol = totvolused['absolute']['totalVolumesUsed']
            for key, value in quota.items():
                quota['volumes'] = int((vol-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)
        except Exception as err:
            self.log.error("Exception occured in setvolumequota method: " +str(err)) 
                  
    def set_boundary_quota_compute(self,project,vm_name):
        """
        Gets set compute boundary quota limits for a project
        Args: Project name, instance name
        return: set compute quota limits for a project 
        """
        try:
            self.openstack_conn.compute.servers()
            quota = self.get_quota_limits(project)
            flavorid = self.get_instace_flavor_id(vm_name)
            #get compute usage of the project
            computeusage = self.openstack_conn.get_compute_usage(project)
            cores= self.openstack_conn.get_flavor_by_id(flavorid)
            vcpus = cores.vcpus
            ramused = computeusage ['total_memory_mb_usage']
            ramsize= self.openstack_conn.get_flavor_by_id(flavorid)
            ram = ramsize.ram
            ram = float(ram)
            _listof_instances = self.get_instance_list()
            vmcount = len(_listof_instances) 
            for key, value in quota.items():
                quota['ram'] = int((ramused +ram))
                quota['cores'] = (vcpus+200)
                quota['instances'] = (vmcount+1)
            del quota['id'] 
            self.openstack_conn.set_compute_quotas(project,**quota )
        except Exception as err:
            self.log.error("Exception occured in setcomputequota method: " +str(err))
    
    def set_boundary_quota_volume(self,project):
        """
        Gets set compute boundary volume limits for a project
        Args: Project name
        return: set compute volume limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            totvolused = self.get_volume_limits(project)
            volused = totvolused['absolute']['totalVolumesUsed']
            volsnap = totvolused['absolute']['totalSnapshotsUsed']
            volsnapsize = totvolused['absolute']['totalGigabytesUsed']
            for key, value in quota.items():
                quota['volumes'] = (volused +10)
                quota['snapshots'] = int((volsnap+10))
                quota['gigabytes'] = int((volsnapsize+5000))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)
        except Exception as err:
            self.log.error("Exception occured in setcomputequota method: " +str(err))
    
    def set_quota_ram(self,project,vm_name):
        """
        Gets set ram quota limits for a project
        Args: Project name ,instance name
        return: set ram quota limits for a project 
        """
        try:
            self.openstack_conn.compute.servers()
            quota = self.get_quota_limits(project)
            flavorid = self.get_instace_flavor_id(vm_name)
            ramsize= self.openstack_conn.get_flavor_by_id(flavorid)
            ram = ramsize.ram
            for key, value in quota.items():
                quota['ram'] = (ram-1)
            del quota['id'] 
            
            self.openstack_conn.set_compute_quotas(project,**quota )
        except Exception as err:
            self.log.error("Exception occured in setcomputequota method: " +str(err))
            
    def set_quota_vcpus(self,project,vm_name):
        """
        Gets set ram quota limits for a project
        Args: Project name ,instance name
        return: set ram quota limits for a project 
        """
        try:
            self.openstack_conn.compute.servers()
            quota = self.get_quota_limits(project)
            flavorid = self.get_instace_flavor_id(vm_name)
            cores= self.openstack_conn.get_flavor_by_id(flavorid)
            vcpus = cores.vcpus
            for key, value in quota.items():
                quota['cores'] = (vcpus-1)
            del quota['id'] 
            
            self.openstack_conn.set_compute_quotas(project,**quota )
        except Exception as err:
            self.log.error("Exception occured in setcomputequota method: " +str(err))
    
    
    
    def reset_quota_limits(self,project):
        """
        Delete quota limits for a project
        Args: Project name
        return: delete quota limits for a project 
        """
        try:
            
            self.openstack_conn.delete_compute_quotas(project)   
        except Exception as err:
            self.log.error("Exception occured in deletecomputequota method: " +str(err))
    
    def reset_volume_limits(self,project):
        """
        Delete quota limits for a project
        Args: Project name
        return: delete quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            for key, value in quota.items():
                quota['volumes'] = int((-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)   
        except Exception as err:
            self.log.error("Exception occured in resetvolumequota method: " +str(err))
    
    def reset_volumesnapshot_limits(self,project):
        """
        Delete quota limits for a project
        Args: Project name
        return: delete quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            for key, value in quota.items():
                quota['snapshots'] = int((-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)   
        except Exception as err:
            self.log.error("Exception occured in resetvolumesnapquota method: " +str(err))
    
    def reset_volumesnapsize_limits(self,project):
        """
        Delete quota limits for a project
        Args: Project name
        return: delete quota limits for a project 
        """
        try:
            quota = self.openstack_conn.get_volume_quotas(project)
            for key, value in quota.items():
                quota['gigabytes'] = int((-1))
            del quota['id']
            self.openstack_conn.set_volume_quotas(project,**quota)   
        except Exception as err:
            self.log.error("Exception occured in resetvolumesnapsizequota method: " +str(err))
    
    def get_zones(self):
        """
        Gets all the VMs in the corresponding zones
        Args:None
        return: returns list of VMs in the corresponding zone
        """
        try:
            servers = self.openstack_conn.compute.servers()
            dict2 = {}
            for server in servers:
                dict2[server.name] = server.availability_zone
            return dict2
        except Exception as err:
            self.log.exception("Exception occurred in get_zones method: " +str(err))

    def get_uuid(self, instanceName):
        """
        Gets UUID of an instance in OpenStack server
        Args: InstanceName
        return:UUID
        """
        try:
            _listof_instances = self.get_instance_list()
            if _listof_instances.keys():
                instance_id = _listof_instances[instanceName]
                return instance_id
        except Exception as err:
            self.log.exception("Exception occured in getUUID method"+str(err))

    def get_instance_details(self, _uuid=None):
        """
        Gets instance details in OpenStack server
        Args : UUID of the instance
        return:instance details
        """
        try:
            servers = self.openstack_conn.compute.servers()
            output = {}
            for server in servers:
                if _uuid == server.id:
                    output["servers"] = servers
                    return output
        except Exception as err:
            self.log.exception("Exception occured in getUUID method:"+str(err))
            
    def get_listsnapshot(self, detailed=True, search_opts=None):
        """
        Gets the list of snapshots
        Args: None
        return:Snapshots
        """
        try:
            snap_list = self.openstack_conn.list_volume_snapshots()
            return snap_list
            
        except Exception as err:
            self.log.exception("Exception occured in setting list of snapshots"+str(err))

    ###Gets the drivelist
    def get_drive_details(self, vmObj):
        try:
            if(vmObj.GuestOS == "Windows"):
                m = machine.Machine(machine_name=vmObj.ip,username=vmObj.user_name,password=vmObj.password)
                out = m.execute_command('Get-PSDrive -PSProvider FileSystem | ?{$_.Used}')
                _drivelist = []
                for _item in out.formatted_output:
                    if len(_item[0]) == 1:
                        _drivelist.append(_item)
                return _drivelist



        except Exception as err:
            self.log.exception("Exception in get_driver_details() %s", str(err))
            return _drivelist
   
    
   
    def poweron_instance(self, _uuid):
        """
        PowerOn the instance

        """
        try:
            flag = False
            dHeaders = {"X-Auth-Token": self.token}
            if _uuid != None:
                _endpoint   =   self.API_NOVA_SERVER_ACTION
                _endpoint   =   _endpoint.replace("{tenantid}",self.tokenObj["tenant"]["id"]) #update tenantId to url
                _endpoint   =   _endpoint.replace("{serverid}",_uuid) #updating instance uuid to the url
                _endpoint   = _endpoint + '?uuid=' + _uuid #append instance UUID to the url
                _body       = {"os-start":"null"}
                (_status,_data)  = self.process_post_request(_endpoint,version=self.AUTH_URL_SUFFIX_V2,
                                                          port=self.NOVA_DEFAULT_PORT,headers=dHeaders,data=_body)

                if _status in self.HTTP_STATUS_CODES:
                    #self.log.info("Started the instance {0} successfully".format(_uuid))
                    self.log.info("Started")
                    flag =  True
                else:
                    #self.log("ERROR: Failed to start the instance ".format(_status))
                    self.log.info("Failed with error {0}".format(_status))
                    flag = False

            else:
                #self.log("ERROR: Couldn't find the server\instance ",_uuid)
                self.log.info("Server not found")
                flag = False
            return flag
        except Exception as err:
            self.log.exception("Exception occured in powerOninstance method".format(err))
            return False

    def poweroff_instance(self, _uuid):
        """
        Poweroff the instance

        """
        try:
            flag = False
            dHeaders = {"X-Auth-Token": self.token}
            if _uuid != None:
                _endpoint   =   self.API_NOVA_SERVER_ACTION
                _endpoint   =   _endpoint.replace("{tenantid}",self.tokenObj["tenant"]["id"]) #update tenantId to url
                _endpoint   =   _endpoint.replace("{serverid}",_uuid) #updating instance uuid to the url
                _endpoint   = _endpoint + '?uuid=' + _uuid #append instance UUID to the url
                _body       = {"os-start":"null"}
                (_status,_data)  = self.process_post_request(_endpoint,version=self.AUTH_URL_SUFFIX_V2,
                                                          port=self.NOVA_DEFAULT_PORT,headers=dHeaders,data=_body)
                if _status in self.HTTP_STATUS_CODES:
                    #self.log("Started the instance {0} successfully".format(_uuid))
                    self.log.info("Stopped")
                    flag = True
                else:
                    #self.log("ERROR: Failed to stop the instance ", _status)
                    self.log.info("Error")
                    flag = False

            else:
                #self.log("ERROR: Couldn't find the server\instance ", _uuid)
                self.log.info("No Server")
                flag = False
            return flag
        except Exception as err:
            self.log.exception("Exception occured in poweroffInstance ".format(err))
            return flag

    
    def get_volume_attachments(self, _uuid=None):
        """
        Gets the list of volumes attached to the server or instance
        param _uuid: uuid of the openstack instance
        return: list of dictionary of volume attachments
        """
        try:
            cinder = self.get_cinder_connection()
            volumelist = []
            for value in cinder.volumes.list():
                if value.attachments and value.attachments[0]['server_id'] == _uuid:
                    volumelist.append(value.__dict__)                  
            return volumelist
        except Exception as err:
            self.log.exception("Exception occured in getVolumeattachments() "+str(err))
    
    def get_instace_flavor_id(self,vm_name):
        """
        Gets the flavor id of the instance

        param : name of the instance.
        return: flavor id of vm

        """
        try:
            servers = self.openstack_conn.compute.servers()
            for server in servers:
                if vm_name == server.name:
                    if 'id' in server.flavor:
                        vmflavorid = server.flavor['id']
                        return vmflavorid
        except Exception as err:
            self.log.exception("Exception occured in vmflavorid() "+str(err))
            
    def get_vmflavor(self,vm_name):
        
        """
        Gets the flavor  of the instance

        param : name of the instance.
        return: flavor of vm

        """
        try:
            flavorid = self.get_instace_flavor_id(vm_name)
            if flavorid != None and flavorid != '':
                vmflavorname= self.openstack_conn.get_flavor_by_id(flavorid)
                vmflavor = vmflavorname.name
                return vmflavor
            else:
                servers = self.openstack_conn.compute.servers()
                for server in servers:
                    if server.metadata != {}:
                        vmflavor = server.flavor['original_name']
                        if vm_name == server.name:
                            return vmflavor
        except Exception as err:
            self.log.exception("Exception occured in getvmflavor() "+str(err))





    def deleteInstance(self):
        pass


    def get_volume_types(self):
        """
        Gets the list of all volume types in openstack server

        param None:
        return: list of dicitonary of volume types

        """
        try:
            dHeaders = {"X-Auth-Token": self.token}

            _endpoint   =   self.API_CINDER_VOLUMETYPE
            _endpoint   =   "/"+self.tokenObj["tenant"]["id"]+ _endpoint #Format {tenantId}/Types

            (_status,_data)  = self.process_get_request(_endpoint,version=self.AUTH_URL_SUFFIX_V2,
                                                             port=self.CINDER_DEFAULT_PORT,headers=dHeaders)
            _data = json.loads(_data)
            if _status in self.HTTP_STATUS_CODES:
                return _data["volume_types"]

            else:
                self.log.info("ERROR: Failed to get the volume types ", _status)

        except Exception as err:
            self.log.exception("Exception occured in getVolumeTypes() ".format(err))


    def get_volume_detail(self):
        """
        Gets the list of all volume types in openstack server

        param None:
        return: list of dicitonary of volume types

        """
        try:
            cinder = self.get_cinder_connection()
            volumelist = []
            for value in cinder.volumes.list():
                volumelist.append(value.__dict__)              

            return volumelist
            dHeaders = {"X-Auth-Token": self.token}

            _endpoint = self.API_CINDER_VOLUME_LIST
            _endpoint = "/"+self.tokenObj["tenant"]["id"]+ _endpoint #Format {tenantId}/Types

            (_status,_data) = self.process_get_request(_endpoint, version=self.AUTH_URL_SUFFIX_V2,
                                                             port=self.CINDER_DEFAULT_PORT, headers=dHeaders)
            _data = json.loads(_data)
            if _status in self.HTTP_STATUS_CODES:
                return _data["volumes"]

            else:
                    self.log.error("ERROR: Failed to get the getVolumedetail ", _status)

        except Exception as err:
            self.log.exception("Exception occured in getVolumedetail() ".format(err))


    def get_volume_typefromAZ(self,AZ):
        """
        Gets the volume from Availabilityzone

        param None: AZ (availablity zone instring)
        return: list of volumeTypes matching AZ

        """
        try:
            _vollist = self.get_volume_detail()
            _volType = []
            if len(_vollist) > 0:
                for _vol in _vollist:
                    if(_vol["availability_zone"] == AZ):
                        _volType.append( _vol["volume_type"])

            else:
                self.log.exception("ERROR: Failed to get the volume type ")

            return _volType
        except Exception as err:
            self.log.exception("Exception occured in getVolumeTypefromAZ() ".format(err))
    
    def get_ram(self,vm_name):
        
        """
        Gets the Ram size of the instance

        param : name of the instance.
        return: ram size
        """
        try:
            flavorid = self.get_instace_flavor_id(vm_name)
            if flavorid != None and flavorid != '':
                ramsize= self.openstack_conn.get_flavor_by_id(flavorid)
                ram = ramsize.ram
                return ram
            else:
                servers = self.openstack_conn.compute.servers()
                for server in servers:
                    if server.metadata != {}:
                        ram = server.flavor['ram']
                        if vm_name == server.name:
                            return ram
        except Exception as err:
            self.log.exception("Exception occured in getram() "+str(err))


    def get_volume_typefrom_volid(self,VolId):
        """
        Gets the volume type info from volume ID(GUID)

        param : Volume ID of each attached volume to openstack instance(server).
        return: volType in str format

        """
        try:
            _vollist = self.get_volume_detail()
            _volType = []
            if len(_vollist) > 0:
                for _vol in _vollist:
                    for _vol_attachment_detail in _vol["attachments"]:
                        if(_vol_attachment_detail["volume_id"] == VolId):
                            _volType =  _vol["volume_type"]

            else:
                self.log.exception("ERROR: Failed to get the volume type ")

            return _volType
        except Exception as err:
            self.log.exception("Exception occured in get_volume_typefrom_volid() ".format(err))


    def get_os_type(self,vm_name):
        """
        Gets the OS type of the instance

        param : name of the instance.
        return: string OS type

        """
        try:
            
            servers = self.openstack_conn.compute.servers()
            for server in servers:
                if server.metadata != {}:
                    if vm_name == server.name:
                        osType = server.metadata['os_type']
                        return osType
                
            
        except Exception as err:
            self.log.exception("Exception occured in getOSType() "+str(err))
    
    def get_vcpus(self,vm_name):
        
        """
        Gets the vcpus type of the instance

        param : name of the instance.
        return: string no of vcpus

        """
        try:
            flavorid = self.get_instace_flavor_id(vm_name)
            if flavorid != None and flavorid != '':
                getvcpus= self.openstack_conn.get_flavor_by_id(flavorid)
                vcpus = getvcpus.vcpus
                return vcpus
            else:
                servers = self.openstack_conn.compute.servers()
                for server in servers:
                    if server.metadata != {}:
                        vcpus = server.flavor['vcpus']
                        if vm_name == server.name:
                            return vcpus
        except Exception as err:
            self.log.exception("Exception occured in getvcpus() "+str(err))


    def get_region(self):
        """
        Gets the OS type of the instance

        param : get region
        return: region_id

        """
        try:
            for endpoints in self.openstack_conn.identity.endpoints():
                return endpoints['region_id']
        except Exception as err:
            self.log.exception("unable to retrive region id () "+str(err))
            raise Exception

    def get_cpu(self, _uuid):
        """
        :param _uuid: UUID of the instance
        :return:
        """
        try:
            dHeaders = {"X-Auth-Token": self.token}
            if _uuid != None:
                 #Prepare URL
                _endpoint       =  self.API_NOVA_SERVER_LIST
                _endpoint       = _endpoint.replace("{tenantid}",self.tokenObj["tenant"]["id"])
                _endpoint       =   _endpoint + '/' + _uuid #append instance UUID to the url
                (_status,_data) =   self.process_get_request(_endpoint,version=self.AUTH_URL_SUFFIX_V2,
                                                             port=self.NOVA_DEFAULT_PORT,headers=dHeaders)

                if _status in self.HTTP_STATUS_CODES:
                    self.log.info("Details of the get cpu {0} fetched successfully".format(_uuid))
                    parsed_response = json.loads(_data)
                    return parsed_response

                else:
                    self.log.info("ERROR: Failed to list floating ips ", _status)
                    return None
        except Exception as err:
             self.log.exception("Exception occcured in floating_ips() %s",str(err))
    
    
    
    def add_floating_ip (self,server_name, wait=False, timeout=60, reuse=True):
        """Assigns floating IP for Instance
            Args: Server_name
            Returns: None
        """
        servers = self.openstack_conn.compute.servers()
        server_details = {}
        for server in servers:
            if server.name == server_name:
                server_details['name'] = server.name
                server_details['id'] = server.id
                server_details['addresses'] = server.addresses
                server_details['interface_ip'] = ''

                self.openstack_conn.add_auto_ip(server_details,wait, timeout, reuse)

    def detach_and_delete_volume(self,destvm_guid, server_details, volume_details):
        """Detaches the attached volume to existing Instance
                    Args: Volume details
                    Returns: None
                """
        servers = self.openstack_conn.compute.servers()
        server_details['id'] = destvm_guid
        for eachvol in volume_details:
            self.openstack_conn.detach_volume(server_details, eachvol)
            self.openstack_conn.delete_volume(eachvol['id'])
        
#         for server in servers:
#             server_details['id'] = server.id
#         self.openstack_conn.detach_volume(server_details, volume_details[0])
#         self.openstack_conn.delete_volume(volume_details[0]['id'])
    def get_all_ips(self, server_id, wait=False, timeout=60, reuse=True):

        servers = self.openstack_conn.compute.servers()
        all_ips = {}
        for server in servers:
            if server.id == server_id:
                all_ips['addresses'] = server.addresses
                all_ips['id'] = server.id
                all_ips['private_network'] = server.addresses['private_network']
                return all_ips['addresses']


    def get_floating_ips(self):
        try:
             #Prepare URL
            dHeaders = {"X-Auth-Token": self.token}
            _endpoint       =  self.API_LIST_FLOATING_IPS
            (_status,_data) =   self.process_get_request(_endpoint,version=self.AUTH_URL_SUFFIX_V20,
                                                             port=self.API_DEFAULT_NETWORK_PORT,headers=dHeaders)
            if _status in self.HTTP_STATUS_CODES:
                self.log.info("Details of the floaingips")
                parsed_response = json.loads(_data)
                return parsed_response
            else:
                self.log.info("ERROR: Failed to floatin ips list ", _status)
                return None

        except Exception as err:
            self.log.exception("Exception in get_float_ips() %s", str(err))

    
    def associate_floating_ips(self, uuid, floating_ip):
        try:
            _ip = floating_ip["floating_ip_address"]
            body = {"addFloatingIp" : {
                             "address":_ip
                            }
            }
             # API_NOVA_SERVER_ACTION  = "/{tenantid}/servers/{serverid}/action"
            dHeaders = {"X-Auth-Token": self.token}
            _endpoint       =  self.API_NOVA_SERVER_ACTION
            _endpoint       = _endpoint.replace("{tenantid}",self.tokenObj["tenant"]["id"])
            _endpoint       =   _endpoint.replace("{serverid}",uuid)
            (_status,_data) =   self.process_post_request(_endpoint,version=self.AUTH_URL_SUFFIX_V21,
                                                             port=self.NOVA_DEFAULT_PORT,headers=dHeaders, data= body)
            if _status in self.HTTP_STATUS_CODES:
                self.log.info("Details of the floaingips")
                return _ip
            else:
                self.log.info("ERROR: Failed to floatin ips list ", _status)
                return None
        except Exception as err:
            self.log.exception("Exception in associate_floating_ips() %s", str(err))
            return None
    
    
    def get_tenant(self):
        try:
            return self.tokenObj["tenant"]["id"]
        except Exception as err:
            self.log.exception("Exception in get_tenant %s", str(err))
