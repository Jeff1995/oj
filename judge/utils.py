"""
This script contains classes and functions that implement the judging process
"""


import os
import os.path
import requests
import pymysql.cursors
import logging
import json
from subprocess import call
from ConfigParser import ConfigParser


logger = logging.getLogger('judge.py')
logger.setLevel(logging.DEBUG)


class Submission:

    """
    This class is the representation of the submission
    """

    def __init__(self, submissionId, comm, compiler, sandbox, comparer):
        self.comm = comm
        self.compiler = compiler
        self.sandbox = sandbox
        self.comparer = comparer

        info = self.comm.fetchInfo(submissionId)

        # Use info to fill in the following attributes
        self.submissionId = submissionId
        self.problemId = info['problemId']
        self.timeLim = info['timeLimit']
        self.memLim = info['memLimit']
        self.stdin = 'problems/' + str(self.problemId) + '/stdin'
        self.stdout = 'problems/' + str(self.problemId) + '/stdout'
        self.src = 'submissions/' + str(self.submissionId) + '/submit.c'
        self.bin = 'submissions/' + str(self.submissionId) + '/submit.o'
        self.usrout = 'submissions/' + str(self.submissionId) + '/usrout'

        self.result = {
            "compile_success": None,
            "run_success": None,
            "compare_success": None,
            "time_exceeded": None,
            "mem_exceeded": None,
            "time_used": None,
            "mem_used": None
        }
        logger.info('Submission[' + str(submissionId) + '] created.')

    def prepare(self):  # Fetch src file and fetch IO file if not already exist
        if not os.path.isfile(self.stdin):
            self.comm.fetchFile(self.stdin)
        if not os.path.isfile(self.stdout):
            self.comm.fetchFile(self.stdout)
        self.comm.fetchFile(self.src)

    def compile(self):  # Compile and update self.result
        self.result['compile_success'] = self.compiler.compile(self.src, self.bin)

    def run(self):  # Run the user program and update self.result
        result = self.sandbox.run(self.bin, self.stdin, self.usrout, self.timeLim, self.memLim)
        self.result['run_success'] = result['success']
        self.result['time_exceeded'] = result['time_exceeded']
        self.result['mem_exceeded'] = result['mem_exceeded']
        self.result['time_used'] = result['time_used']
        self.result['mem_used'] = result['mem_used']

    def compare(self):  # Compare and update self.result
        self.result['compare_success'] = self.comparer.compare(self.stdout, self.usrout)

    def report(self):  # Construct content with self.result and send back
        self.comm.report(json.dump(self.result))


class Sandbox:

    """
    This class runs the compiled program in a sandbox and returns result
    """

    def __init__(self):
        pass

    def run(self, bin, stdin, usrout, time_limit, mem_limit):
        cmd = "./judge.o . %s %s /dev/null %d %d %s"%(stdin, usrout, time_limit, mem_limit, bin)
        result, time_used, mem_used = [int(s) for s in os.popen(cmd).read().split()]

        success = result == 0
        time_exceeded = result == 2
        mem_exceeded = result == 3

        return success, time_exceeded, mem_exceeded, time_used, mem_used

    def close(self):
        pass


class Communicator:

    """
    This class does all communicate with the manager node
    """

    def __init__(self, managerAddr, mysqlPort, mysqlUsr, mysqlPasswd, mysqlDb):
        self.managerAddr = managerAddr
        self.mysqlConn = pymysql.connect(host=managerAddr,
                                         port=mysqlPort,
                                         user=mysqlUsr,
                                         password=mysqlPasswd,
                                         db=mysqlDb,
                                         charset='utf8',
                                         cursorclass=pymysql.cursors.DictCursor)

    def fetchInfo(self, submission):  # Fetch info from database
        try:
            with connection.cursor() as cursor:
                sql = "SELECT `Problem`.`problemId` AS `problemId`, `timeLimit`, `memLimit` " + \
                      "FROM `Submit`, `Problem` WHERE " + \
                      "`submitId`=%s AND `Submit`.`problemId`=`Problem`.`problemId`"
                cursor.execute(sql, (str(submission.submissionId, )))
                result = cursor.fetchone()
                return result
        except DatabaseError:  # TODO: not sure if the error type is correct
            logger.error("Database connection error.")


    def fetchFile(self, path):  # Fetch file from manager node
        response = requests.get("http://" + self.managerAddr + '/' + path)
        with open(path, 'w') as fetchedFile:
            fetchedFile.write(response.text)

    def report(self, content):
        response = requests.post("http://" + self.managerAddr + '/report.php',
                                 data = content)  # TODO: error handling

    def close(self):
        self.mysqlConn.close()


class Compiler:

    """
    This class deals with compilation
    """

    def __init__(self, compiler, args):
        self.compiler = compiler
        self.args = args

    def compile(self, src, bin):  # Return bool
        retcode = call([self.compiler, self.args, '-o', bin, src])
        return retcode == 0


class Comparer:

    """
    This class is responsible for comparing user program output with stdout
    """

    def __init__(self, args):
        self.args = args

    def compare(self, stdout, usrout):  # Return bool
        retcode = call(['diff', args, stdout, usrout])
        return retcode == 0


class Config:

    """
    This class parses configuration file
    """

    def __init__(self, configFile):

        parser = ConfigParser()
        parser.read(configFile)

        self.logFile = parser.get('log', 'logFile')

        self.managerAddr = parser.get('network', 'managerAddr')
        self.mysqlPort = parser.get('network', 'mysqlPort')
        self.mysqlUsr = parser.get('network', 'mysqlUsr')
        self.mysqlPasswd = parser.get('network', 'mysqlPasswd')
        self.mysqlDb = parser.get('network', 'mysqlDb')

        self.compiler = parser.get('compile', 'compiler')
        self.compileArgs = parser.get('compile', 'args')

        self.compareArgs = parser.get('compare', 'args')
