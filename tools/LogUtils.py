import logging
import sys
from ColoredLogFormatter import ColoredLogFormatter

class LogUtils():

    @staticmethod
    def initialiseLogger(verbosity: str, filename: str = None):
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, verbosity))

        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(ColoredLogFormatter())
        logger.addHandler(consoleHandler)

        if filename:
            fileHandler = logging.FileHandler(filename, encoding="utf-8")
            fileLogFormat = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
            fileHandler.setFormatter(fileLogFormat)
            logger.addHandler(fileHandler)

        logger.info("Logger initialised")

        return logger
