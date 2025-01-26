# Notcrypto Writeup

Opening this up, we see that this takes in a 0x38 byte input (the flag) and then operates on it in 8 byte chunks, and finally compares it to some data

For each 8 byte block, it does 0x1000 iterations of
1. Permute the bytes around
2. Replace each byte by a byte in a lookup table
3. Xor each byte by the current iteration (mod 0x100)

This is called a Subtitution-Permutation network, and it is a very common building block in block cipher (e.g. AES)

There are 2 main faults here:
1. It has very bad diffusion since each byte only affects one byte in the output
2. It is unkeyed, so the cipher can be player back in reverse

This gives rise to three possible solutions
1. Figure out which input byte index affect which output byte index,, this can be done either by recovering the permutation in binja, or by running it with gdb and trying all 8 positions. Then, try all bytes for each index
2. Figure out the permutation as in the first solution, but instead of trying all bytes, just run the Subtitution-Permutation network in reverse
3. Notice that since the Subtitution-Permutation network has no actual diffusion, it reduces down to a substitution cipher which messes up the order of the input a little bit -> reorder input and solve as a substitution cipher
