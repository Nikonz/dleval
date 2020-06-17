import docker
import os

import utils

DOCKER_DIR = './eval/docker'
DOCKER_BUILD_DIR = os.path.join(DOCKER_DIR, 'build')

IMAGE_NAME = 'dleval_submission'
CONTAINER_NAME = 'dleval_submission'

class Evaluator:
    def __init__(self, data_path, logger):
        self.__data_path = data_path
        self.__logger = logger
        self.__docker = docker.from_env()

    def get_allowed_assignments(self):
        assignments = set()
        for name in os.listdir(self.__data_path):
            path = os.path.join(self.__data_path, name)
            eval_path = os.path.join(path, 'eval.py')
            if os.path.isfile(eval_path):
                assignments.add(name)
        return assignments

    def evaluate(self, course_data):
        """
        :param moodle.objects.Course feedback: course data
        """
        for assign in course_data.assignments():
            self.__logger.info('Evaluating assignment submissions ' \
                    '[id={}, name={}]'.format(assign.id, assign.name))
            for subm in assign.submissions():
                if self.__eval_submission(subm, assign):
                    comment_line = '\\n'.join(subm.comment.split('\n'))
                    self.__logger.info('Submission was evaluated: ' \
                            'grade={}, comment=`{}\' ' \
                            '[user_id={}, username=`{}\', timestamp={}]'.format(
                            subm.grade, comment_line,
                            subm.user_id, subm.username, subm.timestamp))
                else:
                    self.__logger.warning('Submission was NOT evaluated ' \
                            '[user_id={}, username=`{}\', timestamp={}]'.format(
                            subm.user_id, subm.username, subm.timestamp))

    def __eval_submission(self, subm, assign):
        utils.remove_dir(DOCKER_BUILD_DIR)
        utils.make_dir(DOCKER_BUILD_DIR)

        allowed_assignments = self.get_allowed_assignments()
        subm_evaluator_path = ''

        if assign.id in allowed_assignments:
            subm_evaluator_path = os.path.join(self.__data_path, assign.id)
        elif assign.name in allowed_assignments:
            subm_evaluator_path = os.path.join(self.__data_path, assign.name)
        else:
            self.__logger.error('Evaluator was not found for assignment ' \
                    '[id={}, name=`{}\']'.format(assign.id, assign.name))
            return False

        utils.copy_file(os.path.join(DOCKER_DIR, 'eval_launcher.py'),
                DOCKER_BUILD_DIR)
        # TODO subdirs
        utils.copy_all_files(subm.path, DOCKER_BUILD_DIR)
        utils.copy_all_files(subm_evaluator_path, DOCKER_BUILD_DIR)

        with open(os.path.join(DOCKER_BUILD_DIR, 'Dockerfile'), 'w') as dfile:
            dfile.write('FROM dleval\n' +
                    'COPY . .\n' +
                    'CMD python eval_launcher.py\n')
        try:
            self.__docker.images.build(path=DOCKER_BUILD_DIR,
                    tag=IMAGE_NAME, rm=True, forcerm=True)
        except Exception as e:
            errmsg = e.message if hasattr(e, 'message') else str(e)
            self.__logger.critical('Can not build docker image, reason=`{}\', ' \
                    'have you forgotten `sudo\' or `newgrp docker\'? ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    errmsg, subm.user_id, subm.username, subm.timestamp))
            return False
        # TODO log image id ?
        # TODO handle stderr
        stdout = self.__docker.containers.run(IMAGE_NAME, name=CONTAINER_NAME)
        try:
            container = self.__docker.containers.get(CONTAINER_NAME) # ugly
            container.remove()
        except:
            self.__logger.error('Can not remove docker container ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))
        try:
            self.__docker.images.remove(IMAGE_NAME, force=True)
        except:
            self.__logger.error('Can not remove image ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))

        parsed_result, ok = utils.parse_json(stdout, self.__logger)
        if not ok:
            self.__logger.warning('parse_json failed, raw=`{}\' ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))
            return False
        if parsed_result is None:
            self.__logger.error('Response is missing ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))
            return False

        grade = parsed_result.get('grade')
        comment = parsed_result.get('comment');

        if grade is None:
            self.__logger.error('Grade is missing ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))
            return False
        if comment is None:
            self.__logger.error('Comment is missing ' \
                    '[user_id={}, username=`{}\', timestamp={}]'.format(
                    subm.user_id, subm.username, subm.timestamp))
            return False

        subm.grade = grade
        subm.comment = comment
        return True
