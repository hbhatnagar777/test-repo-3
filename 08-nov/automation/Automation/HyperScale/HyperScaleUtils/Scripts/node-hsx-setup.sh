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
