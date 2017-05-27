#!/usr/bin/env python


"""
This is the backend module called by manager node
"""


import sys
from utils import Config
from utils import Logger
from utils import Submission
from utils import Communicator


configFile = ''
config = Config(configFile)
logger = Logger(config.logFile)
managerAddr = config.managerAddr
submissionId = sys.argv[1]

comm = Communicator(managerAddr)
submission = Submission(submissionId, comm)

submission.prepare() and submission.compile() and \
submission.run() and submission.compare()

submission.report()

submission.close()
comm.close()
logger.close()
