import random


def check_bad_params(a, b):
    return a < 0 or b < 0


def encrypt(data: str, a: int, b: int, seed: int = None):
    from string import printable

    if check_bad_params(a, b):
        print('a and b must be non-negative integers')
        raise ValueError('a and b must be non-negative integers')

    if seed is None:
        seed = random.randint(1, 10**4)

    abc = list(printable[:-6])
    random.Random(seed).shuffle(abc)
    m = len(abc)
    s = ''
    for c in data:
        s += abc[(abc.index(c) + a) % m]
        t = (a+b, a)
        a = t[0]
        b = t[1]
    return s

globals()['check_bad_params'] = check_bad_params
globals()['encrypt'] = encrypt
