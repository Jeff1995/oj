#!/bin/bash
iptables -I INPUT -p tcp -m tcp --dport 1025:65535 -j ACCEPT
iptables -I OUTPUT -p tcp -m tcp --sport 1025:65535 -j ACCEPT
g++ -o judge/judge judge/judge.cpp
judge/ojroot.py &
judge/oj_d.py &

