"""
This script contains classes and functions that implement the judging process
"""


import os
import os.path
import requests
import pymysql
import pymysql.cursors
import logging
import json
import socket

from subprocess import call
from ConfigParser import ConfigParser


logFile = 'log/judge.log'

def constructLogger(name, file):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class Submission:

    """
    This class is the representation of the submission
    """

    def __init__(self, submissionId, comm, compiler, sandbox, comparer):
        self.constructed = False

        self.comm = comm
        self.compiler = compiler
        self.sandbox = sandbox
        self.comparer = comparer
        self.logger = constructLogger('Submission', logFile)

        self.submissionId = int(submissionId)

        info = self.comm.fetchInfo(self)
        if info is None:
            msg = "Failed to fetch submission info!"
            self.logger.error(msg)
            self.comm.report(msg)
            return

        # Use info to fill in the following attributes
        self.problemId = info['problemId']
        self.timeLim = info['timeLimit']
        self.memLim = info['memLimit']
        self.stdin = 'dat/problems/%d/stdin' % self.problemId
        self.stdout = 'dat/problems/%d/stdout' % self.problemId
        self.src = 'dat/submissions/%d/src.cpp' % self.submissionId
        self.bin = 'dat/submissions/%d/src.o' % self.submissionId
        self.usrout = 'dat/submissions/%d/usrout' % self.submissionId

        self.bin_relation = '/src.o'
        self.input_relation = '/input/stdin'
        self.usrout_relation = '/usrout'
        self.errout_relation = '/error'
        self.input_dir = os.path.join(os.getcwd(), 'dat/problems', str(self.problemId))
        self.work_dir = os.path.join(os.getcwd(), 'dat/submissions', str(self.submissionId))

        self.result = {
            "compile_success": None,
            "run_success": None,
            "compare_success": None,
            "time_exceeded": None,
            "mem_exceeded": None,
            "time_used": None,
            "mem_used": None
        }

        self.constructed = True
        self.logger.info('Submission[%d] created successfully.' % self.submissionId)

    def prepare(self):  # Fetch src file and fetch IO file if not already exist
        if not self.constructed:
            return False
        if not os.path.isfile(self.stdin):
            stdinFlag = self.comm.fetchFile(self.stdin)
        else:
            stdinFlag = True
        if not os.path.isfile(self.stdout):
            stdoutFlag = self.comm.fetchFile(self.stdout)
        else:
            stdoutFlag = True
        srcFlag = self.comm.fetchFile(self.src)
        return stdinFlag and stdoutFlag and srcFlag

    def compile(self):  # Compile and update self.result
        if not self.constructed:
            return False
        self.result['compile_success'] = self.compiler.compile(self.src, self.bin)
        return self.result['compile_success']

    def run(self):  # Run the user program and update self.result
        if not self.constructed:
            return False
        result = self.sandbox.run(self.work_dir, self.bin_relation, self.usrout_relation,
            self.errout_relation, self.input_dir, self.input_relation, self.timeLim, self.memLim)
        self.result['run_success'], self.result['time_exceeded'],
        self.result['mem_exceeded'], self.result['time_used'],
        self.result['mem_used'] = result
        return self.result['run_success']

    def compare(self):  # Compare and update self.result
        if not self.constructed:
            return False
        self.result['compare_success'] = self.comparer.compare(self.stdout, self.usrout)
        return self.result['compare_success']

    def report(self):  # Construct content with self.result and send back
        if not self.constructed:
            return False
        return self.comm.report(self)


class Sandbox:

    """
    This class runs the compiled program in a sandbox and returns result
    """

    def __init__(self):
        self.logger = constructLogger('Sandbox', logFile)

    def run(self, work_dir, bin, usrout, errout, input_dir, stdin, time_limit, mem_limit):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect("/tmp/judge_root.sock")
        client.send(json.dumps([work_dir, bin, usrout, errout, input_dir, stdin, time_limit, mem_limit]).encode())
        success, time_exceeded, mem_exceeded, time_used, mem_used = json.loads(client.recv(1024).decode())
        if success:
            self.logger.info('Sandbox run successfully finished.')
        return success, time_exceeded, mem_exceeded, time_used, mem_used

    def close(self):
        pass


class Communicator:

    """
    This class does all communicate with the manager node
    """

    def __init__(self, managerAddr, mysqlPort, mysqlUsr, mysqlPasswd, mysqlDb):
        self.logger = constructLogger('Communicator', logFile)
        self.managerAddr = managerAddr
        self.mysqlConn = pymysql.connect(host=managerAddr,
                                         port=int(mysqlPort),
                                         user=mysqlUsr,
                                         password=mysqlPasswd,
                                         db=mysqlDb,
                                         charset='utf8',
                                         cursorclass=pymysql.cursors.DictCursor)

    def fetchInfo(self, submission):  # Fetch info from database
        try:
            with self.mysqlConn.cursor() as cursor:
                sql = "SELECT `Problem`.`problemId` AS `problemId`, `timeLimit`, `memLimit` " + \
                      "FROM `Submit`, `Problem` WHERE " + \
                      "`submitId`=%s AND `Submit`.`problemId`=`Problem`.`problemId`;"
                cursor.execute(sql, (str(submission.submissionId, )))
                result = cursor.fetchone()
                self.logger.info('Successfully fetched submission info from database.')
                return result
        except pymysql.DatabaseError:  # TODO: not sure if the error type is correct
            self.logger.error("Database connection error when trying to fetch info!")

    def fetchFile(self, path):  # Fetch file from manager node
        try:
            url = "http://%s/OJ/%s" % (self.managerAddr, path)
            response = requests.get(url)
            self.logger.info('Successfully fetched file from manager.')
            path_dir = '/'.join(path.split('/')[:-1])
            if not os.path.exists(path_dir):
                os.makedirs(path_dir)
            with open(path, 'w') as fetchedFile:
                fetchedFile.write(response.text)
                self.logger.info('Successfully saved to file.')
            return True
        except requests.exceptions.RequestException:
            self.logger.error("Failed to fetch file: %s" % path)
            return False
        except IOError:
            self.logger.error("Failed to save file: %s" % path)
            return False

    def report(self, submission):  # TODO: directly write to database
        # try:
        #     response = requests.post("http://%s/report.php" % self.managerAddr,
        #                              data = content)  # TODO: error handling
        #     return True
        # except requests.exceptions.RequestException:
        #     self.logger.error("Failed to send report!")
        #     return False
        result = submission.result
        if not result.compile_success:
            resultCode = 'Compile Error'
        else if not result.run_success:
            resultCode = 'Runtime Error'
        else if not result.compare_success:
            resultCode = 'Wrong Answer'
        else if result.time_exceeded:
            resultCode = 'Time Exceeded Error'
        else if result.mem_exceeded:
            resultCode = 'Memory Exceeded Error'
        else:
            resultCode = 'Accepted'

        try:
            with self.mysqlConn.cursor() as cursor:
                sql = "UPDATE `Submit` SET  `runTime`=%d, `memUsed`=%d, `result`=%s " + \
                      "WHERE `submitId`=%d;"
                cursor.execute(sql, (result.time_used, result.mem_used, resultCode, submission.submissionId))
            self.mysqlConn.commit()
            self.logger.info('Successfully written result to database.')
            return True
        except pymysql.DatabaseError:  # TODO: not sure if the error type is correct
            self.logger.error("Database connection error when trying to report!")
            return False

    def close(self):
        self.mysqlConn.close()


class Compiler:

    """
    This class deals with compilation
    """

    def __init__(self, compiler, args):
        self.logger = constructLogger('Compiler', logFile)
        self.compiler = compiler
        self.args = args

    def compile(self, src, bin):  # Return bool
        cmdList = [self.compiler, self.args, '-o', bin, src]
        retcode = call([self.compiler, self.args, '-o', bin, src])
        if retcode == 0:
            self.logger.info('Compiled successfully.')
        else:
            self.logger.error('Compilation failed!')
        return retcode == 0


class Comparer:

    """
    This class is responsible for comparing user program output with stdout
    """

    def __init__(self, args):
        self.logger = constructLogger('Comparer', logFile)
        self.args = args

    def compare(self, stdout, usrout):  # Return bool
        retcode = call(['diff', args, stdout, usrout])
        if retcode == 0:
            self.logger.info('Answer is correct.')
        else:
            self.logger.info('Answer is incorrect.')
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
