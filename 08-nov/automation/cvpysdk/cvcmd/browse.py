"""static

Main File for performing browse operation at subclient Level adn bacupset level.

"""

import datetime
import os
import platform
import subprocess
import traceback
import json
from requests import Response
import xmltodict
import getpass
from entity import Entity


class Browse(Entity):
    """ Class for browse operation """
    def __init__(
            self,
            package_instance,
            commcell_object,
            client_name,
            agent_name,
            backupset_name,
            logger_object,
            tempFolder=''):
        """ Initialize the browse class instance

            Args:
                package_instance   (str)   -- Instance where commvault is installed

                commcell_object (obj)   -- instance of commcell class

                client_name     (str)   -- Client to perform browse on

                agent_name      (str)   -- Agent to perform browse on

                backupset_name  (str)   -- Backupset to be used for browse

                logger_object   (str)   -- Instance of Logger class

        """
        self._LOG = logger_object
        self.live_browse_path = ''
        self.agent_name = agent_name
        self._loggingPath = tempFolder
        super(Browse, self).__init__(
            logger_object=logger_object,
            commcell_object=commcell_object,
            client_name=client_name,
            agent_name=agent_name,
            backupset_name=backupset_name,
            package_instance=package_instance
        )

    def _browse_display_versions(self, browse_dict):
        """
        Method to print the details of different verions of a file
        """
        dflag = 0
        self._LOG.info("Printing details of versions")
        try:
            if browse_dict == ([], {}):  #This is the return for empty browse with -allVersions
                print("Browse versions returned empty. Please ensure that the provided path is correct and that you have the required permissions. If the path contains symbolic link, try with actual path.")
                return dflag
            print("{:<30}\t{:<8}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format('Name', 'Version', 'Size', 'MTime', 'BackupTime', 'Type'))
            print('_ ' * 62)
            print('\n')
            for item in browse_dict[next(iter(browse_dict))]:
                if item['name'] and item.get('deleted',False):
                    item['name']+=' ( Deleted )'
                print("{:<30}\t{:<8}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format(
                    item['name'] or ' ', 
                    item['version'] or ' ', 
                    item['size'] or ' ', 
                    datetime.datetime.strptime(item['modified_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if item['modified_time'] else ' ',
                    datetime.datetime.strptime(item['backup_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if item['backup_time'] else ' ',
                    item['type'] or ' '))
        except Exception as exp:
            browse_display_exception = str(exp)
            self._LOG.error("Exception Raised in Browse Versions Display: %s", browse_display_exception)
            dflag = 1
        finally:
            return dflag

    def _browse_display(self, browse_dict):
        """
        Method to print the details of files in the path
        """
        dflag = 0
        self._LOG.info("Printing details of files")
        try:
            if not browse_dict:
                print("Browse returned empty. Please ensure that the provided path is correct and that you have the required permissions. If the path contains symbolic link, try with actual path.")
                return dflag
            print("{:<30}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format('Name', 'Size', 'MTime', 'BackupTime', 'Type'))
            print('_ ' * 52)
            print('\n')
            for key in browse_dict:
                if browse_dict[key].get('name') and browse_dict[key].get('deleted'):
                    browse_dict[key]['name']+=' ( Deleted )'
                print("{:<30}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format(
                    browse_dict[key]['name'] or ' ',
                    browse_dict[key]['size'] or ' ',
                    datetime.datetime.strptime(browse_dict[key]['modified_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if browse_dict[key]['modified_time'] else ' ',
                    datetime.datetime.strptime(browse_dict[key]['backup_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if browse_dict[key]['backup_time'] else ' ',
                    browse_dict[key]['type'] or ' '))
        except Exception as exp:
            browse_display_exception = str(exp)
            self._LOG.error("Exception Raised in Browse Display : %s", browse_display_exception)
            dflag = 1
        finally:
            return dflag

    def _find_display(self, browse_dict, vsa_guid=""):
        """
        Method to print the details of files in the path
        """
        dflag = 0
        self._LOG.info("Printing details of files")
        try:
            if not browse_dict:
                print("Find returned empty. Please ensure that the provided path is correct and that you have the required permissions. If the path contains symbolic link, try with actual path.")
                return dflag
            print("{:<30}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format('File path', 'Size', 'MTime', 'BackupTime', 'Type'))
            print('_ ' * 52)
            print('\n')
            temp = ''
            for key in browse_dict:
                if vsa_guid:
                    temp_key = key.strip('\\').strip(vsa_guid).replace('\\', '/')
                    temp_key = os.path.dirname(temp_key)
                else:
                    temp_key = os.path.dirname(key)
                if temp != temp_key:
                    print(temp_key)
                    temp = temp_key
                
                if browse_dict[key].get('name') and browse_dict[key].get('deleted'):
                    browse_dict[key]['name']+=' ( Deleted )'
                print("\t{:<30}\t{:<8}\t{:<20}\t{:<20}\t{:<8}".format(
                    browse_dict[key]['name'] or ' ',
                    browse_dict[key]['size'] or ' ',
                    datetime.datetime.strptime(browse_dict[key]['modified_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if browse_dict[key]['modified_time'] else ' ',
                    datetime.datetime.strptime(browse_dict[key]['backup_time'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S") if browse_dict[key]['backup_time'] else ' ',
                    browse_dict[key]['type'] or ' '))
        except Exception as exp:
            browse_display_exception = str(exp)
            self._LOG.error("Exception Raised in Find Display : %s", browse_display_exception)
            dflag = 1
        finally:
            return dflag

    def qlist_browse(
            self,
            operation='Browse',
            subclient_name=None,
            path=None,
            from_time=None,
            to_time=None,
            filters=None,
            vsa_guid="",
            copy_precedence=None,
            **kwargs
    ):
        """
        Performs browse operation using qlist

        Args:

            operation       (str)   --  Operation to be performed
                                            default: 'Browse'

                                            Accepted Values:
                                            1. Browse
                                            2. Find
                                            3. All versions

            subclient_name	(str)	--	Name of the subclient to perform browse on

            path            (str)   --  Path to be browsed

            from_time		(str)	--	From time for the browse operation

            to_time			(str)	--	To time to be set for the browse operation

            filters			(list)	--	List of filter options

            vsa_guid        (str)   --  VSA GUID used to browse VM

            copy_precedence (int)   --  Copy Precedence

        Returns:
            (bool)	--	Returns True if operation is successful

        """
        flag = 0
        input_file = ''
        output_file = ''
        token_file = ''
        backupset_unspecified = False
        show_deleted= kwargs.get('show_deleted',False)

        # Validate from_time and to_time format
        try:
            if from_time:
                datetime.datetime.strptime(from_time, "%Y-%m-%d %H:%M:%S")
            if to_time:
                datetime.datetime.strptime(to_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Invalid datetime format provided in the input, expected format [yyyy-mm-dd hh:mm:ss]")
            return 1

        try:
            # To support relative path passed by user
            path = Entity._get_absolute_path(path, self.live_browse_path)

            if path not in ['/', '\\']:
                path = path.rstrip('/').rstrip('\\')

            options = {
                'path': path,
                'from_time': from_time,
                'to_time': to_time,
                'filters': filters or [],
            }

            os_type = platform.system()

            # For VSA there is no default Backupset, so Entity.backupset can be None if backupset is not passed by user
            if(Entity.backupset != None):
                backupset_name = Entity.backupset.backupset_name
            else:
                backupset_unspecified = True
                backupset_name = str(next(iter(Entity.agent.backupsets.all_backupsets))) # setting backupset_name to first backupset in the dict returned by all_backupsets()
                Entity.backupset =  Entity.agent.backupsets.get(backupset_name)
                self._LOG.info(
                    "Backupset Unspecified, will use %s as a dummy backupset object for creating request options and json",
                    backupset_name
                )
                
            
            if subclient_name:
                if(backupset_unspecified):
                    raise Exception(
                        "Provide backupset that contains subclient : %s using -bk option", subclient_name)
                self._LOG.info(
                    "Verifying whether subclient: %s exists in backupset: %s",
                    subclient_name,
                    backupset_name
                )
                if Entity.backupset.subclients.has_subclient(subclient_name):
                    self._LOG.info("Subclient exists in backupset")
                    options['_subclient_id'] = Entity.backupset.subclients[subclient_name.lower()]['id']
                else:
                    raise Exception(
                        "Given subclient is not present in the backupset, please enter a valid subclient name")
            else:
                self._LOG.info("Proceeding with browse at backupset level : %s", backupset_name)

            if operation.lower() == 'all versions':
                self._LOG.info("Browsing all versions")
                options['operation'] = 'all_versions'
            elif operation.lower() == 'find':
                self._LOG.info("Proceeding with find operation")
                options['operation'] = 'find'
                options['path'] = path + ("\\**\\*" if 'windows' in Entity.client.os_info.lower() else "/**/*")
            else:
                self._LOG.info("Browsing latest version")
                options['operation'] = 'browse'

            if not options['path']:
                options['path'] = '\\'

            self._LOG.info('Browsing path: %s', options['path'])

            if self.agent_name == 'virtual server':
                options['vs_file_browse'] = 'true'
                options['retry_count'] = 0
                options['path'] = '\\{0}{1}'.format(vsa_guid.rstrip("\n"), options['path'].replace('/', '\\'))
                self._LOG.info("VSA Browse path is %s", options['path'])
            
            if copy_precedence:
                options['copy_precedence'] = copy_precedence

            options['show_deleted'] = show_deleted

            options = Entity.backupset._prepare_browse_options(options)
            request_json = Entity.backupset._prepare_browse_json(options)

            request_json['options']['cvcBrowse'] = 1

            if(backupset_unspecified):
                del request_json['entity']['backupsetId']
                del request_json['entity']['subclientId']

            if os_type == 'OS400':
                request_json['options']['cvcBrowse'] = True
                response_flag, response = Entity.commcell._cvpysdk_object.make_request(
                    'POST',
                    Entity.commcell._services['BROWSE'],
                    request_json)
            else:
                # Converting dict to xml for qlist
                request_json = {'databrowse_BrowseRequest': request_json}
                request_xml = xmltodict.unparse(request_json)

                status, installation_path, error = Entity.simpana_default_obj.simpana_installation_path(
                    Entity.package_instance
                )

                if not status:
                    raise Exception(
                        "No local installation present with the specified instance name."
                        " Cannot perform browse\nError: {}".format(error))

                _time = '{date:%m-%d-%Y_%H_%M_%S}'.format(date=datetime.datetime.now())
                _time = '{}_{}'.format(_time, os.getpid())
                if os_type == 'Linux':
                    command = '{}/Base/qlist'.format(installation_path)
                    try:
                        userHomeDir = os.path.expanduser('~')
                        temp_folder = '{}/cvc'.format(userHomeDir)
                        
                        if self._loggingPath: 
                            temp_folder = self._loggingPath
                        elif not userHomeDir or userHomeDir =='/':
                            print("User home directory not found, please specify a path for logging")
                            exit(1)
                              
                        if not os.path.exists(temp_folder):
                            os.makedirs(temp_folder)
                            os.chmod(temp_folder, 0o700)
                    except OSError:
                        temp_folder = os.getcwd()
                        if not os.access(temp_folder, os.W_OK):
                            print('User does not have permission for writing tmp files on /home/{}/cvc or on current working directory, please provide a valid log file path'.format(getpass.getuser()))
                            exit(1)

                    token_file = '{}/token_{}.dat'.format(temp_folder, _time)
                    input_file = '{}/cvc_browse_request_{}.xml'.format(temp_folder, _time)
                    output_file = '{}/cvc_browse_response_{}.xml'.format(temp_folder, _time)

                elif os_type == 'Windows':
                    command = r'{}\Base\qlist'.format(installation_path)

                    try:
                        temp_folder = r'{}\Temp\cvc'.format(installation_path)
                        if not os.path.exists(temp_folder):
                            os.makedirs(temp_folder)
                    except OSError:
                        temp_folder = os.getcwd()
                    token_file = r'{}\token_{}.dat'.format(temp_folder, _time)
                    input_file = r'{}\cvc_browse_request_{}.xml'.format(temp_folder, _time)
                    output_file = r'{}\cvc_browse_response_{}.xml'.format(temp_folder, _time)
                else:
                    raise Exception('OS: {} not supported'.format(os_type))

                self._LOG.debug('Input file: %s', input_file)
                self._LOG.debug('Output file: %s', output_file)

                with open(input_file, 'w') as _file:
                    _file.write(request_xml)
                os.chmod(input_file, 0o600)
                    
                with open(token_file, 'w') as _tfile:
                    _tfile.write(Entity.commcell.auth_token.split(' ')[1])
                os.chmod(token_file, 0o600)

                command = '{} backupfiles -af "{}" -tfPlain "{}" -dpath "{}"'.format(
                    command,
                    input_file,
                    token_file,
                    output_file
                )

                output = subprocess.run(command, shell=True)
                
                if not output.returncode == 0:
                    raise Exception("Browse failed with error: {}".format(output.stderr))
                
                if output_file and os.path.exists(output_file):
                    os.chmod(output_file, 0o600)

                with open(output_file) as _file:
                    content = _file.read()

                # To convert XML to dict
                content = xmltodict.parse(content, attr_prefix='')['OUTPUT']['databrowse_BrowseResponse']
                content = json.loads(json.dumps(content))

                # To convert dict as request response
                response = Response()
                response._content = str({'browseResponses': content}).replace("'", '"').encode()
                response_flag = True

            if operation.lower() == 'all versions':
                browse_dict = Entity.backupset._process_browse_response(response_flag, response, options)

                if browse_dict is not None:
                    flag = self._browse_display_versions(browse_dict)
            else:
                _, browse_dict = Entity.backupset._process_browse_response(response_flag, response, options)

                if browse_dict is not None:
                    if operation.lower() == 'find':
                        flag = self._find_display(browse_dict, vsa_guid)
                    else:
                        flag = self._browse_display(browse_dict)

        except OSError:
            print('User does not have enough permission to create temp files')
            self._LOG.error(
                'User does not have enough permission to create temp files \n Error: %s',
                traceback.format_exc()
            )

        except Exception:
            self._LOG.error("Exception occurred in browse : %s", traceback.format_exc())
            flag = 1

        finally:
            if input_file and os.path.exists(input_file):
                os.remove(input_file)
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
            if token_file and os.path.exists(token_file):
                os.remove(token_file)

            if(backupset_unspecified):
                Entity.backupset = None

            if flag == 0:
                self._LOG.info("Browse job completed successfully")
            else:
                self._LOG.error("Browse job encountered error")
            return flag


