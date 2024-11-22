# Commvault services Helm Chart

This chart uses a official Docker image of commvault services to deploy backup agents.

## Prerequisites Details

* Kubernetes 1.6+
* PV dynamic provisioning support on the underlying infrastructure

## StatefulSets Details
* https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/

## StatefulSets Caveats
* https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#limitations

## Todo

* Implement TLS/Auth/Security
* Smarter upscaling/downscaling

## Chart Details
This chart will do the following:

* Implement a dynamically scalable commvault cluster using Kubernetes StatefulSets/Deployments

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
$ helm install --name my-release charts/cvservices
```

## Deleting the Charts

Delete the Helm deployment as normal

```
$ helm delete my-release
```

Deletion of the StatefulSet doesn't cascade to deleting associated PVCs. To delete them:

```
$ kubectl delete pvc -l release=my-release,component=data
```

## Configuration

The following tables lists the configurable parameters of the elasticsearch chart and their default values.

|                 Parameter                 |                             Description                             |                       Default                       |
| ----------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------- |
| `mediaAgentReplicaCount`                  | MA container replicas (statefulset)                                 | `2`                                                 |
| `image.name`                              | Container image name                                                | `commvault-ma`                                      |
| `image.tag`                               | Container image tag                                                 | `latest`                                            |
| `image.pullPolicy`                        | Container pull policy                                               | `IfNotPresent`                                      |
| `imageCredentials.registry`               | Container image registry server                                     |                                                     |
| `imageCredentials.username`               | Registry server user name                                           |                                                     |
| `imageCredentials.password`               | Registry server password                                            |                                                     |
| `commcell.csclientname`                   | CommServer Client Name                                              |                                                     |
| `commcell.cshostname`                     | CommServer Network Host Name                                        |                                                     |
| `commcell.csipaddress`                    | CommServer IP Address                                               |                                                     |
| `commcell.user`                           | CommCell user name                                                  | `admin`                                             |
| `commcell.password`                       | CommCell password                                                   |                                                     |
| `commcell.authtoken`                      | CommCell authentication token, overrides user/password              |                                                     |
| `storage.config.storageClassName`         | Configuration persistent volume Class                               | `storage.data.storageClassNmae`                     |
| `storage.config.size`                     | Configuration persistent volume size in GB                          | `5`                                                 |
| `storage.config.accessMode`               | Configuration persistent Access Mode                                | `ReadWriteOnce`                                     |
| `storage.data.storageClassName`           | Backup data persistent volume Class                                 |                                                     |
| `storage.data.size`                       | Backup data volume size in GB                                       | `20`                                                |
| `storage.data.accessMode`                 | Backup data persistent Access Mode                                  | `ReadWriteMany`                                     |
| `storage.ddb.storageClassName`            | Backup ddb persistent volume Class                                  | `storage.data.storageClassNmae`                     |
| `storage.ddb.size`                        | Backup ddb volume size in GB                                        | `5`                                                 |
| `storage.ddb.accessMode`                  | Backup ddb persistent Access Mode                                   | `ReadWriteOnce`                                     |
| `nameOverride`                            | Name to tag the resources with                                      | `Release Name`                                      | 

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.


