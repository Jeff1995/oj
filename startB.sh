#!/bin/bash
if [ ! -d log ]; then
    mkdir log
fi
if [ ! -d dat ]; then
    mkdir dat
    mkdir dat/submissions
    mkdir dat/problems
fi
sudo -u slurm g++ -o judge/judge judge/judge.cpp
sudo judge/ojroot.py &
