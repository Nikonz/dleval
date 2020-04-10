import json
import logging
import os
import subprocess

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
        self.updated = {}

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
            self.logger.error('bad php response: no assignments')
        return submissions

    def __download_filearea_files(self, filearea,
                assignment_id, submission_id, log_msg_suffix):
        files = filearea['files']
        if files is None:
            self.logger.error('no files' + log_msg_suffix)
            return False

        dir_path = ('./data/submissions/assignment_%d/submission_%d' % \
                (assignment_id, submission_id))
        os.makedirs(dir_path, exist_ok=True)
        for f in files:
            fpath = dir_path + '/' + f['filename']
            args = [f['fileurl'], fpath]
            resp = self.__run_php('php/download_file.php',
                    args, no_response=True)
            if resp is None:
                self.logger.warning('run_php failed, skip')
                return False
        return True

    def __download_plugin_files(self, plugin,
            assignment_id, submission_id, log_msg_suffix):
        fileareas = plugin.get('fileareas')
        if fileareas is None:
            self.logger.error('no fileareas' + log_msg_suffix)
            return False

        for filearea in fileareas:
            if filearea['area'] == 'submission_files':
                success = self.__download_filearea_files(filearea,
                        assignment_id, submission_id, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download_filearea_files failed, skip ' + log_msg_suffix)
                    return False
                return True
        self.logger.error('no submission files in filearea ' + log_msg_suffix)
        return False

    def __download_submission(self, assignment_id, submission, log_msg_suffix):
        plugins = submission.get('plugins')
        if plugins is None:
            self.logger.error('no plugins ' + log_msg_suffix)
            return False

        submission_id = submission['id']

        for plugin in plugins:
            if plugin['type'] == 'file' and \
                    plugin['name'] == 'File submissions': # XXX check name too ?
                success = self.__download_plugin_files(plugin,
                        assignment_id, submission_id, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download_plugin_files failed, skip ' + log_msg_suffix)
                    return False
                return True
        self.logger.error('no submission files in plugin ' + log_msg_suffix)
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
                #print(submission)
                submission_id = submission['id']
                timestamp = submission['timemodified']
                status = submission['status']

                # TODO log username
                log_msg_suffix = \
                    ' [assignment_id=%d, submission_id=%d, timestamp=%d]' % \
                    (assignment_id, submission_id, timestamp)

                if status == 'new':
                    continue
                if status != 'submitted':
                    self.logger.warning(
                            "unusual status '%s', submission was skipped"
                            % status + log_msg_suffix)
                    continue

                prev_timestamp = \
                        self.updated.get((assignment_id, submission_id), 0)

                if prev_timestamp < timestamp:
                    t = 'new' if prev_timestamp == 0 else 'updated'
                    self.logger.info('got %s submission' % t + log_msg_suffix)

                success = self.__download_submission(
                        assignment_id, submission, log_msg_suffix)
                if not success:
                    self.logger.warning(
                            'download submission failed, skip ' + log_msg_suffix)
                    continue

                self.updated[(assignment_id, submission_id)] = timestamp
                new_submissions.append((assignment_id, submission_id))

        return new_submissions
