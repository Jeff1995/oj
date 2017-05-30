#!/usr/bin/env python


"""
This is the backend module called by manager node
"""


import sys
import logging
from utils import logFile, constructLogger, Config, Submission, Communicator, Compiler, Sandbox, Comparer


if __name__ == '__main__':

    # Read configuration file
    configFile = 'conf/oj.conf'
    config = Config(configFile)

    # Start logging to file
    logFile = config.logFile
    logger = constructLogger('judge.py', logFile)

    # Get parameters
    submissionId = sys.argv[1]

    # Setup submission
    comm = Communicator(config.managerAddr, config.mysqlPort, config.mysqlUsr, config.mysqlPasswd, config.mysqlDb)
    compiler = Compiler(config.compiler, config.compileArgs)
    sandbox = Sandbox()  # TODO
    comparer = Comparer(config.compareArgs)
    submission = Submission(submissionId, comm, compiler, sandbox, comparer)

    # Test submission
    submission.prepare() and submission.compile() and \
    submission.run() and submission.compare()

    # Report result
    submission.report()

    # Cleaning up
    # submission.close()
    comm.close()
