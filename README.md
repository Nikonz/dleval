[This readme is outdated. It is related to the \`api' branch version]

# dleval
New and fancy exercises evaluation system for the "Deep Learning" course!

...[Work in progress]...


### How to try:

Create a token (https://sandbox.moodledemo.net/login/token.php?username=teacher&password=sandbox&service=moodle_mobile_app)
and put it to config.yaml.

Login as a teacher (https://sandbox.moodledemo.net/login/).

Create a new assignment (add an activity or resourse) for the course (https://sandbox.moodledemo.net/course/view.php?id=2). Choose "Manually" for the "Attempts reopened" field in the "Submission setting" section.

Login as a student and make a submission.

```
python dleval.py
```

???

PROFIT!
