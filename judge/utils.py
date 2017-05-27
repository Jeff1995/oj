"""
This script contains classes and functions that implement the judging process
"""


import logging
logger = logging.getLogger('judge.py')
logger.setLevel(logging.DEBUG)


class Submission:

    """
    This class is the representation of the submission
    """

    def __init__(self, submissionId, comm):
        self.comm = comm
        self.compiler = Compiler()
        self.sandbox = Sandbox()
        self.comparer = Comparer()

        info = self.comm.fetchInfo(submissionId)

        # Use info to fill in the following attributes
        self.id = submissionId
        self.cpuLim = None  # TODO: CPU time limit of the corresponding problem
        self.memLim = None  # TODO: Memory limit of the corresponding problem
        self.stdin = None  # TODO: Standard input file path
        self.stdout = None  # TODO: Standard output file path
        self.src = None  # TODO: Submitted source code file path
        self.bin = None  # TODO: Compiled binary file path
        self.usrout = None  # TODO: Output file path of the user program

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

    def prepare(self):  # Fetch src file, fetch IO file if not already exist
        pass

    def compile(self):  # Compile and update self.result
        pass

    def run(self):  # Run the user program and update self.result
        pass

    def compare(self):  # Compare and update self.result
        pass

    def report(self):  # Construct content with self.result and send back
        pass

    def close(self):  # Cleaning up
        pass


class Sandbox:

    """
    This class runs the compiled program in a sandbox and returns result
    """

    def __init__(self):
        pass

    def run(self, submission):
        pass

    def close(self):
        pass


class Communicator:

    """
    This class does all communicate with the manager node
    """

    import os.path
    import requests
    import pymysql.cursors

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
                sql = "SELECT `Problem`.`path` AS `PPATH`, `Submit`.`path` AS `SPATH`, "
                      "`timeLimit`, `memLimit` FROM `Submit`, `Problem` WHERE "
                      "`submitId`=%s AND `Submit`.`problemId`=`Problem`.`problemId`"
                cursor.execute(sql, (str(submission.id,)))
                result = cursor.fetchone()
                # TODO
        except DatabaseError:
            logger.error("Database connection error.")


    def fetchFile(self, path):  # Fetch file from manager node
        if not os.path.isfile(path):
            requests.get()

    def report(self, content):
        pass

    def close(self):
        self.mysqlConn.close()


class Compiler:

    """
    This class deals with compilation
    """

    def __init__(self):
        pass

    def compile(self, submission):
        pass


class Comparer:

    """
    This class is responsible for comparing user program output with stdout
    """

    def __init__(self):
        pass

    def compare(self, submission):
        pass


class Config:

    """
    This class parses configuration file
    """

    def __init__(self, configFile):
        from ConfigParser import ConfigParser
        parser = ConfigParser()
        parser.read(configFile)

        self.logFile = parser.get('log', 'logFile')
        self.managerAddr = parser.get('network', 'managerAddr')
