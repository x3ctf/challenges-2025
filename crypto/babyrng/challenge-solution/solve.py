m = 1 << 64


def shiftxor(n, w):
    return w ^ (w >> n)


def shiftxormult(n, k, w):
    return (shiftxor(n, w) * k) % m


def mix64(z0):
    z1 = shiftxormult(33, 0xff51afd7ed558ccd, z0)
    z2 = shiftxormult(33, 0xc4ceb9fe1a85ec53, z1)
    return shiftxor(33, z2)


def unmix64(z3):
    z2 = shiftxor(33, z3)
    z1 = shiftxor(33, (pow(0xc4ceb9fe1a85ec53, -1, m) * z2) % m)
    return shiftxor(33, (pow(0xff51afd7ed558ccd, -1, m) * z1) % m)


def get_gamma(a, b):
    a = unmix64(a)
    b = unmix64(b)
    return (b - a) % m


ct = bytes.fromhex('070dbb36be2b25fadda85ba68d791dd8ec4626d81ebd338cb13a4f318d98d7102bddd0fd2f22946138e4401fe006e4eb318cabfb034adfac4163e595f2442c7b')
x = 7283898632471611723
y = 9620209372472646369
gamma = get_gamma(x, y)

ks = [mix64((unmix64(x) - (i + 1) * gamma) % m) % 256 for i in range(len(ct))][::-1]
flag = bytes([a ^ b for a, b in zip(ct, ks)])
print(flag.decode())