#!/usr/bin/env python

import ConfigParser
import socket
import os
import json

def main():
    cf = ConfigParser.ConfigParser()
    cf.read("conf/oj.conf")

    judge_host = cf.get('sandbox', 'judgeHost')
    userid = int(cf.get('sandbox', 'userid'))

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if os.path.exists("/tmp/judge_root.sock"):
        os.unlink("/tmp/judge_root.sock")
    server.bind("/tmp/judge_root.sock")
    os.system('chmod 777 /tmp/judge_root.sock')
    server.listen(0)
    while True:
        connection, address = server.accept()
        infor = json.loads(connection.recv(1024).decode())
        work_dir, bin, usrout, errout, input_dir, stdin, time_limit, mem_limit = infor
        cmd = "%s %s %s %s %s %s %s %s %s %s"%(judge_host, work_dir, bin, usrout, errout, input_dir, stdin, time_limit, mem_limit, userid)
	tmp = os.popen(cmd).read()
        result, time_used, mem_used = [int(s) for s in tmp.split()]
        success = result == 0
        time_exceeded = result == 2
        mem_exceeded = result == 3
        connection.send(json.dumps([success, time_exceeded, mem_exceeded, time_used, mem_used]).encode())


if __name__ == '__main__':
    main()
