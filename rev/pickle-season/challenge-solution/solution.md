*This is very condensed writeup/solution as there is limit for length... So sorry if it feels too rushed. :)*

- Pickle rev, yay!
- `pickle` is basically a VM machine (that is why there is big red message in `pickle` documentation about unpickling untrusted data), so you can do lots of interesting stuff with it...
- Basically two ways to solve it:
    - Hard one (intended when I created the challenge but then during testing I found an easy way to deal with this):
        1. Disassemble pickle code/data (e.g. with `pickletools` (but patch is needed as `pickletools` are not happy about hand-written pickle code))
        2. Write custom `pickle` debugger
        3. ??? (~~magic needed~~ very hard work here (and in step before))
        4. Profit
    - Easy one - [`fickling`](https://github.com/trailofbits/fickling) and "decompile" it to atleast somewhat "sane" Pyhton code

- Decompilation with `fickling` (output is not nice (or even runable) Python but we can work with that):
```sh
pip install fickling
grep -Po '(?<=data = ").*(?=")' pickle_season.py | xxd -ps -r > pickle.bin
fickling pickle.bin > decompiled.py
```

- Get rid of strange `_varXY = _var0; _varXY.__setstate__((None, {'SOMETHING': ...}}))` constructs (these are created by `fickling` as it is (also) quite confused about hand-written pickle code) by replacing them with `SOMETHING = ...`
- Get rid of `from t import something.whatever` (useless and not even valid Python syntax)
- Now we have runable code
- Do actual reversing... (but this is actually very simple step as there isn't really much going on after cleanups)
- Code can be rewriten as:
```py
i = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -42]
i.extend(map(ord, input()))

d = { ... } # Weird nested dict
x = 735
for _ in range(29):
    x ^= i.pop()
    d = d.get(x, {})

print(d.get(None, 'Wrong flag... :('))
```
- Reverse that:
```py
d = {674: {716: {764: {655: {699: {648: {763: {676: {663: {763: {656: {755: {706: {658: {717: {675: {658: {717: {672: {656: {756: {711: {693: {645: {711: {700: {753: {679: {746: {None: 'Correct!'}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
x = 735

output = ""
while None not in d:
    k = next(iter(d.keys())) # Get current value
    output += chr(x^k) # Get correct char
    x = k # Set next key
    d = d[k] # Traverse to next dict

print(output[::-1]) # Flag is checked from the end
```

