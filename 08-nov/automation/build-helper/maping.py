import os
import shutil 
import sys
import time
import ctypes
import constants
import logging
import threading
import run_pylint
from downloadpackages import DownloadPackages
from email_body import construct_email_body
lock = threading.Lock()

class CVlintThreads(threading.Thread):
    exitflag=False
    
    def __init__(self, cvlint_directory, filepath, output_values):
        threading.Thread.__init__(self,daemon=False)
        self.thread_name = filepath
        self.filepath = filepath
        self.cvlint_directory = cvlint_directory 
        self.output_values = output_values   
    
    def run(self):
        cvlint_obj = run_pylint.PylintOutput()
        cvlintout = cvlint_obj.run(self.cvlint_directory, self.filepath)
        with lock:
            self.output_values.append(cvlintout)
            
    def get_id(self): 
  
        # returns id of the respective thread 
        if hasattr(self, '_thread_id'): 
            return self._thread_id 
        for id, thread in threading._active.items(): 
            if thread is self: 
                return id
            
    def raise_exception(self): 
        thread_id = self.get_id() 
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit)) 
        if res > 1: 
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0) 
            pass 
        

class Mapping(object):
    """
    mapping file to map files to binaries and generate folders for changed files.
    
    """
    def __init__(self, build_type, changefile=None, source = None,
                  destination=None, log=None, cvlint_directory=None, pylint_change_file =None, official=False):
        """
        initializing the mapping file
        """
        self.source = source
        self.destination = destination
        self.official = official
        if changefile:
            self.changefile = changefile
        else:
            self.changefile = constants.path_to_changefile
        if build_type == 'build':
            #if not self.official:
                #self.changefile = os.path.join(os.path.dirname(changefile), 'binaries_orig.json')
            self.build = True
            self.binary = False
        else:
            self.binary = True
            self.build = False
            self.destination = self.source
        self.pylint_change_file = pylint_change_file
        self.windows_binaries = constants.windows_binary_mapping 
        self.unix_binaries = constants.unix_binary_mapping
        self.formnumber = ''
        self.logger = log
        self.cvlint_directory = cvlint_directory
        
    def get_file_list(self):
        """
        reads change file and returns list of changed files in a list
        
        """
                    
        if not os.path.isfile(self.changefile):
            logger.error("File path {} does not exist. Exiting...".format(self.changefile))
            raise Exception("File path {} does not exist. Exiting...".format(self.changefile))
        
        changefile_list=[]
        
        with open(self.changefile) as fp:            
            if self.build:
                import json
                changefile = json.load(fp)
                for binvalue in changefile['WinBinaries']:
                    if binvalue !='CVAutomation.py':
                        if constants.master_binary == binvalue or binvalue.find(".see")<0:
                            continue
                    found = False
                    for key , value in constants.windows_binary_mapping.items():
                        if value == binvalue:
                            changefile_list.append(key)
                            found = True
                            break
                    if found:
                        continue
                    else:
                        logger.error("Binary not found in constants for binary {}...".format(binvalue))
                        # raise Exception("Binary not found in constants for binary {}...".format(binvalue))
            else:
                for cnt, line in enumerate(fp):
                    logger.info("Line {}: {}".format(cnt, line))
                    changefile_list.append(line)
                    
        if len(changefile_list) <=0:
            logger.error("File exist {} but no files specified...".format(self.changefile))
            #raise Exception("File exist {} but no files specified...".format(self.changefile))
            
        return changefile_list
    
    def get_path(self,change_file):
        """
        returns the actual path from change file path
        
        """
        logger.info("change file %s"%change_file)
        if self.build:
            if change_file == 'cvpysdk':
                return change_file, change_file, change_file
            elif change_file == 'CVAutomation.py':
                return 'Automation', '', change_file
            else:
                return 'Automation', change_file, change_file
                
            
        else:
            split_values = change_file.split(r"/")
            
            if len(split_values) >=3:
                return split_values[0], split_values[1],split_values[len(split_values)-1].rstrip()
            elif len(split_values) >=2:
                return split_values[0], '', split_values[1].rstrip()
            else:
                logger.info("Skipping this file %s"%str(split_values))
                return split_values[0], split_values[0], split_values[0]
    
    def run_cvlint(self, cvlint_filepaths):
        """
        returns the actual path from change file path
        
        """
        logger.info("change file %s"%cvlint_filepaths)
        threads=[]
        output_values=[]
        counter = 0
        for filpath in cvlint_filepaths:            
            t = CVlintThreads(self.cvlint_directory, filpath, output_values)
            threads.append(t)
            t.daemon = True
            t.start()        
            counter = counter + 1
            if len(threads) >=2:
                for threadobj in threads:
                    self.logger.info("waiting for thread {}".format(threadobj.getName()))
                    while threadobj.is_alive():
                        time.sleep(30)                        
                    self.logger.info("Completed processing thread {}".format(
                    threadobj.getName()))
                threads=[]
            if counter >=20:
                self.logger.error("Number of files more than 30, so skipping other files pylint stats.")
                break
        for threadobj in threads:
            counter = 0
            self.logger.info("waiting for thread {}".format(threadobj.getName()))
            while threadobj.is_alive():
                time.sleep(30)
                counter = counter + 1
            self.logger.info("Completed processing thread {}".format(
            threadobj.getName()))
        self.logger.info("All threads exited")
        text = construct_email_body(output_values, "formid")
        with open(os.path.join(self.cvlint_directory, "cvlintoutput.html"), "w") as file: 
            # Writing data to a file 
            file.write(str(text)) 
        

    def copy_data(self, src, dst, is_file=False, downloadpacakges = False, download_src = None, Download_dst=None):
        """
        copies folders from source to destination
        
        """  
        if downloadpacakges:
            download = DownloadPackages(r"/usr/local/bin", download_src, Download_dst,logger)
            download.execute_command()      
        try:
            if os.path.exists(dst):
                shutil.rmtree(dst, ignore_errors=True)
        except:
            logger.info('Error while deleting directory')
        
        try:
            from cvshelper import CVS
            cvs = CVS(logger)
            if src.find(constants.cvs_checkout_folders[0])>=0:
                if not os.path.exists(src):
                    os.makedirs(src)                
                cvspath = constants.cvs_paths[0]
                cvs.checkout(src, cvspath)
                src=os.path.join(src, cvspath)
                shutil.copytree(src, dst,ignore=shutil.ignore_patterns("CVS"))
                return
            # elif src.find(constants.cvs_checkout_folders[1])>=0:
            #     if not os.path.exists(src):
            #         os.makedirs(src)
            #     shutil.copytree(src, dst,ignore=shutil.ignore_patterns("CVS"))
            #     cvspath = constants.cvs_paths[1]
            #     package_path = os.path.join(src, 'packages')
            #     cvs.checkout(package_path, cvspath)                
            #     src=os.path.join(package_path, cvspath)
            #     dst = os.path.join(dst, 'packages')
            elif src.find(constants.cvs_checkout_folders[2])>=0:
                if not os.path.exists(src):
                    os.makedirs(src)
                shutil.copytree(src, dst,ignore=shutil.ignore_patterns("CVS"))
                cvspath = constants.cvs_paths[2]
                package_path = os.path.join(src, 'packages')
                cvs.checkout(package_path, cvspath)                
                src=os.path.join(package_path, cvspath)
                dst = os.path.join(dst, 'packages')
        except Exception as e:
            logger.error('Error while doing cvs checkout %s'%str(e))
            return
        
        try:
            if is_file:
                filepath = os.path.dirname(os.path.abspath(dst))
                if not os.path.exists(filepath):
                    os.makedirs(filepath)
                shutil.copy(src, dst)
            else:
                try:
                    if os.path.exists(dst):
                        shutil.rmtree(dst, ignore_errors=True)
                except:
                    logger.info('Error while deleting directory')
                shutil.copytree(src, dst,ignore=shutil.ignore_patterns("CVS"))
                
            
        
        except OSError as exc: # python >2.5
            raise Exception("Failed to copy folders from source %s to destination %s"%(src,dst))
    
    def create_binary_file(self, file_list):
        """
        creates binary mapping file
        
        """
        binaries_dict = {"WinBinaries":['cv-automation-master'],
                         "UnixBinaries":[]}
        for file in file_list:
            if file in constants.windows_binary_mapping:
                binaries_dict["WinBinaries"].append(constants.windows_binary_mapping[file])
            if file in constants.unix_binary_mapping:
                binaries_dict["UnixBinaries"].append(constants.unix_binary_mapping[file])
            
                
        logger.info("Binary dicti file %s"%str(binaries_dict))        
        with open(self.destination, "w") as file:
            # Writing data to a file 
            file.write(str(binaries_dict).replace("'","\"")) 
    
    def pylint_stats(self):
        """
        run pylint on changed files
        
        """
        if not self.official:
            changefile_list=[]        
            with open(self.pylint_change_file) as fp: 
                for cnt, line in enumerate(fp):
                    logger.info("Line {}: {}".format(cnt, line))
                    changefile_list.append(line)
                 
            cvlint_filepaths=[]
            for change_file in changefile_list:            
                if change_file.find(".py")>=0:
                    cvlint_filepaths.append(os.path.join(self.source, change_file.rstrip()))            
                
            if len(cvlint_filepaths) >0:
                self.run_cvlint(cvlint_filepaths)
       
        
    def generate_change_folders(self):
        """
        generates changed files folders based on change file list
        
        """
        changed_files = self.get_file_list()        
        binari_details=[]
        for change_file in changed_files:
            parentfolder, subfolder, filename = self.get_path(change_file)
            subfolder=subfolder.rstrip()
            full_path = None
            if parentfolder == 'cvpysdk':
                if self.source is not None:
                    if subfolder:
                        full_path = os.path.join(self.source, parentfolder)
                        dest_path = os.path.join(self.destination, self.formnumber, parentfolder)
                    else:
                        full_path = os.path.join(self.source, parentfolder, filename)
                        dest_path = os.path.join(self.destination, self.formnumber, parentfolder, filename)
                else:
                    full_path = os.path.join(constants.cvpysdk_folder_path , subfolder)
            elif parentfolder == 'Automation' :
                if self.source is not None:
                    if subfolder:
                        full_path = os.path.join(self.source, parentfolder, subfolder)
                        dest_path = os.path.join(self.destination, self.formnumber, parentfolder, subfolder)
                    else:
                        full_path = os.path.join(self.source, parentfolder, filename)
                        dest_path = os.path.join(self.destination, self.formnumber, parentfolder, filename)
                    
                else:
                    full_path = os.path.join(constants.automation_folder_path, subfolder)
                
            if subfolder not in binari_details:
                if subfolder == '' and filename == 'CVAutomation.py':
                    binari_details.append(filename)
                elif parentfolder == 'cvpysdk' and parentfolder not in binari_details:
                    binari_details.append(parentfolder)                    
                else:
                    binari_details.append(subfolder)     
                
            if self.build:
                
                downloadpacakges=False
                download_src=None
                download_dst=None
                if subfolder.find("cvautomationmask")>=0:
                    downloadpacakges=False
                    download_src = os.path.join(full_path,"packages", 'all_requirements.txt')
                    download_dst= os.path.join(full_path,"packages")
                if subfolder.find("cvpysdk")>=0:
                    downloadpacakges=False
                    download_src = os.path.join(full_path,"packages", 'all_requirements.txt')
                    download_dst= os.path.join(full_path,"packages")
                
                if self.destination is not None:
                    if full_path is not None:
                        self.copy_data(full_path, dest_path, os.path.isfile(full_path),downloadpacakges,download_src, download_dst) 
                    else:
                        logger.info("skipping the file copy %s"%change_file)                              
                else:
                    self.copy_data(full_path, os.path.join(constants.updates_folder, self.formnumber, subfolder),
                               os.path.isfile(full_path), filename)
        if self.binary:
            self.create_binary_file(binari_details)
        elif not self.official:
            self.pylint_stats()



if __name__ == '__main__':
    """
    main function to start execution
    """
    if len(sys.argv) <=3:
        print("please provide formnumber, changesfile, source, destination details")
        sys.exit(False)
    
    if sys.argv[0] =='help':
        print("Please provide parameters in the form of getBinary/batch changefile, source, destination")
    changefile = sys.argv[2]
    build_type = sys.argv[1]
    source = sys.argv[3]
    destination = sys.argv[4]
    official = False
    pylint_change_file = None
    if len(sys.argv) >= 7:
        pylint_change_file = sys.argv[5]
        if sys.argv[6] == "false":
            official = True
        
    
    
    logger = logging.getLogger('Automation')
    cvlint_directory = os.path.join(os.getcwd(),"jobDetails")
    log_path = os.path.join(cvlint_directory, "automation.log")
    if os.path.exists(log_path):
        shutil.rmtree(log_path, ignore_errors=True)
        with open(log_path,"w") as fp:
            pass
    else:
        with open(log_path,"w") as fp:
            pass
    hdlr = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(logging.INFO)
    #logging.config.fileConfig(os.path.normpath())

    # Create the logger
    # Admin_Client: The name of a logger defined in the config file
    #l#ogger = logging.getLogger(os.path.normpath(os.path.join(os.getcwd(),"jobDetails","autoamtion.log"))

    
    
    logger.info("Change file: %s"%sys.argv[2])
    logger.info("build_type: %s"%sys.argv[1])
    logger.info("source: %s"%sys.argv[3])
    logger.info("destination: %s"%sys.argv[4])
    logger.info("official: %s"%str(official))
    logger.info("pylint_change_file: %s"%str(pylint_change_file))

    # Shut down the logger
    
    mapping = Mapping(build_type, changefile, source, destination, logger, cvlint_directory, pylint_change_file, official)
    files = mapping.generate_change_folders()




