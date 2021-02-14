import logging
LOG_FORMAT = '%(threadName)s | %(filename)s | %(lineno)d | %(asctime)s | %(levelname)s | %(message)s'

logging.basicConfig(filename='/root/client/server/logs/main.log',
    level=logging.INFO,
    format=LOG_FORMAT,
    # filemode='w' # to create new log files instead of overwrite
    )

logFormatter = logging.Formatter(LOG_FORMAT)


logger = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)

logger.addHandler(consoleHandler)