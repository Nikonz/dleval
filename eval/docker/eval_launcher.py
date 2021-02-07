import contextlib
import json
import os
import eval

with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
    scores = eval.evaluate()
grade = sum(scores.values())

comment = ''
for key, value in scores.items():
    comment += '{}: {}\n'.format(key, value)
if len(comment) > 0:
    comment = comment[:-1]

result = {'grade': grade, 'comment': comment}
print(json.dumps(result))
