from moodleclient import Client

token = '927f6d588ca5ce92d7827ca7a5f3b072'
domain = 'https://sandbox.moodledemo.net'
course_id = 2

client = Client(token, domain, course_id)
client.download_new_submissions()
