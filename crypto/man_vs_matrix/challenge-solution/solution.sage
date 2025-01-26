# We have 9 samples from the RNG and 9 unknown variables.
# It's easy to realize that the relationship is linear between these unknowns and the given samples.
# After building a symbolic version of the RNG, we can derive the exact system of equations and solve it using matrices.
from Crypto.Util.number import long_to_bytes

R.<s1,s2,s3,s4,s5,s6,s7,s8,s9> = PolynomialRing(ZZ)

p = next_prime(2**24)
F = GF(p)

class RNG:

    def __init__(self):
        self.M = matrix([[s1,s2,s3], [s4,s5,s6], [s7,s8,s9]])
        self.state = vector(map(ord, "Mvm"))

    def get_random_num(self):
        out = self.M * self.state

        for i in range(len(self.state)):
            self.state[i] = pow(2, self.state[i], p)

        return out * self.state

rng = RNG()
A = []

for i in range(9):
    A.append(rng.get_random_num().coefficients())

A = matrix(F, A)
samples = vector(F, [6192533, 82371, 86024, 4218430, 12259879, 16442850, 6736271, 7418630, 15483781])
seed = A.solve_right(samples)

flag = b""

for s in seed:
    flag += long_to_bytes(int(s))

print("MVM{" + flag.decode() + "}")
