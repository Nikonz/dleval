from moodleclient import Client

token = '0f2e75e36edb0e43ddab132c553eaf24'
domain = 'https://sandbox.moodledemo.net'
course_id = 2

client = Client(token, domain, course_id)
client.download_new_submissions()
