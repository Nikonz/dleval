import pandas as pd
from robobrowser import RoboBrowser
import webbrowser
from tabulate import tabulate
import getpass
from pyfiglet import Figlet

from bs4 import BeautifulSoup

#import configparser
#import config

# TODO to config

CAS_URL = 'https://cas.zimt.uni-siegen.de/cas/login'
CAS_USERNAME = 'g051326'
CAS_PASSWORD = '-------'

MOODLE_WEBSITE = 'https://moodle.uni-siegen.de/'
COURSE_ID = 21642

class scrap:
    def __init__(self, moodle_website):
        self.__moodle_website = moodle_website
        #self.__browser = RoboBrowser(parser='html.parser')
        self.__browser = RoboBrowser(parser='html.parser',
                user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:76.0)')
                #user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                #(KHTML, like Gecko) Ubuntu Chromium/81.0.4044.122 \
                #Chrome/81.0.4044.122 Safari/537.36' \
                #'Gecko/20100101 Firefox/76.0')
        self.__data = pd.DataFrame()

    def cas_login(self, url, username, password):
        self.__browser.open(url)
        #login_form = browser.get_form(id='fml')
        login_form = self.__browser.get_forms()[0]
        print(login_form)
        login_form['username'].value = username
        login_form['password'].value = password
        self.__browser.submit_form(login_form)

    def get_main_page(language='en'):
        template = self.__moodle_website + 'my/index.php?lang={}'
        return template.format(language)

    def get_course_main_page(self, course_id):
        template = self.__moodle_website + 'course/view.php?id={}'
        return template.format(course_id)

    def get_assignment_page(self, assign_id):
        template = self.__moodle_website + '/mod/assign/view.php?id={}'
        return template.format(assign_id)

    def get_view_submissions_page(self, assign_id):
        return self.__get_assignment_page(assign_id) + '&amp;action=grading'

    def get_grade_page(self, assign_id):
        return self.__get_assignment_page(assign_id) + '&amp;action=grader'

    def download_assignment(self, assign_id):
        self.__browser.open(self.get_assignment_page(assign_id))

    def __download_section(self, section):
        for assign in section.find_all(class_='activity assign modtype_assign'):
            assign_id = assign['id'].split('-')[1]
            #print(self.__browser.select('.page-header-headings')[0].h1.string)
            self.download_assignment(assign_id)

    def add_course_new_info(self, course_id):
        #self.__browser.open('https://moodle.uni-siegen.de/mod/assign/view.php?id=497517&rownum=0&action=grader&userid=58491')
        self.__browser.open('https://moodle.uni-siegen.de/mod/assign/view.php?id=498312&action=grader&userid=59637')
        with open('tmp.txt', 'w') as f:
            f.write(str(self.__browser.parsed))
            #f.write(str(self.__browser.response.content))
            #print(self.__browser.response.content)
            #print(self.__browser.parsed)
        x = self.__browser.find(class_="sr-only sr-only-focusable")
        print(x)
        forms = self.__browser.get_forms()
        print(forms)
        return

        self.__browser.open(self.get_course_main_page(course_id))
        course_name = self.__browser.select('.page-header-headings')[0].h1.string
        for section in self.__browser.find_all(class_='section main clearfix'):
            self.__download_section(section)

def try_robobrowser():
    client = scrap(MOODLE_WEBSITE)
    client.cas_login(CAS_URL, CAS_USERNAME, CAS_PASSWORD)
    #print(client.get_course_name(COURSE_ID))
    client.add_course_new_info(COURSE_ID)

#try_robobrowser()
