from datetime import datetime
import locale
import os
import pandas as pd
import shutil

from robobrowser import RoboBrowser

import utils
from moodle.objects import Course, Assignment, Submission
from moodle import utils as moodleutils

CAS_URL = 'https://cas.zimt.uni-siegen.de/cas/login'
MOODLE_DOMAIN = 'moodle.uni-siegen.de'

class Client:
    def __init__(self, data_path, timeout=None, max_retries=None):
        """
        :param str data_path: Where to store submissions
        :param int timeout: Default timeout, in seconds
        :param int max_retries: Number of retries
        """
        self.__data_path = data_path
        self.__browser = RoboBrowser(parser='html.parser',
                timeout=timeout, tries=max_retries, multiplier=1)

    def login(self, username, password):
        """
        :param str username: ZIMT username
        :param str password: ZIMT password
        """
        self.__browser.open(CAS_URL)
        login_form = self.__browser.get_forms()[0]
        login_form['username'].value = username
        login_form['password'].value = password
        self.__browser.submit_form(login_form)

    def download_new_course_data(self, course_id):
        """
        :param int course_id: Id of the course (can be found in the course url)
        """
        main_page = moodleutils.get_course_main_page(MOODLE_DOMAIN, course_id)
        self.__browser.open(main_page)

        course_name = self.__browser.select('.page-header-headings')[0].h1.string
        course_data = Course(course_id, course_name)

        for section in self.__browser.find_all(class_='section main clearfix'):
            for assign in section.find_all(class_='activity assign modtype_assign'):
                assign_id = assign['id'].split('-')[1]
                course_data.add_assignment(
                        self.__download_new_assignment_data(
                        assign_id,
                        self.__data_path))
        return course_data

    def send_feedback(self, course_data):
        """
        :param moodle.objects.Course course_data: course data with grades and comments
        """
        for assign_data in course_data.assignments():
            submissions_page = \
                    moodleutils.get_view_submissions_page(MOODLE_DOMAIN, assign_data.id)
            self.__browser.open(submissions_page)

            options_form = None
            for form in self.__browser.get_forms():
                if self.__is_options_form(form):
                    options_form = form
                    break
            if options_form is None:
                # TODO log
                continue
            if not self.__fill_options_form(options_form):
                # TODO log
                continue
            self.__browser.submit_form(options_form)

            grading_form = None
            for form in self.__browser.get_forms():
                if self.__is_grading_form(form):
                    grading_form = form
                    break
            if grading_form is None:
                # TODO log
                continue

            for subm_data in assign_data.submissions():
                if subm_data.grade is None:
                    continue
                subm = self.__browser.find(
                        class_='user{}'.format(subm_data.user_id))
                if subm is None:
                    continue
                submitted = subm.find(class_='submissionstatussubmitted')
                if submitted is None:
                    continue
                subm_ts = self.__parse_timestamp(
                        subm.find(class_='cell c7').contents[0])
                if subm_data.timestamp != subm_ts:
                    # TODO log
                    continue
                if not self.__fill_grading_form(grading_form, subm_data):
                    # TODO log
                    continue
                # TODO log
            self.__browser.submit_form(grading_form)

    def __parse_timestamp(self, date_str, date_locale='de_DE.utf8'):
        cur_locale = locale.getlocale()
        locale.setlocale(locale.LC_ALL, date_locale) # XXX install locale
        timestamp = datetime.strptime(
                date_str, '%A, %d. %B %Y, %H:%M').timestamp()
        locale.setlocale(locale.LC_ALL, cur_locale)
        return timestamp

    def __download_file(self, link, path):
        resp = self.__browser.session.get(link) # XXX ugly
        if resp.status_code != 200:
            # TODO log
            return False
        with open(path, 'w') as f:
            f.write(resp.content.decode('utf-8'))
        # TODO log
        return True

    def __download_submission(self, subm, path):
        user_id = subm['class'][0][4:]
        timestamp = self.__parse_timestamp(subm.find(class_='cell c7').contents[0])

        subm_path = os.path.join(path, 'user_' + user_id)
        subm_data = Submission(user_id, timestamp, subm_path)

        utils.remove_dir(subm_path)
        utils.make_dir(subm_path)
        for f in subm.find_all(class_='fileuploadsubmission'):
            name = f.a.contents[0]
            link = f.a['href']
            if not self.__download_file(link, os.path.join(subm_path, name)):
                # TODO log
                return None
        return subm_data

    def __download_new_assignment_data(self, assign_id, path):
        submissions_page = moodleutils.get_view_submissions_page(MOODLE_DOMAIN, assign_id)
        self.__browser.open(submissions_page)
        table = self.__browser.find(class_='flexible generaltable generalbox')

        assign_path = os.path.join(path, 'assignment_' + assign_id)
        assign_name = self.__browser.find(role='main').h2.string
        assign_data = Assignment(assign_id, assign_name)

        for subm in table.tbody.find_all('tr'):
            submitted = subm.find(class_='submissionstatussubmitted')
            if submitted is None:
                continue
            graded = subm.find(class_='submissiongraded')
            subm_ts = self.__parse_timestamp(subm.find(class_='cell c7').contents[0])
            grade_ts = self.__parse_timestamp(subm.find(class_='cell c10').contents[0])
            if graded and subm_ts + 60 < grade_ts: # XXX +1 minute - to retest in case of delays
                # FIXME AM PM
                continue
            subm_data = self.__download_submission(subm, assign_path)
            if subm_data is not None:
                assign_data.add_submission(subm_data)
            else:
                # TODO log
                pass
        return assign_data

    def __download_new_section_data(self, section, path):
        section_data = []
        for assign in section.find_all(class_='activity assign modtype_assign'):
            assign_id = assign['id'].split('-')[1]
            section_data.append(self.__download_new_assignment_data(assign_id, path))
        return section_data

    def __is_options_form(self, form):
        for field in form.keys():
            if field == 'quickgrading':
                return True
        return False

    def __fill_options_form(self, form):
        try:
            form['filter'] = ''
            form['perpage'] = '-1'
            form['quickgrading'] = ['1']
            return True
        except:
            return False

    def __is_grading_form(self, form):
        for field in form.keys():
            if field.startswith('quickgrade_'):
                return True
        return False

    def __fill_grading_form(self, form, subm):
        try:
            form['quickgrade_' + subm.user_id] = subm.grade
            # it is necessary to update form even if the data is the same
            old_comment = form['quickgrade_comments_' + subm.user_id].value
            new_comment = subm.comment
            if new_comment is None:
                new_comment = ''
            if new_comment == old_comment:
                new_comment += ' '
            form['quickgrade_comments_' + subm.user_id] = new_comment
            return True
        except:
            return False
