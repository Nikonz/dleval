def get_main_page(domain, language='en'):
    return 'https://{}/my/index.php?lang={}'.format(domain, language)

def get_course_main_page(domain, course_id):
    return 'https://{}/course/view.php?id={}'.format(domain, course_id)

def get_assignment_page(domain, assign_id):
    return 'https://{}/mod/assign/view.php?id={}'.format(domain, assign_id)

def get_view_submissions_page(domain, assign_id):
    return get_assignment_page(domain, assign_id) + '&action=grading'
