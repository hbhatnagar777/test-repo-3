path_to_changefile = '/root/Desktop/ChangeFolder/changes.txt'
automation_folder_path = '/root/Desktop/Automation'
cvpysdk_folder_path = '/root/Desktop/cvpysdk'
updates_folder = '/root/Desktop/updatesfolder'
master_binary = 'cv-automation-master'
cvs_paths = [r'vaultcx/Source/tools/Automation/CompiledBins',
             r'vaultcx/Source/tools/Automation/cvautomationmask/packages',
             r'vaultcx/Source/tools/cvpysdk/packages']
cvs_checkout_folders=["CompiledBins",'cvautomationmask','cvpysdk']
cvs_root=':pserver:gbuilder:gbuilder@ncvs.commvault.com:/cvs/cvsrepro/GX'

windows_binary_mapping = {
    'cvpysdk':'cvpysdk.see',
    # 'Application':'cvautomation_application.see',
    # 'Autocenter':'cvautomation_autocenter.see',
    # 'AutomationUtils':'cvautomationutils.see',
    # 'CompiledBins':'cvautomation_compiled_bins.see',
    # 'CoreUtils':'cvautomation_coreutils.see',
    # 'cvautomationmask':'cvautomationmask.see',
    # 'CVTrials':'cvautomation_cvtrials.see',
    # 'Custom':'cvautomation_custom.see',
    # 'Database': 'cvautomation_database.see',
    # 'DROrchestration': 'cvautomation_drorch.see',
    # 'dynamicindex': 'cvautomation_dynamicindex.see',
    # 'FileSystem': 'cvautomation_fs.see',
    # 'Indexing':'cvautomation_indexing.see',
    # 'Install':'cvautomation_install.see',
    # 'Kubernetes': 'cvautomation_kubernetes.see',
    # 'Laptop':'cvautomation_laptop.see',
    # 'MediaAgents':'cvautomation_ma.see',
    # 'Mobile':'cvautomation_mobile.see',
    # 'Metallic': 'cvautomation_metallic.see',
    # 'NAS':'cvautomation_nas.see',
    # 'Oracle':'cvautomation_oracle.see',
    # 'Reports':'cvautomation_reports.see',
    # 'SapOracle':'cvautomation_sap_oracle.see',
    # 'Server':'cvautomation_server.see',
    # 'Testcases':'cvautomation_testcases.see',
    # 'VirtualServer':'cvautomation_vsa.see',
    # 'Web':'cvautomation_web.see',
    # 'CVAutomation.py':'CVAutomation.py'
}

unix_binary_mapping = {
    'cvpysdk':'cv-pysdk.tar',
    # 'Application':'cvautomation-application.tar',
    # 'Autocenter':'cvautomation-autocenter.tar',
    # 'AutomationUtils':'cvautomation-utils.tar',
    # 'CompiledBins':'cvautomation-compiled-bins.tar',
    # 'CoreUtils':'cvautomation-coreutils.tar',
    # 'Custom':'cvautomation-custom.tar',
    # 'cvautomationmask':'cvautomation-mask.tar',
    # 'Database': 'cvautomation-database.tar',
    # 'DROrchestration': 'cvautomation-drorch.tar',
    # 'dynamicindex': 'cvautomation-dynamicindex.tar',
    # 'FileSystem': 'cvautomation-fs.tar',
    # 'Indexing':'cvautomation-indexing.tar',
    # 'Install':'cvautomation-install.tar',
    # 'Kubernetes': 'cvautomation-kubernetes.tar',
    # 'Laptop':'cvautomation-laptop.tar',
    # 'MediaAgents':'cvautomation-ma.tar',
    # 'Mobile':'cvautomation-mobile.tar',
    # 'Metallic':'cvautomation-metallic.tar',
    # 'NAS':'cvautomation-nas.tar',
    # 'Oracle':'cvautomation-oracle.tar',
    # 'Reports':'cvautomation-reports.tar',
    # 'SapOracle':'cvautomation-sap-oracle.tar',
    # 'Server':'cvautomation-server.tar',
    # 'Testcases':'cvautomation-testcases.tar',
    # 'VirtualServer':'cvautomation-vsa.tar',
    # 'Web':'cvautomation-web.tar',
    # 'CVAutomation.py':'CVAutomation.py'
}
