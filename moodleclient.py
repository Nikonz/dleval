import json
import os
import subprocess
import utils

class Client:
    def __init__(self, token, domain, course_id, logger):
        # self.timeout = 30 # FIXME unused
        # TODO retries
        # TODO normal log messages

        self.token = token
        self.domain = domain
        self.course_id = course_id
        self.logger = logger

        self.assignments = None
        self.last_attempt = {}

    def __parse_json(self, data):
        try:
            return json.loads(data)
        except Exception as e:
            errmsg = e.message if hasattr(e, 'message') else str(e)
            self.logger.error('can not parse json: ' +
                    errmsg + ' [data=%s]' % data)
            return None

    def __run_php(self, path, args, no_response=False):
        try:
            result = subprocess.check_output(
                ['php', path, self.token, self.domain] + args,
            )
        except Exception as e:
            errmsg = e.message if hasattr(e, 'message') else str(e)
            self.logger.error(errmsg + ' [args=%s]' % args)
            return None

        # FIXME ugly
        if no_response:
            return {}

        parsed_result = self.__parse_json(result)
        if parsed_result is None:
            self.logger.warning('parse_json failed, skip')
            return None
        return self.__parse_json(result)

    def __update_assignments(self):
        args = [str(self.course_id)]
        resp = self.__run_php('php/get_assignments.php', args)
        if resp is None:
            self.logger.warning('run_php failed, skip')
            return False
        try:
            self.assignments = resp['courses'][0]['assignments'] # FIXME
            self.logger.info('got %d assignments' %
                    len(self.assignments))
            return True
        except Exception as e:
            self.logger.error('bad php response: ' + str(resp))
            self.assignments = None
            return False

    def __get_submissions(self):
        success = self.__update_assignments()
        if not success:
            self.logger.warning('update_assignments failed, skip')
            return None

        args = [str(asgn['id']) for asgn in self.assignments]
        resp = self.__run_php('php/get_submissions.php', args)
        if resp is None:
            self.logger.warning('update_assignments failed')
            return None

        submissions = resp.get('assignments')
        if submissions is None:
            self.logger.error('bad php response: no assignments') # FIXME
        return submissions

    def __download_filearea_files(self, filearea,
                assignment_id, user_id, attempt, log_msg_suffix):
        files = filearea['files']
        if files is None:
            self.logger.error('no files' + log_msg_suffix)
            return False

        dir_path = utils.get_submission_directory(
                assignment_id, user_id, attempt)

        os.makedirs(dir_path, exist_ok=True)
        for f in files:
            # TODO download only new files
            fpath = dir_path + '/' + f['filename']
            args = [f['fileurl'], fpath]
            resp = self.__run_php('php/download_file.php',
                    args, no_response=True)
            if resp is None:
                self.logger.warning('run_php failed, skip')
                return False
        return True

    def __download_plugin_files(self, plugin,
            assignment_id, user_id, attempt, log_msg_suffix):
        fileareas = plugin.get('fileareas')
        if fileareas is None:
            self.logger.error('no fileareas' + log_msg_suffix)
            return False

        for filearea in fileareas:
            if filearea['area'] == 'submission_files':
                success = self.__download_filearea_files(filearea,
                        assignment_id, user_id, attempt, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download_filearea_files failed, skip' + log_msg_suffix)
                    return False
                return True
        self.logger.error('no submission files in filearea' + log_msg_suffix)
        return False

    def __download_submission(self, assignment_id, submission, log_msg_suffix):
        plugins = submission.get('plugins')
        if plugins is None:
            self.logger.error('no plugins' + log_msg_suffix)
            return False

        user_id = submission['userid']
        attempt = submission['attemptnumber']

        for plugin in plugins:
            if plugin['type'] == 'file' and \
                    plugin['name'] == 'File submissions': # XXX check name too ?
                success = self.__download_plugin_files(plugin,
                        assignment_id, user_id, attempt, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download_plugin_files failed, skip' + log_msg_suffix)
                    return False
                return True
        self.logger.error('no submission files in plugin' + log_msg_suffix)
        return False

    def download_new_submissions(self):
        submissions = self.__get_submissions();
        if submissions is None:
            self.logger.warning('get_submissions failed, skip')
            return []

        new_submissions = []
        for assignment in submissions:
            # TODO log assignment names
            assignment_id = assignment["assignmentid"]
            for submission in assignment['submissions']:
                # XXX add group id ?
                submission_id = submission['id']
                user_id = submission['userid']
                status = submission['status']
                attempt = submission['attemptnumber']
                timestamp = submission['timemodified']

                # TODO find a way to log username
                log_msg_suffix = \
                    ' [assignment_id=%d, submission_id=%d, ' \
                    'user_id=%d, attempt=%d, timestamp=%d]' \
                    % (assignment_id, submission_id, user_id, attempt, timestamp)

                if status == 'new' or status == 'draft' or status == 'reopened':
                    continue
                if status != 'submitted':
                    self.logger.warning(
                            "unusual status '%s', submission was skipped"
                            % status + log_msg_suffix)
                    continue

                prev_attempt = \
                        self.last_attempt.get((assignment_id, submission_id), -1)
                if prev_attempt < attempt:
                    t = 'new' if attempt == 0 else 'updated'
                    self.logger.info('got %s submission' % t + log_msg_suffix)

                success = self.__download_submission(
                        assignment_id, submission, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download_submission failed, skip' + log_msg_suffix)
                    continue

                self.last_attempt[(assignment_id, submission_id)] = attempt
                new_submissions.append((assignment_id, user_id, attempt))

        return new_submissions

    def send_results(self, results):
        for assignment_id, grades in results.items():
            args = [str(self.course_id), str(assignment_id),
                    json.dumps(grades)]
            resp = self.__run_php('php/set_grades.php', args)
            if resp is None:
                self.logger.warning('run_php failed, skip' \
                        '[assignment_id=%d]' % assignment_id)
                return False
        return True
