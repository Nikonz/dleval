import logging
import sys
import traceback
import yaml

from time import time, sleep

from moodleclient import Client
from evaluator import Evaluator

class DlEval:
    def __init__(self, config_filename):

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s]: %(message)s ' \
                '(%(module)s:%(funcName)s:%(lineno)d)')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        with open(config_filename, 'r') as ymlfile:
            self.cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

        self.client = Client(
                self.cfg['moodle']['token'],
                self.cfg['moodle']['domain'],
                self.cfg['moodle']['course_id'],
                self.logger)
        self.evaluator = Evaluator(self.logger)

    def run(self):
        while True:
            try:
                new_submissions = self.client.download_new_submissions()
                results = self.evaluator.evaluate(new_submissions)
                self.client.send_results(results) # TODO retries !!
            except Exception:
                # FIXME fstring
                tback = repr(traceback.format_exception(*sys.exc_info()))
                self.logger.critical(
                        'an exception occured!\n' + tback)
            sleep(self.cfg['interval'])

if __name__ == "__main__":
    dleval = DlEval('config.yml')
    dleval.run()
