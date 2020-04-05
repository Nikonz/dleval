import json
import logging
import subprocess

class Client:
    def __init__(self, token, domain, course_id):
        self.token = token
        self.domain = domain
        self.course_id = course_id
        self.assignments = None
        self.submissions = None

        self.logger = logging.getLogger()
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(funcName)s: ' \
                '%(message)s (%(module)s:%(lineno)d)')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def __parse_json(self, data):
        return json.loads(data)

    def __run_php(self, path, args):
        try:
            result = subprocess.check_output(
                ['php', path, self.token, self.domain] + args,
            )
            return self.__parse_json(result.stdout)
        except Exception as e:
            if hasattr(e, 'message'):
                raise type(e)('run_php: ' +  e.message)
            else:
                raise type(e)('run_php: ' + str(e))

    def __update_assignments(self):
        try:
            args = [str(self.course_id)]
            resp = self.__run_php("php/get_assignments.php", args)
            self.assignments = resp["courses"][0]["assignments"]
        except Exception as e:
            if hasattr(e, 'message'):
                self.logger.error(e.message)
            else:
                self.logger.error(str(e))
            self.assignments = None

    def __get_submissions(self):
        self.__update_assignments()
        # TODO check whether assingments & submissions are old
        args = [str(asgn["id"]) for asgn in self.assignments]
        submissions = self.__run_php('php/get_submissions.php', args)
        failed = not submissions or 'exception' in submissions
        return None if failed else submissions["assignments"]

    def download_new_submissions(self):
        new_submissions = self.__get_submissions();
        # TODO check None
        print(new_submissions)
        for asgn in self.submissions:
            print(asgn)
        self.submissions = new_submissions
