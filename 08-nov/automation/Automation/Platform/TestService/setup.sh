#!/bin/bash

mkdir -p /etc/CommVaultRegistry/Galaxy/Instance001/CVContainer/DotNet/CVDNC
echo "sControllerDlls /app/CVDNCTestService.dll" > /etc/CommVaultRegistry/Galaxy/Instance001/CVContainer/DotNet/CVDNC/.properties

commvault restart