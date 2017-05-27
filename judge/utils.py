"""
This script contains classes and functions that implement the judging process
"""


class Submission:

    """
    This class is the representation of the submission
    """

    def __init__(self, submissionId, comm):
        global logger
        self.comm = comm
        self.compiler = Compiler()
        self.sandbox = Sandbox()
        self.comparer = Comparer()

        info = self.comm.fetchInfo(submissionId)

        # Use info to fill in the following attributes
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
        global logger
        pass

    def run(self, submission):
        pass

    def close(self):
        pass


class Communicator:

    """
    This class does all communicate with the manager node
    """

    def __init__(self, managerAddr):
        global logger
        pass

    def fetchInfo(self, submissionId):  # Fetch info from database
        pass

    def fetchFile(self, path):  # Fetch file from manager node
        pass

    def report(self, content):
        pass

    def close(self):
        pass


class Compiler:

    """
    This class deals with compilation
    """

    def __init__(self):
        global logger
        pass

    def compile(self, submission):
        pass


class Comparer:

    """
    This class is responsible for comparing user program output with stdout
    """

    def __init__(self):
        global logger
        pass

    def compare(self, submission):
        pass


class Logger:

    """
    This class deals with logging related issue
    """

    def __init__(self, logFile):
        pass

    def log(event):
        pass

    def close(self):
        pass


class Config:

    """
    This class parses configuration file
    """

    def __init__(self, configFile):
        self.logFile = None
        self.managerAddr = None
        pass

