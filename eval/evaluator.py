import docker
import os

import utils

DOCKER_DIR = './eval/docker'
DOCKER_BUILD_DIR = os.path.join(DOCKER_DIR, 'build')

IMAGE_NAME = 'dleval_submission'
CONTAINER_NAME = 'dleval_submission'

class Evaluator:
    def __init__(self, data_path):
        self.__docker = docker.from_env()
        self.__data_path = data_path

    def evaluate(self, course_data):
        """
        :param moodle.objects.Course feedback: course data
        """
        for assign in course_data.assignments():
            for subm in assign.submissions():
                self.__eval_submission(subm, assign)

    def __eval_submission(self, subm, assign):
        utils.remove_dir(DOCKER_BUILD_DIR)
        utils.make_dir(DOCKER_BUILD_DIR)

        print(DOCKER_BUILD_DIR, assign.name)

        subm_evaluator_path = os.path.join(self.__data_path, assign.id)
        if not os.path.isdir(subm_evaluator_path):
            subm_evaluator_path = os.path.join(self.__data_path, assign.name)
        if not os.path.isdir(subm_evaluator_path):
            # TODO log
            return

        utils.copy_file(os.path.join(DOCKER_DIR, 'eval_launcher.py'),
                DOCKER_BUILD_DIR)
        # TODO subdirs
        utils.copy_all_files(subm.path, DOCKER_BUILD_DIR)
        utils.copy_all_files(subm_evaluator_path, DOCKER_BUILD_DIR)

        with open(os.path.join(DOCKER_BUILD_DIR, 'Dockerfile'), 'w') as dfile:
            dfile.write('FROM dleval\n' +
                    'COPY . .\n' +
                    'CMD python eval_launcher.py\n')
        self.__docker.images.build(path=DOCKER_BUILD_DIR,
                tag=IMAGE_NAME, rm=True, forcerm=True)
        # TODO log image id
        # TODO handle stderr
        stdout = self.__docker.containers.run(IMAGE_NAME, name=CONTAINER_NAME)
        try:
            container = self.__docker.containers.get(CONTAINER_NAME) # ugly
            container.remove()
        except:
            # TODO log
            print('CONTAINER!')
            pass

        try:
            self.__docker.images.remove(IMAGE_NAME, force=True)
        except:
            print('IMAGE!')
            pass

        parsed_result, ok = utils.parse_json(stdout)
        print(stdout)
        if not ok:
            #self.logger.warning('parse_json_failed, skip' + log_msg_suffix)
            print(1)
            return
        if parsed_result is None:
            #self.logger.error('unexpected empty response' + log_msg_suffix)
            print(2)
            return

        grade = parsed_result.get('grade')
        if grade is None:
            #self.logger.error('no grade' + log_msg_suffix)
            return

        comment = parsed_result.get('comment');
        if comment is None:
            #self.logger.error('no explanation' + log_msg_suffix)
            return

        subm.grade = grade
        subm.comment = comment
