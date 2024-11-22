# usage:
# ./form.sh </net/eng path copied frome engupdates website> <node1 hostname> <node2 hostname> <...>
# DO NOT SPECIFY THE HOSTNAME OF THE HOST RUNNING THIS SCRIPT - GOES TO INFINITE RECURSION

# e.g.:
# [hydhsxautovm10 ~]# ./form.sh /net/eng/devltotest_readonly/devltotest_src/11.0.0/Build80/Updates/Unix/linux-x8664/linux-x8664_11.0.0B80_188806 hydhsxautovm{11,12}.idcprodcert.loc
# note that node 10 is not included in the command line arguments

# prefix="/net/eng/mnt/DevlToTest/"
dest=/update
form_path=$1
# form_path=${prefix}11.0.0${given_form_path#*11.0.0}
nodes=${@:2}

mkdir -p $dest
umount $dest
mount $form_path $dest
# mount eng.gp.cv.commvault.com: /net/eng
cp -r $dest/cd_update ~

form_id=`cat ~/cd_update/Config/update.ini | grep -i form | egrep -o "[[:digit:]]+"`
form_name=`cat ~/cd_update/Config/update.ini | egrep -i "^name=" | cut -d- -f4-`
form_dir=~/Form$form_name
mv -f ~/cd_update $form_dir

for node in $nodes
do
scp -r $form_dir $node:$form_dir
done
echo "--------------------------------------------------------"
grep TransactionID $form_dir/Config/update.ini
echo "Run with:"
echo "$form_dir/InstallUpdates -silent"
echo "Verify with:"
echo "ls /opt/commvault/Updates | grep $form_name"