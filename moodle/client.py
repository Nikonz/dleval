from datetime import datetime
import locale
import os
import pandas as pd
from robobrowser import RoboBrowser

from moodle import utils

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
        :param str: username: ZIMT username
        :param str: password: ZIMT password
        """
        self.__browser.open(CAS_URL)
        print(self.__browser.get_forms())
        login_form = self.__browser.get_forms()[0]
        login_form['username'].value = username
        login_form['password'].value = password
        self.__browser.submit_form(login_form)

    def download_new_submissions(self, course_id):
        """
        :param int course_id: Id of the course (can be found in the course url)
        """
        main_page = utils.get_course_main_page(MOODLE_DOMAIN, course_id)
        self.__browser.open(main_page)
        # course_name = self.__browser.select('.page-header-headings')[0].h1.string

        new_submissions = []
        for section in self.__browser.find_all(class_='section main clearfix'):
            new_submissions.extend(
                    self.__download_section(section, self.__data_path))
        return new_submissions

    def send_feedback(self, feedback):
        """
        :param dict (of dicts) feedback:
                Grades and comments for each submission (key=(user_id, timestamp))
                of each assignment (key=assignment_id)
        """
        for assign_id, assign_data in feedback:
            submissions_page = \
                    utils.get_view_submissions_page(MOODLE_DOMAIN, assign_id)
            self.__browser.open(submissions_page)

            for form in self.__browser.get_forms():
                user_id = self.__parse_grade_form(form)
                if user_id is None:
                    continue

                subm = self.__browser.find(
                        class_='user{} unselected row'.format(user_id))
                # TODO check if still exists
                subm_ts = self.__parse_timestamp(subm.find(class_='cell c7').contents[0])
                if (user_id, subm_ts) not in assign_data:
                    continue

                grade, comment = assign_data[user_id, subm_ts]
                self.__submit_grade_form(form, user_id, grade, comment)

    def __parse_timestamp(self, date_str, date_locale='de_DE.utf8'):
        cur_locale = locale.getlocale()
        locale.setlocale(locale.LC_ALL, date_locale) # XXX install locale
        timestamp = datetime.strptime(
                date_str, '%A, %d %B %Y, %H:%M ').timestamp()
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
        subm_path = os.path.join(path, 'user_' + user_id)

        os.makedirs(subm_path, exist_ok=True)
        for f in subm.find_all(class_='fileuploadsubmission'):
            name = f.a.contents[0]
            link = f.a['href']
            print(path)
            if not self.__download_file(link, os.path.join(subm_path, name)):
                # TODO log
                return False
        return True

    def __download_assignment(self, assign_id, path):
        submissions_page = utils.get_view_submissions_page(MOODLE_DOMAIN, assign_id)
        self.__browser.open(submissions_page)
        table = self.__browser.find(class_='flexible generaltable generalbox')

        new_submissions = []
        for subm in table.tbody.find_all('tr'):
            submitted = subm.find(class_='submissionstatussubmitted')
            graded = subm.find(class_='submissiongraded')
            if submitted is None or graded is not None:
                continue

            subm_ts = self.__parse_timestamp(subm.find(class_='cell c7').contents[0])
            grade_ts = self.__parse_timestamp(subm.find(class_='cell c10').contents[0])
            if subm_ts + 60 < grade_ts: # XXX +60 - in case of delays
                continue

            ok = self.__download_submission(
                    subm, os.path.join(path, 'assignment_' + assign_id))
            if ok:
                user_id = subm['class'][0][4:]
                new_submissions.append((assign_id, user_id, subm_ts))
            else:
                # TODO log
                pass
        return new_submissions

    def __download_section(self, section, path):
        new_submissions = []
        for assign in section.find_all(class_='activity assign modtype_assign'):
            assign_id = assign['id'].split('-')[1]
            new_submissions.extend(self.__download_assignment(assign_id, path))
        return new_submissions

    def __parse_grade_form(self, form):
        user_id = None
        for field in form.keys():
            if field.startswith('quickgrade_comments_'):
                user_id = field.split('_')[-1]
                break
        return user_id

    def __submit_grade_form(self, form, user_id, grade, comment):
        form['quickgrade_' + user_id] = grade
        form['quickgrade_comments_' + user_id] = comment
        self.__browser.submit_form(form)
