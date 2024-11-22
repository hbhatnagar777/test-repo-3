Function DO_CLUSTER_FAILOVER() { 

##################################################################################################

#-------------------Execution starts here -------------------------------------------------------#
$activenode = "##Automation--activenode--##"         #string
$passivenode = "##Automation--passivenode--##"         #string


Get-ClusterNode $activenode | Get-ClusterGroup | Move-ClusterGroup -Node $passivenode

##################################################################################################

}


