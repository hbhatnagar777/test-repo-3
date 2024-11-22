PATH=##Automation--path--##
TYPE=##Automation--path_type--##

is_valid()
{
    if [ $1 $2 ]
    then
        echo "TRUE"
    fi
}

echo `is_valid $TYPE $PATH`
