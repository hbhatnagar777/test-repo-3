import os, subprocess
import constants
#export CVSROOT=:pserver:sbandari@ncvs.commvault.com:/cvs/cvsrepro/GX
#SET CVSROOT=:pserver:sbandari@ncvs.commvault.com:/cvs/cvsrepro/GX


_PROG_NAME          =   'CVS_HELPER'

class CVS(object):
    @property   
    def cvsRoot(self):
        return self._cvsRoot
    @cvsRoot.setter    
    def cvsRoot(self,value):
        self._cvsRoot = value
        
    def __init__(self,logger):
        #To use this class, pass the automation logger in.  Will work with standard logger.
        self.__name__       =   'CVS'
        self._cvsRoot       =   None
        self.log            =   logger
        
    def checkout(self, workingDir, cvstag, version = "REL_11_0_0_BRANCH"):
        log =   self.log
        
        try:
            os.environ['CVSROOT'] = constants.cvs_root
            
            cmdList     =   r'cvs checkout -r %s %s' % (version, cvstag)
            process = subprocess.Popen(
                cmdList,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workingDir,
                shell=True
            )
    
            output, error = process.communicate()
    
            if output:
                #print("Command output: {%s}"%output.decode())
                self.log.info("Command output: {%s}"%output.decode())
    
            if error:
                if str(error).find('cvs checkout: Updating') >=0:
                    pass
                else:
                    raise Exception("Error: {%s}"%error.decode())           
            
            return True
        except Exception as err:
            log.exception(str(err))
            raise Exception("CVS checkout failed with exeception %s"%str(err))
    