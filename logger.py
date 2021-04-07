import logging
LOG_FORMAT = '%(threadName)s | %(filename)s | %(lineno)d | %(asctime)s | %(levelname)s | %(message)s'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    )

logFormatter = logging.Formatter(LOG_FORMAT)


logger = logging.getLogger()

# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)

# logger.addHandler(consoleHandler)