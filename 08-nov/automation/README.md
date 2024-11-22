# The Automation Package

We are moving away from the Media-installable Automation Package to a self-checkout approach to install the Automation Package on controllers.
**Use the public automation link to clone this repository on your non-trusted VMs: [Testlab Public Git](https://gitlab.testlab.commvault.com/eng-public/automation)**
Localization folder and CompiledBins have to be copied to the machine manually from a trusted VM.
Follow the steps below to setup your machine to install the Automation Package

### Install Steps

Install these on the machine

1. Install Python(3.6+) from [python.org](https://www.python.org/downloads/) and ensure it is on the PATH. **Use Python 3.11 to avoid issues while building wheels for the provided versions**
2. Install git(2.37.1+) from [git-scm](https://git-scm.com/downloads)
3. Install cvsnt command line from [sourceforge](https://sourceforge.net/projects/cvsnt-legacy/files/) and ensure it is on PATH [Note: optional if CompiledBins not required]

### Script Options

Script to install the Automation Package is setup.py at the top level of the repo with the following options

```
usage: setup.py [-h] [--username USERNAME] [--skip-cvs-login] [--skip-cvs-checkout] [--git-cred-manager]

optional arguments:
  -h, --help           show this help message and exit
  --username USERNAME  CVS Username for Login
  --skip-cvs-login     Use this arg if you've already setup CVSROOT and logged in
  --skip-cvs-checkout  Use this arg to skip CompiledBins checkout from CVS
  --git-cred-manager   Use this arg if you have set up credentials using Git Credential Manager (local creds)
```

### CVS Login

**CVS checkout for CompiedBins is not supported for non-trusted VMs. Manually copy this**

 You can do either of the following for CVS Login

 1. You can either set up ```CVSROOT``` environment variable on your machine and perform ```cvs login``` before running the script. If you do this, you need to pass the ```--skip-cvs-login``` argument to the script
 2. You can pass your CVS username as an argument to the script ```--username USERNAME``` and the script will prompt you for your CVS password (Note that the CVS password is different from the AD password)

You can also skip checking out CompiledBins if you think you do not need it. Pass the ```--skip-cvs-checkout``` argument to skip checking out these bins from CVS

### Git Login

**Git Login setup is not required for cloning from the public testlab endpoint**

For Git Login you can do either of the following. The default method assumed by the script is SSH. For normal login add ```--git-cred-manager``` argument when starting the script. Ensure you have at least read access for the [web](https://git.commvault.com/eng/ui/web) project on git so that the localization folder can be checked out.

1. **SSH (Recommended)**: Setup SSH Login for GitLab so the credential does not expire and is safer
    1. Confirm if SSH keys are not generated for the machine in the User folder. If it is skip these steps:
        1. Since git is already installed, open a git bash terminal
        2. Use the ```ssh-keygen``` command to generate the keys
        3. Confirm location as default location in User folder under ```.ssh``` folder
        4. Leave the password blank
        5. Keys should be generated in the location mentioned
    2. Copy your public key (```id_rsa.pub```) to your clipboard
    3. Add the key to GitLab
        1. Go to [git.commvault.com](git.commvault.com)
        2. Go to your user settings by clicking on your profile on the top right and selecting Edit Profile
        3. Go to SSH keys from the sidebar
        4. Paste the public key in the key text area
        5. Title will be populated from the key; you can change this if you need to
        6. Do not set an expiration date and add key
    4. Test your SSH connection by trying to clone from git.commvault.com and when prompted type yes to add git.commvault.com permanently to your machine's known hosts
2. **Git Credential Manager**: You can also log in using your AD credentials which will be saved by the Git Credential Manager on Windows. Attempt to clone a repo and you will be prompted for a username and password for Git which will be saved on the machine. These can later be modified by using the Windows Credential Manager if required.

### Configuration

Once cvs and git logins have been configured, run ```python setup.py``` with the required arguments on cmd. Logs will be populated at the top level as ```setup.log```. Report any issues you see while running this script to [Dev-Automation](mailto:Dev-Automation@commvault.com) with the seen error on the cmd.

### Additional links

[Automation Documentation](http://autocenter.automation.commvault.com/NewDocs/index.html)  
[Adding New Python Packages to Automation](Automation/cvautomationmask/)
