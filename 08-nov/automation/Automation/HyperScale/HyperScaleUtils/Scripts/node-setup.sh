# CHANGE VARIABLES HERE #

# public interface, which connects to commserve 
if_pub=ens192

# private interface, internal to nodes
if_pri=ens224

# host file details
read -r -d '' peers <<EOM
ip_1 hostname_1
ip_2 hostname_2
ip_3 hostname_3
ip_4 hostname_4
EOM

node_name=$1
# VARIABLE SECTION ENDS #

echo "changing time"
date
mv /etc/localtime /etc/localtime.backup
ln -s /usr/share/zoneinfo/Asia/Calcutta /etc/localtime
date

echo "Node name: $node_name"

echo "setting hostname: $node_name"
hostnamectl set-hostname $node_name

echo "reading public IP..."
# dhclient $if_pub
ip_pub=`ip -f inet addr show $if_pub | grep -Po 'inet \K[\d.]+'`
echo "Got IP "$ip_pub

echo "reading private MAC..."
mac_pri=`cat /sys/class/net/$if_pri/address`
echo "Got MAC "$mac_pri

ip_pri=`echo "$peers" | grep "${node_name}sds$" | cut -d' ' -f1`
echo "private IP $ip_pri: "
# read confirm

printf "HWADDR=%s\nBOOTPROTO=static\nIPADDR=%s\nDEVICE=$if_pri\nONBOOT=yes\nNM_CONTROLLED=no\n" $mac_pri $ip_pri > /etc/sysconfig/network-scripts/ifcfg-$if_pri
printf "BOOTPROTO=dhcp\nDEVICE=$if_pub\nONBOOT=yes\nNM_CONTROLLED=no\n" > /etc/sysconfig/network-scripts/ifcfg-$if_pub

echo "restarting network..."
systemctl restart network
echo "verifying private ip"
ip -f inet addr show $if_pri | grep -Po 'inet \K[\d.]+'


echo "adding entries to hosts file"

echo "$peers" >> /etc/hosts

# HSX
echo "changing time"
date
mv /etc/localtime /etc/localtime.backup
ln -s /usr/share/zoneinfo/Asia/Calcutta /etc/localtime
date

# some helpers
echo 'export HISTTIMEFORMAT="%d/%m/%y %T "' >> ~/.bash_profile
echo "export cvma=/var/log/commvault/Log_Files/CVMA.log" >> ~/.bashrc
echo "export logs=/var/log/commvault/Log_Files" >> ~/.bashrc
echo "export sout=/opt/commvault/iDataAgent/jobResults/ScaleOut" >> ~/.bashrc
echo "export unixcache=/opt/commvault/SoftwareCache/CVAppliance/Unix" >> ~/.bashrc
echo "export ma=/opt/commvault/MediaAgent" >> ~/.bashrc
echo "export cvreg=/etc/CommVaultRegistry/Galaxy/Instance001" >> ~/.bashrc
echo "export mareg=/etc/CommVaultRegistry/Galaxy/Instance001/MediaAgent" >> ~/.bashrc
echo "export evreg=/etc/CommVaultRegistry/Galaxy/Instance001/EventManager" >> ~/.bashrc
echo "export TMOUT=0" >> ~/.bashrc

source ~/.bashrc
echo "Exiting"
