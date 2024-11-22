# invoke with ./node-setup-all.sh nodes-{1..3}
# where the script is present on nodes-1

script_name="./node-setup.sh"
this_host=$1
all_nodes=${@:1}
other_nodes=${@:2}

$script_name $this_host

./ssh-access.sh $all_nodes

for node in $other_nodes
do
scp node-setup.sh root@$node:/root
ssh -q $node "$script_name $node"
done
