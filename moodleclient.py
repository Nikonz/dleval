import json
import logging
import subprocess
import os

class Client:
    def __init__(self, token, domain, course_id):
        self.timeout = 30 # FIXME unused
        # TODO retries
        # TODO normal log messages

        self.token = token
        self.domain = domain
        self.course_id = course_id
        self.assignments = None

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s]: %(message)s ' \
                '(%(module)s:%(funcName)s:%(lineno)d)')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

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
            errmsg = e.message if hasattr(e, 'message') else str(e)
            self.logger.error('bad php response: ' + errmsg)
            print(resp) # FIXME
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
        if not 'assignments' in resp:
            self.logger.error('bad php response: no assignments')
            return None
        return resp['assignments']

    def __download_filearea_files(self, filearea, assignment_id, submission_id,
                timestamp, log_msg_suffix):
        if not 'files' in filearea:
            self.logger.error('no files' + log_msg_suffix)
            return False

        # TODO check timestamp

        # FIXME timestamp
        dir_path = ('./data/submissions/%d/%d' % \
                (assignment_id, submission_id))
        os.makedirs(dir_path, exist_ok=True)
        for f in filearea['files']:
            fpath = dir_path + '/' + f['filename']
            args = [f['fileurl'], fpath]
            resp = self.__run_php('php/download_file.php',
                    args, no_response=True)
            if resp is None:
                # TODO
                self.logger.warning('run_php failed, skip')
                return False
        return True

    def __download_plugin_files(self, plugin, assignment_id, submission_id,
            timestamp, log_msg_suffix):
        if not 'fileareas' in plugin:
            self.logger.error('no fileareas' + log_msg_suffix)
            return False
        for filearea in plugin['fileareas']: # TODO check
            if filearea['area'] == 'submission_files':
                success = self.__download_filearea_files(filearea,
                        assignment_id, submission_id, timestamp, log_msg_suffix)
                if not success:
                    return False
                return True
        # TODO logging
        return False

    def __download_submission(self, assignment_id, submission):
        # TODO log username
        submission_id = submission['id']
        timestamp = submission['timemodified']
        log_msg_suffix = \
            ' [assignment_id=%d, submission_id=%d, timestamp=%d]' % \
            (assignment_id, submission_id, timestamp)

        if not 'plugins' in submission:
            self.logger.error('no plugins ' + log_msg_suffix)
        for plugin in submission['plugins']:
            if plugin['type'] == 'file' and \
                    plugin['name'] == 'File submissions': # XXX check name too ?
                success = self.__download_plugin_files(plugin,
                        assignment_id, submission_id, timestamp, log_msg_suffix)
                if not success:
                    return False
                # TODO logging
                # TODO store
                return True
        # TODO logging
        return False

    def download_new_submissions(self):
        submissions = self.__get_submissions();
        if submissions is None:
            self.logger.warning('get_submissions failed, skip')
            return False

        for assignment in submissions:
            assignment_id = assignment["assignmentid"]
            for submission in assignment['submissions']:
                print(submission)
                success = self.__download_submission(assignment_id, submission)
                if not success:
                    # TODO logging
                    pass
