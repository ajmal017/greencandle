#pylint: disable=no-member,arguments-differ,too-few-public-methods

"""
Generic logging class for greencandle modules
"""

import logging
from systemd.journal import JournaldLogHandler
from . import config
from .alerts import send_push_notif

class OneLineFormatter(logging.Formatter):
    """logging formatter for exceptions"""
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result

class AppFilter(logging.Filter):
    """
    Add module_name as well as app_name for journald logging
    """

    def __init__(self, module_name, *args, **kwargs):
        self.module_name = module_name
        super(AppFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        record.module_name = self.module_name
        return True

class NotifyOnCriticalStream(logging.StreamHandler):
    """
    Stream handler to send push notifications on error or critical
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            send_push_notif(record.msg)

class NotifyOnCriticalJournald(JournaldLogHandler):
    """
    Journald handler to send push notification on error or critical
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            send_push_notif(record.msg)


def get_logger(module_name=None):
    """
    Get Customized logging instance
      Args:
        logger_name: name of module
      Returns:
        logging instance with formatted handler
    """
    app_name = config.main.name
    logger = logging.getLogger(app_name)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(int(config.main.logging_level))
    logger.propagate = False
    logger.addFilter(AppFilter(module_name=module_name))
    if config.main.logging_output == "journald":
        handler = NotifyOnCriticalJournald()
        formatter = OneLineFormatter('[%(levelname)s] %(module_name)s %(message)s')
        handler.setFormatter(formatter)
    else:
        #handler = logging.StreamHandler()
        handler = NotifyOnCriticalStream()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(module_name)s %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def get_decorator(errors=(Exception,)):
    """logging decorator"""
    logger = get_logger(__name__)
    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.exception("Got Error: ")   # %s %s", str(sys.exc_info()), errors)
                #logger.critical('Function', method.__name__, 'time:', round((te -ts)*1000,1), 'ms')

#                raise

        return new_func

    return decorator
