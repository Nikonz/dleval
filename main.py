from moodleclient import Client

token = '011159db80017519a17d93afa280f5f4'
domain = 'https://sandbox.moodledemo.net'
course_id = 2

client = Client(token, domain, course_id)
client.download_new_submissions()
