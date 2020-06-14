import json
import eval

scores = eval.evaluate()
grade = sum(scores.values())

comment = ''
for key, value in scores.items():
    comment += '{}: {},\n'.format(key, value)
if len(comment) > 0:
    comment = comment[:-2]

result = {'grade': grade, 'comment': comment}
print(json.dumps(result))
