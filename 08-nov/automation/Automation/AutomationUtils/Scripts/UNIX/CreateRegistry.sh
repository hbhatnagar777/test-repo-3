FILE=##Automation--file--##
KEY=##Automation--key--##
VALUE=##Automation--value--##

add_registry()
{
    touch $1
    sed -i "/^$2/d" $1
    echo "$2 $3" >> $1
}

echo `add_registry $FILE $KEY $VALUE`
