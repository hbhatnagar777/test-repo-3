FILE=##Automation--file--##
KEY=##Automation--key--##

get_registry_value()
{
echo `grep -i -w $2 $1 | sed 's/[^ ]* //'`
}

echo `get_registry_value $FILE $KEY`
