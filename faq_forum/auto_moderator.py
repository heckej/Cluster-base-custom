from profanity_check import predict_prob
from nostril import nonsense
from cluster import connector as cluster


def offensiveness(sentence):
    """
    Compute and return the probability that the given sentence is offensive.
    Args:
        sentence: The sentence to check

    Returns: The probability that the given sentence is offensive as a float p (1 = offensive, 0 = nice, 0 <= p <= 1)

    """
    profane_prob = predict_prob([sentence])
    return profane_prob[0]


def is_nonsense(sentence):
    """
    Checks if a sentence is nonsense or not.

    Args:
        sentence: The string that is to be checked.

    Returns: True if the string is not nonsense and it contains more than 6 characters

    """
    try:
        return nonsense(sentence)
    except ValueError:
        return False


def _test():
    print(offensiveness("Fuck you"))
    print(offensiveness("Little bitch"))
    print(offensiveness("You can find a coffee machine on the second floor"))
    print(offensiveness("You're so dumb you can't even find a stupid coffee machine"))
    print(offensiveness("Can I fire that bitch, Charles?"))
    print(offensiveness("Where can I find a coffee machine?"))
    print(offensiveness("How can I file a complaint?"))
    # Models aren't perfect, this model does not cover all dialects
    print(offensiveness("Ray is a cunt"))

    # function nonsense returns true if a string has no meaning
    print(nonsense("This should return false."))
    print(nonsense("ZkIOMJSIOJEKLMZKJMELLKS"))
    # Even when concatenating words or using more complicated codes, the model can usually recognize meaningful strings.
    print(nonsense("ioFlXFndrInfo"))
    # according to the documentation the accuracy is 99%
    # text has to be long enough otherwise a ValueError is raised
    print(nonsense("t2shrt"))
