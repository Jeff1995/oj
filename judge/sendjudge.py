#!/usr/bin/env python

import socket
import sys

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect("/tmp/judge_root2.sock")
print sys.argv[1]
client.send(sys.argv[1])
