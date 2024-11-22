# usage: ./ssh-access.sh murtaza-node2 murtaza-node3
# this script adds the SSH keys to nodes that are mentioned
# in the command line

if test -f ~/.ssh/id_rsa.pub; then
    echo "public key exists"
else
    echo "creating key pair..."
    ssh-keygen -qf ~/.ssh/id_rsa -P ""
fi

for node;
do
# this ensures that the prompt to accept is taken care of
ssh-keyscan -H $node >> ~/.ssh/known_hosts
sshpass -p "<<DEFAULT_PASSWORD>>" ssh-copy-id -i ~/.ssh/id_rsa.pub $node
done
