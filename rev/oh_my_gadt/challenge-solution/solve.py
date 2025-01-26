from pwn import concat, xor

def splitevery(line,n):
    return [line[i:i+n] for i in range(0, len(line), n)]

def rotate(l, n):
    return l[(n%len(l)):] + l[:n%len(l)]

def doManyUnscrambleSteps(bs, i):
    t = bs
    for it in range(i):
        t = doUnscrambleStep(t)
    return t

def doUnscrambleStep(bs):
    def s4Step(i):
        return [xor(*i)[0]] + i[:-1]
    s4 = s4Step(s4Step(s4Step(bs)))
    rs4 = list(reversed(s4))
    hs3 = [e ^ (rs4[i-1] if i != 0 else 0) for (i, e) in enumerate(rs4)]
    s3 = [hs3[0]]+list(reversed(hs3[1:]))

    f = lambda x: (6*x**6+2*x**3+x)%256
    l = [f(x) for x in range(0,256)]
    il = [l.index(x) for x in range(256)]
    s2 = [il[x] for x in s3]
    s1 = concat([rotate(ss,-i) for (i,ss) in enumerate(splitevery(s2,4))])
    return list(bytes(s1))

MODE="int"
if MODE=="int":
    inp = int(input("scrambled: ")) # the big int in the file
    iters = int(input("iters: ")) # how many scramble iterations it does - input 13
    inpArray = [int(x,16) for x in splitevery(hex(inp),2)[1:]]
    print(bytes(doManyUnscrambleSteps(inpArray, iters)).decode("ascii"))
elif MODE=="exparray":
    inp = eval(input("scrambled: "))
    iters = int(input("iters: "))
    print(bytes(doManyUnscrambleSteps(inp, iters)).decode("ascii"))
