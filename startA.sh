#!/bin/bash
sudo judge/oj_d.py &
iptables -I INPUT -p tcp -m tcp --dport 1024:65535 -j ACCEPT
iptables -I OUTPUT -p tcp -m tcp --sport 1024:65535 -j ACCEPT
sudo -u slurm /opt/slurm/sbin/slurmctld -c

