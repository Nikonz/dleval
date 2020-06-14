def get_main_page(domain, lang='de'):
    return 'https://{}/my/index.php?lang={}'.format(domain, lang)

def get_course_main_page(domain, course_id, lang='de'):
    return 'https://{}/course/view.php?id={}&lang={}'.format(
            domain, course_id, lang)

def get_assignment_page(domain, assign_id, lang='de'):
    return 'https://{}/mod/assign/view.php?id={}&lang={}'.format(
            domain, assign_id, lang)

def get_view_submissions_page(domain, assign_id, lang='de'):
    return get_assignment_page(domain, assign_id, lang) + '&action=grading'
