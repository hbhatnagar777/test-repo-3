# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Regions related operations on various entities

RegionsHelperMain:

edit_region_of_entity()         --  Add or edit the region of an entity

get_region_of_entity()          --  Gets the region associated to the given entity

calculate_region_of_entity()    --  Calculates the region for the given entity

get_client_groups()             --  REturns the list of clientgroup Id's that client is associated to

validate_calculated_region()    --  Checks if the calculated region for an entity is valid

_get_entity_id()                --  Returns the Id of a given entity

_get_region_from_db()           --  Returns teh region Id associated to an entity from DB

_is_nas_client()                --  Checks if given client is a NAS client

validate_backup_destination_region -- checks if calculates backup destination region for an entity is valid

get_region_name                 --  returns the region name

create_overlapping_location_region()    --  creates custom regions with overlapping locations

cleanup()                       --  Deletes regions that has provided marker / string

"""
from cvpysdk.commcell import Commcell
from AutomationUtils import logger, database_helper
import random


class RegionsHelper:
    """ Helper for Regions associated to different commcell entities """

    def __init__(self, commcell_object: Commcell):
        """
        Initializes the Regions helper module
        Args:
            commcell_object     (object) : Commcell object
        """
        self._commcell = commcell_object
        self.log = logger.get_log()
        self.csdb = database_helper.CommServDatabase(self._commcell)
        self._regions = self._commcell.regions

    def _get_entity_id(self, entity_type, entity_name):
        """
         Returns ID of the given entity and it's entitty Type Id
         Args:
             entity_type         (str)   :   Type of the entity
             entity_name          (str)   :   Name of the entity
        """
        if entity_type.upper() == 'CLIENT':
            self.entity_type_id = 3
            entity_id = self._commcell.clients.get(entity_name).client_id
        elif entity_type.upper() == 'CLIENT_GROUP':
            self.entity_type_id = 28
            entity_id = self._commcell.client_groups.get(entity_name).clientgroup_id
        elif entity_type.upper() == 'COMPANY':
            self.entity_type_id = 189
            entity_id = self._commcell.organizations.get(entity_name).organization_id
        elif entity_type.upper() == 'STORAGE_POOL':
            self.entity_type_id = 160
            entity_id = self._commcell.storage_pools.get(entity_name).storage_pool_id
        elif entity_type.upper() == 'MEDIAAGENT':
            self.entity_type_id = 11
            entity_id = self._commcell.media_agents.get(entity_name).media_agent_id
        elif entity_type.upper() == 'COMMCELL':
            self.entity_type_id = 1
            entity_id = self._commcell.commcell_id
        else:
            raise Exception("No Support of Regions on the given entity type")

        return entity_id, self.entity_type_id

    def _get_region_from_db(self, entity_id, entity_type_id, entity_region_type):
        """
        Returns the region ID associated to an entity from DB
        Args:
            entity_id           (list)  :   List of entity IDs
            entity_type_id      (int)   :   Type of the entity
            entity_region_type  (str)   :   Type of the region you want to get for an entity
                                            accepted values: {'WORKLOAD', 'BACKUP'}
        """
        if entity_region_type.upper() == 'BACKUP':
            flag = 1
        elif entity_region_type.upper() == 'WORKLOAD':
            flag = 2
        else:
            raise Exception("Invalid Entity Region Type passed: %s", entity_region_type)

        _query = "select regionId from App_EntityRegionAssoc with(NOLOCK) where entityId = {0} and entityType={1} and flags={2}". \
            format(entity_id, entity_type_id, flag)
        self.csdb.execute(_query)
        region_id = self.csdb.fetch_one_row()[0]
        return 0 if not region_id else int(region_id)

    def edit_region_of_entity(self, entity_type=None, entity_name=None, entity_region_type=None, region_name=None,
                              region_id=None,entity_id=None):
        """
            Add or edit the region of an entity
            Args:
                entity_type         (str)   :   Type of the entity
                                                (eg:    COMMCELL,
                                                        COMPANY,
                                                        CLIENT,
                                                        CLIENT_GROUP,
                                                        MEDIAAGENT,
                                                        STORAGE_POOL, etc
                                                )
                entity_name          (str)   :   Name of the entity

                entity_region_type   (str)   :   Type of the region to edit
                                                eg: (WORKLOAD or BACKUP)

                region_name          (str)   :   Get the Id of given region

                entity_id           (int)   :   ID of teh entity
        """
        if not entity_id:
            entity_id, entity_type_id = self._get_entity_id(entity_type, entity_name)

        if region_id is None and region_name is None:
            region_id = 0
        if region_id is None and region_name is not None:
            region_obj = self._regions.get(region_name)
            region_id = int(region_obj.region_id)

        self.log.info("====================================================================================")
        self.log.info("Setting %s region of the %s : %s to %s", entity_region_type, entity_type, entity_id, region_id)

        self._regions.set_region(entity_type, entity_id, entity_region_type, region_id)
        self.log.info("Set successfully!")

    def get_region_of_entity(self, entity_type=None, entity_name= None,
                             entity_region_type=None, entity_id =None, entity_type_id= None):
        """
        Gets the region associated to the given entity
        Args:
                entity_type         (str)   :   Type of the entity
                                                (eg:    COMMCELL,
                                                        COMPANY,
                                                        CLIENT,
                                                        CLIENT_GROUP,
                                                        MEDIAAGENT,
                                                        STORAGE_POOL, etc
                                                )
                entity_type_id     (int)    :   ID of the entity_type
                entity_name        (str)    :   Name of the entity
                entity_id          (int)    :   ID of the entity
                entity_region_type   (str)  :   Type of the region to edit
                                                eg: (WORKLOAD or BACKUP)

        Returns:
                int     - Id of the region associated to the Entity
        """
        if (not entity_id) and entity_name:
            entity_id, entity_type_id = self._get_entity_id(entity_type, entity_name)

        self.log.info("====================================================================================")
        self.log.info("Getting %s region of %s: %s" %(entity_region_type, entity_type, entity_id))

        if entity_region_type.upper() not in ['BACKUP', 'WORKLOAD']:
            raise Exception("Entity Region type should be either WORKLOAD or BACKUP. Passed value:", entity_region_type)

        region_in_response = self._regions.get_region(entity_type, entity_id, entity_region_type)
        self.log.info('%s Region of %s %s is %s'% (entity_region_type, entity_type, entity_id, region_in_response))

        self.log.info("Validating API response with DB values")
        region_in_db = self._get_region_from_db(entity_id, entity_type_id, entity_region_type)

        if region_in_response != region_in_db and region_in_response != None:
            raise Exception(f"Region received via GET API is {region_in_response}, Associated region in DB is {region_in_db}")
        else:
            self.log.info("Valid!!")

        return (region_in_response)

    def calculate_region_of_entity(self, entity_region_type, entity_type=None,
                                   entity_name=None, entity_id=None):
        """
        Calculates the region for the given entity
        Args:
                entity_type         (str)   :   Type of the entity
                                                (eg:    COMMCELL,
                                                        COMPANY,
                                                        CLIENT,
                                                        CLIENT_GROUP,
                                                        MEDIAAGENT,
                                                        STORAGE_POOL, etc
                                                )
                entity_region_type   (str)  :   Type of the region to edit
                                                eg: (WORKLOAD or BACKUP)

                entity_name        (str)    :   Name of the entity

                entity_id          (int)    :   ID of the entity

        Returns:
                int     - Id of the region associated to the Entity
        """
        self.log.info("====================================================================================")
        self.log.info("Calculating the %s region of the entity", entity_region_type)

        if (not entity_id) and (entity_name is not None):
            entity_id, entity_type_id = self._get_entity_id(entity_type, entity_name)

        if entity_region_type.upper() not in ['BACKUP', 'WORKLOAD']:
            raise Exception("Entity Region type should be either WORKLOAD or BACKUP. Passed value:", entity_region_type)

        region_in_response = self._regions.calculate_region(entity_type, entity_id, entity_region_type)
        self.log.info('Associated %s Region is %s', entity_region_type, region_in_response)
        return int(region_in_response)

    def _is_nas_client(self, entity_name):
        """
        Returns True if given client is a NAS client, else False
        Args:
            entity_name     (str)   --  Name of the given entity

        Returns:
            True if the given entity is a NAS client

            False if the given entity is not a NAS client
        """
        nas_clients = self._commcell.clients.filter_clients_return_displaynames(filter_by="OS", os_type='NAS')
        return True if entity_name in nas_clients else False

    def get_client_groups(self, client_obj):
        """
        Returns the list of client group IDs for a given client
        Args:
            client_obj  (object)  --  Object of a client

        Returns:
            list    - list of clientgroup IDs
        """
        client_groups = client_obj.associated_client_groups
        cg_id = []
        if client_groups:
            for d in client_groups:
                cg_id.append(d.get('clientGroupId'))

            cg_id.sort()
        return cg_id

    def validate_calculated_region(self, entity_type, entity_region_type, entity_name=None,
                                   entity_id=None, entity_type_id=None):
        """
        Calculate region for a physical entity using its geolocation
        Note: since the calculate_region API is removed, so we can calculate and ideal region for a client using this
            function
        Args:
            entity_type         (str)   :   Type of the entity
            entity_region_type  (str)   :   Type of the region to edit
                                                eg: (WORKLOAD or BACKUP)
            entity_name         (str)   :   Name of the entity
            entity_id           (int)   :   Id of an entity
            entity_type_id      (int)   :   Id of the entity Type

        Returns:
                regionId

        Raises:
                for invalid parameters
        """
        self.log.info("====================================================================================")
        self.log.info("Validating the calculated region with expected region")

        if (entity_id is None) and (entity_name is not None):
            entity_id, entity_type_id = self._get_entity_id(entity_type, entity_name)

        if entity_region_type.upper() not in ['BACKUP', 'WORKLOAD']:
            raise Exception("Entity Region type should be either WORKLOAD or BACKUP. Passed value:", entity_region_type)

        if entity_type_id == 3 or entity_type_id == 11:
            client_obj = self._commcell.clients.get(entity_name)
            latitude = client_obj.latitude
            longitude = client_obj.longitude

            if (latitude is not None) and (longitude is not None):
                _query = """select id from App_Region where id =(
                select Top 1 regionId from App_RegionZoneAssoc  where zoneRegionId in (
               select top 1 id from App_Zone order by power((power((latitude - {0}),2))+power((longitude - {1}),2),0.5)))"""\
                    .format(latitude, longitude)
                self.csdb.execute(_query)
                expected_region = int(self.csdb.fetch_one_row()[0])

            elif client_obj.is_vm:
                hyperv_id = client_obj.hyperv_id_of_vm
                expected_region = self._regions.get_region('CLIENT', hyperv_id, 'WORKLOAD')

            elif self._is_nas_client(entity_name):
                self.log.info("Support to be added for getting region from Data access nodes")
                expected_region = 0
            else:
                self.log.info("Given Pseudo client type validation support not added yet")
                expected_region = 0

            if expected_region <= 0:
                client_groups = self.get_client_groups(client_obj)
                if client_groups:
                    for cg in client_groups:
                        expected_region = int(self._get_region_from_db(cg, 28, 'WORKLOAD'))
                        if expected_region > 0:
                            break

                if expected_region <= 0:
                    company_id = client_obj.company_id
                    if company_id > 0:
                        expected_region = int(self._get_region_from_db(company_id, 189, 'WORKLOAD'))
                    else:
                        expected_region = int(self._get_region_from_db(company_id, 1, 'WORKLOAD'))

        else:
            self.log.info("As calculate Region doesn't work for this EntityType, No need of validating it")
            return True


        self.log.info("calculated workload region = %s"%expected_region)
        return expected_region

    def get_VM_client_group(self, VM_name):
        """
        method to get client group id and name associated to VM
        """
        cg= self._commcell.clients.get(VM_name).associated_client_groups
        self._client_group_name = [x["clientGroupName"] for x in cg]
        return  self._client_group_name

    def validate_backup_destination_region(self, calculated_region, plan_name,entity_type, entity_id=None, entity_name=None
                                           , entity_type_id=None):
        """
        validate if the backup destination region is nearest to workload region of client

        """
        self.log.info("====================================================================================")
        self.log.info("Validating the backup destination region")

        if (entity_id is None) and (entity_name is not None):
            entity_id, entity_type_id = self._get_entity_id(entity_type, entity_name)

        plan_regions = self._commcell.plans.get(plan_name).region_id
        temp = ", ".join(map(str,plan_regions))
        if len(plan_regions)>=1:
            if entity_type_id == 3 or entity_type_id == 11:
                client_obj = self._commcell.clients.get(entity_name)
                latitude = client_obj.latitude
                longitude = client_obj.longitude
                if (latitude is not None) and (longitude is not None):
                    _query = """select regionId from App_RegionZoneAssoc where zoneRegionId=(
                     select top 1 id from App_Zone where id in (
                     select zoneRegionId from App_RegionZoneAssoc where regionId in ({0})) 
                     order by power((power((latitude - {1}),2))+power((longitude - {2}),2),0.5))""" \
                        .format(temp, latitude, longitude)
                    self.csdb.execute(_query)
                    result = [int(x[0]) for x in self.csdb.fetch_all_rows()]
                    # creating the frequency dict of the list(result+plan_regions) and then getting the value which has frequency as 2
                    temp={}
                    for i in (plan_regions+result):
                        temp[i]=(plan_regions+result).count(i)
                    if list(temp.values()).count(2) != 1:
                        raise Exception("Regions with overlapping zones are assigned to the plan")
                    else:
                        # expected region is the region with frequency 2
                        expected_region = list(temp.keys())[list(temp.values()).index(2)]
                        self.log.info("Expected region to be assigned is %s"%expected_region)
        else:
            Exception("Validation would work for plans with multiple regions only")

        if calculated_region == expected_region:
            self.log.info("Backup destination region asigned is correct!")
        else:
            self.log.info("Backup destination region asisgned is incorrect, expected region is %s"% expected_region)

        return True

    def get_region_name(self,region_id):
        """ Returns region name when region id is given """
        _query = "select name,displayName from APP_region where id = {}".format(region_id)
        self.csdb.execute(_query)
        return self.csdb.fetch_one_row()

    def get_locations_details(self, locations: list) -> list:
        """
        Method to get the location details from DB
            Args:
                locations   (list)      --      list of locations
        """
        locations_details = []
        locations_str = "'{}'".format("', '".join(map(str, locations)))
        self.csdb.execute(f"select city,state,country,latitude,longitude from app_zone "
                          f"where name in ({locations_str})")
        if self.csdb.rows[0][0] != '':
            for details in self.csdb.rows:
                locations_details.append({'city': details[0],
                                          'state': details[1],
                                          'country': details[2],
                                          'latitude': details[3],
                                          'longitude': details[4]})
        else:
            raise Exception('Invalid location')
        return locations_details

    def create_overlapping_location_region(self, locations: list, count: int) -> list:
        """
        Method to create custom regions with overlapping locations
            Args:
                locations   (list)      --      location to be used for the region
                count       (int)       --      Number of regions to create
        """
        self.log.info(f'Creating {count} regions with overlapping location: {locations}')
        regions = []
        locations_details = self.get_locations_details(locations)
        for _ in range(count):
            region_name = f'overlapping_zones_region_{random.randint(1,10000)}'
            region = self._regions.add(region_name, 'user_created', locations_details)
            regions.append(region.region_name)

        if not regions:
            raise Exception('Failed to create regions.')
        self.log.info(f"Successfully created regions: {regions}")
        return regions

    def cleanup(self, marker: str) -> None:
        """
            Delete regions that has provided marker / string

            Args:
                marker      (str)   --  marker tagged to server groups for deletion

            Returns:
                None
        """
        self._regions.refresh()
        for region in self._regions.all_regions:
            if region.startswith(marker.lower()):
                try:
                    self._regions.delete(region)
                    self.log.info("Deleted region - {0}".format(region))
                except Exception as exp:
                    self.log.error(f"Unable to delete server group {region} due to {str(exp)}")
