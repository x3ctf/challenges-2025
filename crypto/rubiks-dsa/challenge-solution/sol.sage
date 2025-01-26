from hashlib import sha256
from tqdm import tqdm

rubik_moves = "B' U  B' R  F2 "
P = Permutation(eval(open("permutation.txt").read())).to_permutation_group_element()
forbidden = [2, 27, 45, 56, 70, 86, 94, 138, 140, 167, 182, 232, 283, 284, 306, 308, 335, 348, 350, 363, 378, 423, 428, 446, 452, 506, 507, 536, 544, 560, 578, 579, 585, 587, 590, 592, 619, 642, 670, 675, 702, 731, 732, 738, 758, 760, 768, 770, 782, 783, 814, 830, 834, 843, 862, 867, 927, 936, 952, 980, 1010, 1038, 1091, 1119, 1148, 1150, 1152, 1170, 1174, 1175, 1188, 1190, 1204, 1206, 1222]
n = 641154303900

def spicy_rubik_pow(k):
    C = RubiksCube().move(rubik_moves * (k % 1260))
    
    return (P * C._state)**k

def hash_to_int(m):
    return int(sha256(m.encode()).hexdigest(), 16) % n

def sign(msg, d):
    k = n
    r_hash = n

    while gcd(k, n) != 1 or gcd(r_hash, n) != 1 or (k % 1260) in forbidden:
        k = randint(2, n - 1)
        r = spicy_rubik_pow(k)
        r_hash = hash_to_int(str(r))
    
    s = pow(k, -1, n) * (hash_to_int(msg) + r_hash*d) % n

    return r, s

precomputation = []

print("doing precomputation...")
for i in range(1260):
    if i in forbidden:
        continue

    C = RubiksCube().move(rubik_moves * i)
    precomputation.append(C._state)

def solve_dlog(Q):
    i = 0
    for C_state in tqdm(precomputation):
        try:
            k = discrete_log(Q, P*C_state)

            return k
        except:
            continue

lines = open("out.txt").readlines()

print("solving for privkeys...")
recovered_privkeys = []
for i in range(32):
    r = PermutationGroupElement(lines[i*2].strip())
    s = int(lines[i*2+1])
    
    k = solve_dlog(r)
    d = (s*k - hash_to_int(f"mvm_{i}")) * pow(hash_to_int(str(r)), -1, n) % n

    recovered_privkeys.append(d)
    print(recovered_privkeys)

def Babai_closest_vector(M, target):
    G = M.gram_schmidt()[0]
    small = target
    for _ in range(1):
        for i in reversed(range(M.nrows())):
            c = ((small * G[i]) / (G[i] * G[i])).round()
            small -= M[i] * c
    return target - small

sums = [int(line.strip()) for line in lines[-4:]]
out = ""

for i in range(0, 16, 4):
    d_i = vector(recovered_privkeys[i:i+4])

    W = diagonal_matrix([2**40] * 2 + [1]*4)
    print(sums[i//4])
    M = matrix([sums[i//4]] + list(-d_i)).transpose().augment(identity_matrix(5))

    reduced_matrix = (M * W).BKZ() / W

    target = vector([0, 1] + [2**6] * 4)
    res = Babai_closest_vector(reduced_matrix, target)
    print(res)
    out += "".join(map(chr, res[2:]))

print("MVM{" + out + "}")
