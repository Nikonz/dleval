from submission import script

def evaluate():
    scores = {}
    try:
        scores["foo"] = (6 if script.foo(3, 4) == 12 else 0)
    except:
        scores["foo"] = 0

    try:
        scores["bar"] = (4 if script.bar(5, 6) == 11 else 0)
    except:
        scores["bar"] = 0

    return scores
