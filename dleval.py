import logging
import sys
import traceback
import yaml

from argparse import ArgumentParser
from time import time, sleep

from moodle.client import Client
from eval.evaluator import Evaluator

DEFAULT_CONFIG_PATH = 'config.yml'
DEFAULT_INTERVAL = 120

DEFAULT_MOODLE_DATA_PATH = './moodle/data'
DEFAULT_TIMEOUT = 2
DEFAULT_MAX_RETRIES = 2

DEFAULT_EVAL_DATA_PATH = './eval/data'

LOG_LEVELS = {'critical' : logging.CRITICAL,
              'error'    : logging.ERROR,
              'warning'  : logging.WARNING,
              'info'     : logging.INFO,
              'debug'    : logging.DEBUG}

class DlEval:
    def __init__(self, config_path, log_level='info'):
        """
        :param str config_path: path to config file
        """
        self.__logger = logging.getLogger()
        self.__logger.setLevel(LOG_LEVELS[log_level])
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s]: %(message)s ' \
                '(%(module)s:%(funcName)s:%(lineno)d)')
        ch.setFormatter(formatter)
        self.__logger.addHandler(ch)

        with open(config_path, 'r') as ymlfile:
            self.__cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

        self.__client = Client(
                self.__cfg['moodle'].get('data_path', DEFAULT_MOODLE_DATA_PATH),
                self.__logger,
                self.__cfg['moodle'].get('timeout', DEFAULT_TIMEOUT),
                self.__cfg['moodle'].get('max_retries', DEFAULT_MAX_RETRIES))

        eval_data_path = DEFAULT_EVAL_DATA_PATH
        if 'eval' in self.__cfg and 'data_path' in self.__cfg['eval']:
            eval_data_path = self.__cfg['eval']['data_path']
        self.__evaluator = Evaluator(eval_data_path, self.__logger)

    def run(self):
        try:
            ok = self.__client.login(
                    self.__cfg['moodle']['username'],
                    self.__cfg['moodle']['password'])
            if not ok:
                self.__logger.critical('login failed')
            else:
                allowed_assignments = \
                        self.__evaluator.get_allowed_assignments()
                course_data = self.__client.download_new_course_data(
                        self.__cfg['moodle']['course_id'],
                        allowed_assignments)
                self.__evaluator.evaluate(course_data)
                self.__client.send_feedback(course_data)
        except:
            tback = ''.join(traceback.format_exception(*sys.exc_info()))
            self.__logger.critical('an exception occured!\n' + tback)
            sleep(self.__cfg.get('interval', DEFAULT_INTERVAL))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH,
            help='path to config (default=`config.yml\'')
    parser.add_argument('--log-level', default='info',
            help='`critical\', `error\', `warning\', `info\', `debug\' ' \
            '(default=`info\')')
    args = parser.parse_args()

    dleval = DlEval(args.config, args.log_level)
    dleval.run()
