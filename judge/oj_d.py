#!/usr/bin/env python

import ConfigParser
import socket
import os
import json

def main():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if os.path.exists("/tmp/judge_root2.sock"):
        os.unlink("/tmp/judge_root2.sock")
    server.bind("/tmp/judge_root2.sock")
    os.system('chmod 777 /tmp/judge_root2.sock')
    server.listen(0)
    while True:
        connection, address = server.accept()
        cur = connection.recv(1024).decode()
        print cur
        cmd = "/opt/slurm/bin/srun /opt/OJ/judge/judge.py " + cur
	print cmd
        os.system(cmd)
        connection.close()

if __name__ == '__main__':
    main()
