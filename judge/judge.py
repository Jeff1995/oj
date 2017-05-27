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
    managerAddr = config.managerAddr
    submissionId = sys.argv[1]

    # Setup submission
    comm = Communicator(managerAddr)
    submission = Submission(submissionId, comm)

    # Test submission
    submission.prepare() and submission.compile() and \
    submission.run() and submission.compare()

    # Report result
    submission.report()

    # Cleaning up
    submission.close()
    comm.close()
