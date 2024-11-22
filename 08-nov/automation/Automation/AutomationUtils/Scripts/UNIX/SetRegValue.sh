FILE=##Automation--file--##
KEY=##Automation--key--##
VALUE=##Automation--value--##

set_registry_value()
{
    sed -i "/^$2/d" $1
    echo "$2 $3" >> $1
}

echo `set_registry_value $FILE $KEY $VALUE`
