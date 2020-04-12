import os
import utils

class Evaluator:
    def __init__(self, logger):
        self.logger = logger

    def __build_and_run(self,
            submission_directory, evaluator_directory, log_msg_suffix):
        # TODO docker
        return 100

    def __evaluate_submission(self,
            assignment_id, user_id, attempt, log_msg_suffix):
        submission_directory = utils.get_submission_directory(
                assignment_id, user_id, attempt)
        evaluator_directory = utils.get_evaluator_directory(assignment_id)

        grade = self.__build_and_run(
                submission_directory, evaluator_directory, log_msg_suffix)
        if grade is None:
            self.logger.warning('build_and_run failed, skip' + \
                    log_msg_suffix)
        return grade

    def evaluate(self, submissions):
        results = {}
        for submission in submissions:
            assignment_id, user_id, attempt = submission
            log_msg_suffix = ' [assignment_id=%d, user_id=%d, attempt=%d]' \
                    % (assignment_id, user_id, attempt)

            grade = self.__evaluate_submission(
                    assignment_id, user_id, attempt, log_msg_suffix)
            if grade is None:
                self.logger('evaluate_submission failed, skip ' + \
                        log_msg_suffix)
                continue

            if not assignment_id in results:
                results[assignment_id] = []

            results[assignment_id].append({
                    "userid": user_id,
                    "grade": grade,
                    "attemptnumber": attempt,
                    "addattempt": 1,
                    "workflowstate": "Graded"})
        return results
