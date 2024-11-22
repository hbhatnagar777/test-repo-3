# usage: ./ssh-command.sh "echo 'hello world!'" murtaza-node2 murtaza-node3
# this script runs commands in nodes that are mentioned
# in the command line

command=$1
nodes=${@:2}
for node in $nodes
do
echo 
echo $node"$ "$command
ssh -q $node $command
done
