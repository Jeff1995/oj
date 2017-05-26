# Slurm

## About slurm

* `slurmd` is a daemon running at compute node
* `slurmctld` is a daemon running at manager node.

## Installation and configuration

> Assume installation path is `/opt/slurm`

### Installation

* Make sure `libssl-dev`, `munge`, `python` of ubuntu (or equivalent packages on other systems) are installed (`munge` might not be necessary, not tested yet)
* Download source form slurm official website, extract tar ball
* `./configure --prefix=/opt/slurm`
* `make` and then `make install`
* Execute `ldconfig -n /opt/slurm/lib`

### Configuration
* Create directory `/opt/slurm/etc`
* Create private key and public certificate
    - `openssl genrsa -out /opt/slurm/etc/slurm.key 1024`
    - `openssl rsa -in /opt/slurm/etc/slurm.key -pubout -out /opt/slurm/etc/slurm.cert`
    - `chmod 400 /opt/slurm/etc/slurm.key`
* Copy example configuration file `slurm.conf` to `/opt/slurm/etc`, modify as needed
    - Manager and compute node names should be the same as `hostname -s`
    - Modify `ControlAddr` and `NodeAddr`
* Create log directory and other related directories as specified in `slurm.conf`, namely, `/opt/slurm/log`, `/opt/slurm/spool/d` and `/opt/slurm/spool/ctld`

* `useradd -u 1234 slurm`
* `chown -R slurm /opt/slurm` and `chgrp -R slurm /opt/slurm`
* Modify `PATH` to include `/opt/slurm/bin` and `/opt/slurm/sbin`

* Complete the above installation steps first on manager node and then on compute node
    - Make sure that compute node has `slurm.cert` copied from manager node, instead of generating its own
    - Compute node does not need `slurm.key`

### Testing

* Run `slurmctld` on manager node, and run `slurmd` on compute node
* Run `srun ifconfig` on manager node. If it prints network information of the compute node, it means that the system is working fine.
* If something goes wrong, add `-D` for `slurmctld` and `slurmd` to debug in foreground.

### Customization

* Further customize `/opt/slurm/etc/slurm.conf` for production purpose.
