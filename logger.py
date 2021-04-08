import logging

SPACING = '\n' * 2
LOG_FORMAT = f'%(threadName)s | %(filename)s | %(lineno)d | %(asctime)s | %(levelname)s | %(message)s {SPACING}'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    )

logFormatter = logging.Formatter(LOG_FORMAT)
logger = logging.getLogger()