# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Other SDK generations for commvault"""

import json, enum, os
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from abc import abstractmethod
from shutil import copyfile

class operation(enum.Enum):
    GENERATE ="generate"
    RUN ="run"
    PACK = "pack"
    BUILD ="build"
    INSTALL ="install"


class Generator:
    """
    Base class for Generating SDK based on language

    Methods:
        prepare_swagger_json  -- prepares the swagger JSON for SDK to eb generated
        Factory               -- Create a Factory Object for SDK generator
    """
    def __init__(self,
                 commcell_object,
                 input_file_location):

        self.commcell_object = commcell_object
        self.input_file_location = input_file_location
        self.controller = Machine()
        self.log = logger.get_log()
        if not self.controller.check_file_exists(self.input_file_location):
            self.prepare_swagger_json()
        self.base_cmd = "autorest "

    @property
    def swagger_url(self):
        _services = self.commcell_object._services
        return _services['GET_SWAGGER']

    def set_output_folder(self, postfix):
        """
        Generate output folder path and create folder if not exist
        Args:
            postfix:    (str) - Postfix for output folder path

        Returns:
            Outout_folder (str) - Path of the output folder

        """
        output_folder = self.controller.join_path(self.cmd_line_args['output_folder'], postfix)
        if not self.controller.check_directory_exists(output_folder):
            self.controller.create_directory(output_folder)
        return output_folder

    def prepare_swagger_json(self):
        """
        Prepare the swagger JSON for Generator to use
        Returns:

        """
        flag, response = self.commcell_object._cvpysdk_object.make_request("GET", self.swagger_url)
        json_object = json.dumps(response.json(), indent=2)
        self.log.info("Response json is {0}".format(json_object))
        with open(self.input_file_location, "w") as swagger:
            swagger.write(json_object)

    def _process_output(self, result, operation=operation.GENERATE):
        """
        Process the output of the autorest sdk genration
        Args:
            result: (str)    -- Result fo Execute Command

        Returns:
            Raise exception in failure
        """

        if operation == operation.GENERATE:
            if "Complete" in result.output:
                self.log.info("{0} sdk generation is successul {1}".format(self.language, result.output))
            else:
                self.log.error("Failed to Generate {0} SDK {1}".format(self.language, result.output))
                raise Exception("Failed To generate {0} SDK , Please check logs".format(self.language))

        elif operation == operation.RUN:
            if "isolated process" in result.output:
                self.log.info("{0} sdk run is successul {1}".format(self.language, result.output))
            else:
                self.log.error("Failed to run {0} SDK {1}".format(self.language, result.output))
                raise Exception("Failed To run {0} SDK , Please check logs".format(self.language))

        elif operation == operation.INSTALL:
            if "Imported" in result.output:
                self.log.info("{0} sdk import is successul {1}".format(self.language, result.output))
            else:
                self.log.error("Failed to install {0} SDK {1}".format(self.language, result.output))
                raise Exception("Failed To install {0} SDK , Please check logs".format(self.language))

        elif operation == operation.PACK:
            if "created package" in result.output:
                self.log.info("{0} sdk compilation is successul {1}".format(self.language, result.output))
            else:
                self.log.error("Failed to compile {0} SDK {1}".format(self.language, result.output))
                raise Exception("Failed To compile {0} SDK , Please check logs".format(self.language))

        elif operation == operation.INSTALL:
            if "created package" in result.output:
                self.log.info("{0} sdk compilation is successul {1}".format(self.language, result.output))
            else:
                self.log.error("Failed to compile {0} SDK {1}".format(self.language, result.output))
                raise Exception("Failed To compile {0} SDK , Please check logs".format(self.language))

    @abstractmethod
    def generate(self, **kwargs):
        """
        generates the SDK
        Args:
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """
        self.log.info("Generating the SDK ")


class PowershellGenerator(Generator):
    """
    Generates SDK for Powershell

    Methods:
        generate  -- Generate the powershell SDK
    """

    def __init__(self, commcell_object, input_file_location):
        super(PowershellGenerator, self).__init__(commcell_object, input_file_location)
        self.language = "Powershell"
        self.cmd_line_args ={
            "namespace": "Commvault.API",
            "clear_output_folder": True,
            "output_folder": None,
            "powershell": True,
            "input_file": self.input_file_location
        }
        dirname, filename = os.path.split(os.path.abspath(__file__))
        self.custom_folder ="{0}\\custom".format(dirname)

    def generate(self, **kwargs):
        """
        Generate the Powershell SDK in the path specified
        Args:
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """
        try:
            self.base_cmd = self.base_cmd + " {0}".format(kwargs.get("powershell_configuration_file"))
            kwargs['powershell_configuration_file'] = None
            for key, value in kwargs.items():
                self.cmd_line_args[key] = value

            self.cmd_line_args['output_folder'] = self.set_output_folder("PowershellSDK")

            self.log.info(("Generating powershell SDK in location %s".format(self.cmd_line_args['output_folder'])))
            for key, value in self.cmd_line_args.items():
                if value:
                    temp_key = key.replace("_" , "-")
                    if isinstance(value, str):
                        self.base_cmd = self.base_cmd+"  --"+temp_key+f'="{value}"'
                    else:
                        self.base_cmd = self.base_cmd + "  --" + temp_key

            self.log.info("Deleted and Created disrectory {0}".format(self.cmd_line_args['output_folder']))
            self.controller.remove_directory(self.cmd_line_args['output_folder'])
            self.controller.create_directory(self.cmd_line_args['output_folder'])
            self.log.info("Base Command to be executed is {0}".format(self.base_cmd))
            result = self.controller.execute_command(self.base_cmd)
            self._process_output(result)
            self.controller.copy_folder(self.custom_folder, self.cmd_line_args['output_folder'])

        except Exception as err:
            self.log.info("An exception {0} occurred in generating the SDK".format(err))
            raise err

    def build_module(self, **kwargs):
        """
                run the Powershell SDK in the path specified
                Args:
                    language (str) - Language of SDK needs to be generated
                                        Powershell, Go
                    **kwargs:  - List of inouts need to be passed for SK generation
                Returns:
                    Raise exceltion on failure

                """
        try:
            self.run_command = r"pwsh {0}\\build-module.ps1".format(self.cmd_line_args['output_folder'])
            self.log.info(("running  powershell SDK in location %s".format(self.cmd_line_args['output_folder'])))
            self.log.info("Base Command to be executed is %s" % self.run_command)
            result = self.controller.execute_command(self.run_command)
            self._process_output(result, operation.BUILD)

        except Exception as err:
            self.log.info("An exception {0} occurred in running the SDK".format(err))
            raise err

    def pack_module(self, **kwargs):
        """
        pack the Powershell SDK in the path specified
        Args:
            language (str) - Language of SDK needs to be generated
                                Powershell, Go
            **kwargs:  - List of inouts need to be passed for SK generation
        Returns:
            Raise exceltion on failure

        """
        try:
            self.log.info("copying the nuspec file from custom to base ")
            nuspec_file = "{0}\\custom\\CommvaultRestApi.NUSPEC".format(self.cmd_line_args['output_folder'])
            custom_folder = "{0}\\custom".format(self.cmd_line_args['output_folder'])
            self.controller.copy_from_local(nuspec_file, self.cmd_line_args['output_folder'])
            self.pack_command = r"pwsh {0}\\pack-module.ps1".format(self.cmd_line_args['output_folder'])
            self.log.info(("packing  powershell SDK in location %s".format(self.cmd_line_args['output_folder'])))
            self.log.info("Base Command to be executed is %s" % self.pack_command)
            result = self.controller.execute_command(self.pack_command)
            self._process_output(result, operation.PACK)
            dirname, filename = os.path.split(os.path.abspath(__file__))
            install_file = "{0}\\InstallCVModule-Auto.ps1".format(dirname)
            self.controller.copy_from_local(install_file, self.cmd_line_args['output_folder'])
            self.log.info("copied install file {0} to custom folder {1}".format(install_file, self.cmd_line_args['output_folder']))
            script_path = "{0}\\InstallCVModule-Auto.ps1".format(self.cmd_line_args['output_folder'])
            data = dict()
            data["ps_path"] = self.cmd_line_args['output_folder']
            self.controller.is_commvault_client = False
            result = self.controller.execute_script(script_path, data=data)
            self._process_output(result, operation.INSTALL)
            self.log.info("getting command list")
            list_command = "Powershell Get-Command -Module CommvaultRestApi"
            result = self.controller.execute_command(list_command)
            file_name = r"{0}\\CommvaultPSModule.txt".format(self.cmd_line_args['output_folder'])
            file_obj = open(file_name, 'w')
            file_obj.write(result.output)

        except Exception as err:
            self.log.info("An exception {0} occurred in packing the SDK".format(err))
            raise err



class GOSDKGenerator(Generator):
    """
    Generates SDK for Powershell

    Methods:
        generate  -- Generate the powershell SDK
    """

    def __init__(self, commcell_object, file_location):
        super(GOSDKGenerator, self).__init__(commcell_object, file_location)
        self.language = "Go"
        self.cmd_line_args ={
            "clear_output_folder": True,
            "output_folder": self.controller.join_path("C:\SDK", "GOSDK"),
            "input_file": self.input_file_location,
            "go": True,
            "v3": True
        }

    def generate(self, **kwargs):
        """
        Generate the GO SDK in the path specified
        Args:
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """
        try:
            self.base_cmd = self.base_cmd + " {0}".format(
                kwargs.get("go_configuration_file"))
            kwargs['go_configuration_file'] = None
            for key, value in kwargs.items():
                self.cmd_line_args[key] = value

            self.cmd_line_args['output_folder'] = self.set_output_folder("GoSDK")

            self.log.info(("Generating GO SDK in location %s".format(self.cmd_line_args['output_folder'])))
            for key, value in self.cmd_line_args.items():
                if value:
                    temp_key = key.replace("_", "-")
                    if isinstance(value, str):
                        self.base_cmd = self.base_cmd+"  --"+temp_key+"='{0}'".format(value)
                    else:
                        self.base_cmd = self.base_cmd + "  --" + temp_key

            self.log.info("Base Command to be executed is %s" % self.base_cmd)
            result = self.controller.execute_command(self.base_cmd)
            self._process_output(result)

        except Exception as err:
            self.log.info("An exception {0} occurred in generating the SDK".format(err))
            raise err


class SdkFactory:
    """
    Creates Factory Object for various generator

     Methods:
        generate  -- Call the generate function for particular Generator

    """
    def __init__(self,
                 commcell_object,
                 file_location="C:\swagger_latest.json",
                 language="powershell"
                 ):
        self.commcell_object = commcell_object
        self.file_location = file_location
        sdk_geenrators = {
            "powershell": PowershellGenerator,
            "go": GOSDKGenerator
        }
        self.sdk_object = sdk_geenrators[language.lower()](self.commcell_object, self.file_location)

    def generate(self, **kwargs):
        """
        Generate the Powershell SDK in the path specified
        Args:
            language (str) - Language of SDK needs to be generated
                                Powershell, Go
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """

        return self.sdk_object.generate(**kwargs)

    def build_module(self,  **kwargs):
        """
        Build the Powershell SDK in the path specified
        Args:
            language (str) - Language of SDK needs to be generated
                                Powershell, Go
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """

        sdk_geenrators = {
            "powershell": PowershellGenerator,
            "go": GOSDKGenerator
        }

        return self.sdk_object.build_module(**kwargs)

    def pack_module(self, language="Powershell", **kwargs):
        """
        pack the Powershell SDK in the path specified
        Args:
            language (str) - Language of SDK needs to be generated
                                Powershell, Go
            **kwargs:  - List of inouts need to be passed for SK generation
                input-file  (str) - path of the configuration yaml
                output-foder(str)  - folder where SDK needs to be generated

        Returns:
            Raise exceltion on failure

        """


        return self.sdk_object.pack_module(**kwargs)





