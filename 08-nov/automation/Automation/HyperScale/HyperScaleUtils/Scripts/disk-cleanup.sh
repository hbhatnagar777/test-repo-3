#!/bin/sh
# usage: ./disk-cleanup disk1 disk2
# this script attempts to clean the disk
disks="$@"

hostname=`hostname`
for disk in $disks
do
sed -i.bak '/$disk/d' /etc/fstab
pid=`gluster v status | grep "${hostname}sds:/ws/$disk" | awk '{print $6}'`
kill -9 $pid
$block=`lsblk | grep /ws/$disk | awk '{print $1}'`
dd if=/dev/zero bs=512 count=1 of=/dev/$block
umount $disk
rm -rf /ws/$disk
echo "select diskId from MMDiskHWInfo inner join APP_Client on APP_Client.id = hostId where net_hostname like '$hostname' and deviceOSPath like '/ws/$disk'"
done
