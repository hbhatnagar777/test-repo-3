#!/bin/bash
set -x
if [ $# -lt 3 ]
then 
	echo "Usage: $0 <ENV file path> <volume path> <docker image name> [container name]"
	echo "volume path - This folder should have enough space for backup data / ddb index / Index cache / Log files etc"
	exit 1
fi

ENV_FILE=$1
CVDIR=$2
IMAGE=$3
CONTAINER_NAME=$4

if [ ! -f $ENV_FILE ]
then
	echo "Env file $ENV_FILE not found"
	exit 1
fi

if [ ! -d ${CVDIR} ] 
then 
	echo "Volume directory doesn't exist"
fi

CONTAINER_NAME_OPT=""
if [ ! -z "$CONTAINER_NAME" ]
then
	CONTAINER_NAME_OPT=--name=$CONTAINER_NAME
	#get rid of any running containers with same name if name option is being used.
	echo "Deleting container with name $CONTAINER_NAME"
	docker kill $CONTAINER_NAME > /dev/null 2>&1
	docker rm $CONTAINER_NAME > /dev/null 2>&1
fi

source $ENV_FILE

#set the path to folder which will contain persistent info from container

FULLIMAGE_NAME=${DOCKERREG}${IMAGE}
echo $FULLIMAGE_NAME

echo "Creating container $CONTAINER_NAME"

docker run -d $CONTAINER_NAME_OPT \
-v $ENV_FILE:/opt/cvdocker.env \
-v $CVDIR/CommvaultRegistry/:/etc/CommVaultRegistry \
-v $CVDIR/libraryPath/:/opt/libraryPath \
-v $CVDIR/ddbPath:/opt/ddbPath \
-v $CVDIR/IndexCache/:/opt/commvault/MediaAgent/IndexCache \
-v $CVDIR/jobResults/:/opt/commvault/iDataAgent/jobResults \
-v $CVDIR/certificates:/opt/commvault/Base/certificates \
-v $CVDIR/Log_Files:/var/log/commvault/Log_Files \
--hostname $CV_CLIENT_CLIENTNAME \
--net bridge \
--add-host $CV_CSHOSTNAME:$CV_CSIPADDR \
--env-file $ENV_FILE \
$FULLIMAGE_NAME

