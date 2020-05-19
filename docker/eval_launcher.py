import json
import eval

scores = eval.evaluate()
grade = sum(scores.values())
explanation = str(scores)

result = {'grade': grade, 'explanation': explanation}
print(json.dumps(result))
