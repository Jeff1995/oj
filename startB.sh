#!/bin/bash
if [ ! -d log ]; then
    sudo -u slurm mkdir log
fi
if [ ! -d dat ]; then
    sudo -u slurm mkdir dat
    sudo -u slurm mkdir dat/submissions
    sudo -u slurm mkdir dat/problems
fi
sudo -u slurm g++ -o judge/judge judge/judge.cpp
sudo judge/ojroot.py &

iptables -I INPUT -p tcp -m tcp --dport 1024:65535 -j ACCEPT
iptables -I OUTPUT -p tcp -m tcp --sport 1024:65535 -j ACCEPT
sudo -u slurm /opt/slurm/sbin/slurmd -c

