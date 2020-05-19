import docker
import os
import utils

class Evaluator:
    def __init__(self, logger):
        self.docker = docker.from_env()
        self.logger = logger

    def __build_and_run(self,
            submission_directory, evaluator_directory, log_msg_suffix):
        docker_dir = utils.get_docker_directory()
        docker_build_dir = docker_dir + '/build'
        os.makedirs(docker_build_dir, exist_ok=True)

        # XXX need to do it that way due to the docker context issues
        utils.copy_file(docker_dir + '/eval_launcher.py',
                docker_build_dir, self.logger)
        utils.copy_all_files(submission_directory,
                docker_build_dir, self.logger)
        utils.copy_all_files(evaluator_directory,
                docker_build_dir, self.logger)

        with open(docker_build_dir + '/Dockerfile', 'w') as f:
            f.write('FROM dleval\n' +
                    'COPY . .\n' +
                    'CMD python eval_launcher.py\n')
        self.docker.images.build(path=docker_build_dir, tag='dleval_submission')
        # TODO handle stderr
        # TODO remove container manually on error
        stdout = self.docker.containers.run('dleval_submission', auto_remove=True)

        if len(stdout) == 0:
            self.logger.error('empty container output' + log_msg_suffix)
            return (None, None)

        parsed_result, ok = utils.parse_json(stdout, self.logger)
        if not ok:
            self.logger.warning('parse_json_failed, skip' + log_msg_suffix)
            return (None, None)
        if parsed_result is None:
            self.logger.error('unexpected empty response' + log_msg_suffix)
            return (None, None)

        grade = parsed_result.get('grade')
        if grade is None:
            self.logger.error('no grade' + log_msg_suffix)
            return (None, None)

        explanation = parsed_result.get('explanation');
        if explanation is None:
            self.logger.error('no explanation' + log_msg_suffix)
            return (None, None)

        return (grade, explanation)

    def __evaluate_submission(self,
            assignment_id, user_id, attempt, log_msg_suffix):
        submission_directory = utils.get_submission_directory(
                assignment_id, user_id, attempt)
        evaluator_directory = utils.get_evaluator_directory(assignment_id)

        grade, explanation = self.__build_and_run(
                submission_directory, evaluator_directory, log_msg_suffix)
        if grade is None or explanation is None:
            self.logger.warning('build_and_run failed, skip' + \
                    log_msg_suffix)
        return grade, explanation

    def evaluate(self, submissions):
        results = {}
        for submission in submissions:
            assignment_id, user_id, attempt = submission
            log_msg_suffix = ' [assignment_id=%d, user_id=%d, attempt=%d]' \
                    % (assignment_id, user_id, attempt)

            grade, explanation = self.__evaluate_submission(
                    assignment_id, user_id, attempt, log_msg_suffix)
            if grade is None:
                self.logger.warning('evaluate_submission failed, skip ' + \
                        log_msg_suffix)
                continue

            self.logger.info("grade=%d, explanation=`%s'" %
                    (grade, explanation) + log_msg_suffix)

            # TODO move to php or use advancedgrading
            #plugin_data = [{'assignfeedbackcomments_editor':
            #        [{'text': explanation, 'format': 0}]}]
            plugin_data = []

            if not assignment_id in results:
                results[assignment_id] = []

            results[assignment_id].append({
                    "userid": user_id,
                    "grade": grade,
                    "attemptnumber": attempt,
                    "addattempt": 1,
                    "workflowstate": "Graded",
                    "plugindata": plugin_data})
        return results
