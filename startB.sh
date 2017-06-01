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
sudo -u slurm /opt/slurm/sbin/slurmd -c

