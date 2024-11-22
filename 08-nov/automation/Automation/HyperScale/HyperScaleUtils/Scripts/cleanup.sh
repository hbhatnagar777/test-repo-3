# CHANGE VARIABLES HERE #

# the hyper scale storage name
storage=$1

# the nodes on which cleanup is to be run
nodes=${@:2}

# VARIABLE SECTION ENDS #

./ssh-command.sh "umount /ws/glus*" $nodes
./ssh-command.sh "rm -rf /ws/glus*" $nodes


gluster v stop $storage
gluster v delete $storage
for node in $nodes
do
gluster peer detach $node"sds" force
done

# clear out /ws/disk1/*, /ws/disk2/*, /ws/ddb/*, etc.
./ssh-command.sh "for i in \`lsblk | grep -i /ws/ | awk '{print \$7}'\` ; do rm -fr \$i/* ; ls -l \$i ; done" $nodes

# remove /ws/glus entry from /etc/fstab
./ssh-command.sh "sed -i.bak "/$storage/d" /etc/fstab" $nodes

# remove the ReplaceBricksFile
./ssh-command.sh "rm -rf /opt/commvault/iDataAgent/jobResults/ScaleOut/ReplaceBricksFile" $nodes

# force update
./ssh-command.sh "commvault restart" $nodes

