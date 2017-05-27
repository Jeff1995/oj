#!/usr/bin/env python


"""
This is the backend module called by manager node
"""


import sys
import logging
from utils import logger, Config, Submission, Communicator
import ipdb


if __name__ == '__main__':

    # Read configuration file
    configFile = 'conf/oj.conf'
    config = Config(configFile)

    # Start logging to file
    handler = logging.FileHandler(config.logFile)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Get parameters
    submissionId = sys.argv[1]

    # Setup submission
    comm = Communicator(config.managerAddr)
    comiler = Compiler(config.compiler, config.compileArgs)
    sandbox = Sandbox()  # TODO
    comparer = Comparer(config.compareArgs)
    submission = Submission(submissionId, comm, compiler, sandbox, comparer)

    # Test submission
    submission.prepare() and submission.compile() and \
    submission.run() and submission.compare()

    # Report result
    submission.report()

    # Cleaning up
    submission.close()
    comm.close()
