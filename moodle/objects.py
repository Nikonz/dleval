
class Course:
    def __init__(self, id, name):
        self.__id = id
        self.__name = name
        self.__assignments = []

    def add_assignment(self, assignment):
        if not isinstance(assignment, Assignment):
            raise(TypeError('expected {}, got {}'.format(
                    Assignment, type(assignment))))
        self.__assignments.append(assignment)

    def assignments(self):
        return iter(self.__assignments)

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

class Assignment:
    def __init__(self, id, name):
        self.__id = id
        self.__name = name
        self.__submissions = set()

    def add_submission(self, submission):
        if not isinstance(submission, Submission):
            raise(TypeError('expected {}, got {}'.format(
                    Submission, type(submission))))
        self.__submissions.add(submission)

    def submissions(self):
        return iter(self.__submissions)

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

class Submission:
    def __init__(self, user_id, username, timestamp, path):
        self.__user_id = user_id
        self.__username = username
        self.__timestamp = timestamp
        self.__path = path
        self.__grade = None
        self.__comment = None

    def __hash__(self):
        return hash((self.__user_id, self.__timestamp))

    def __eq__(self, other):
        if isinstance(other, tuple):
            return (self.__user_id, self.__timestamp) == other
        return (self.__user_id, self.__timestamp) == \
                (other.__user_id, other.__timestamp)

    @property
    def user_id(self):
        return self.__user_id

    @property
    def username(self):
        return self.__username

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def path(self):
        return self.__path

    @property
    def grade(self):
        return self.__grade

    @property
    def comment(self):
        return self.__comment

    @grade.setter
    def grade(self, grade):
        self.__grade = grade

    @comment.setter
    def comment(self, comment):
        self.__comment = comment
