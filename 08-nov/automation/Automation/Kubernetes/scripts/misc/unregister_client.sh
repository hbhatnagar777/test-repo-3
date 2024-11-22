#!/bin/bash
#unregister client from commserver
if [ $# -lt 5 ]
then
	echo "Usage: $0 <client name to unregister and remove> <CS Host Name> <User Name> <Password>"
	exit
fi

CLIENT_NAME=$1
CS_HOST_NAME=$2
CS_UNAME=$3
CS_PWD=$4

CLIENT_XML=/tmp/tmpclient.xml

cat <<EOF >${CLIENT_XML}
<TMMsg_ReleaseLicenseReq isClientLevelOperation="1">
<clientEntity _type_="CLIENT_ENTITY" clientName="${CLIENT_NAME}" hostName="${CLIENT_NAME}" />
<licenseTypes appType="0" licenseType="0" licenseName="0" />
</TMMsg_ReleaseLicenseReq>
EOF


INSTDIR=/opt/commvault/Base
echo $INSTDIR
$INSTDIR/qlogin -cs ${CS_HOST_NAME} -u ${CS_UNAME} -clp ${CS_PWD}
$INSTDIR/qoperation execute -af ${CLIENT_XML}
rm -f ${CLIENT_XML}

#delete media agent instance
$INSTDIR/qdelete mediaagent -y -m ${CLIENT_NAME}
$INSTDIR/qdelete client -y -c ${CLIENT_NAME}


