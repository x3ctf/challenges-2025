# Fastcrypto

## TLDR
The main thing to notice here is that NTT doesn't actually facilitate normal multiplication, but rather polynomial multiplication. The base of the polynomial was heuristically chosen such that modpow(data, 0x10001, p) would fail ~1% of the time. From there its just RSA-CRT fault attack.

## Multiplication
The modpow in chall.py is bogstandard, aside from one quirk
```python
def modpow(base: int, ex: int, mod: int) -> int:
	ret = 1
	while ex:
		if ex & 1 == 1:
			ret = multiply(ret, base)
			ret %= mod
		base = multiply(base, base)
		base %= mod
		ex >>= 1
	
	return ret
```
multiply doesn't actually do multiplication, rather it turns the inputs it into base $B$ polynomials, and then convolves them together using a NTT implementation written in C++.
This is a problem, as this isn't actually doing normal multiplication, but rather polynomial multiplication over $\mathbb{Z}_{998244353}[x]$, that means that it doesn't carry overflowing results, rather it reduces them modulo the NTT modulus. This messes up the poly to number computation, resulting in a fault.

The polynomial base was chosen to be $B = 7639$, far lower than the NTT modulus $998244353$. This significantly reduces the possibility of overflow, and as such, each $data^e % p$ computation only has about a ~1% chance of triggering a carry that leads to a fault.

Consider the following examples:
$$
	y = 13x + 693 // polynomial representation of 10^5
	z = 13x + 693 // polynomial representation of 10^5
	w = y * z = 169*x^2 + 18018*x + 480249
	// w, when evaluated at B over ZZ is, as one would expect 10^5 * 10^5 = 10^10
$$
$$
	y = 7638*x^17 + 7638*x^16 + 7638*x^15 + 7638*x^14 + 7638*x^13 + 7638*x^12 + 7638*x^11 + 7638*x^10 + 7638*x^9 + 7638*x^8 + 7638*x^7 + 7638*x^6 + 7638*x^5 + 7638*x^4 + 7638*x^3 + 7638*x^2 + 7638*x + 7638 // polynomial representation of B^18 - 1
	z = 7638*x^17 + 7638*x^16 + 7638*x^15 + 7638*x^14 + 7638*x^13 + 7638*x^12 + 7638*x^11 + 7638*x^10 + 7638*x^9 + 7638*x^8 + 7638*x^7 + 7638*x^6 + 7638*x^5 + 7638*x^4 + 7638*x^3 + 7638*x^2 + 7638*x + 7638 // polynomial representation of B^18 - 1
	w = y * z = 58339044*x^34 + 116678088*x^33 + 175017132*x^32 + 233356176*x^31 + 291695220*x^30 + 350034264*x^29 + 408373308*x^28 + 466712352*x^27 + 525051396*x^26 + 583390440*x^25 + 641729484*x^24 + 700068528*x^23 + 758407572*x^22 + 816746616*x^21 + 875085660*x^20 + 933424704*x^19 + 991763748*x^18 + 51858439*x^17 + 991763748*x^16 + 933424704*x^15 + 875085660*x^14 + 816746616*x^13 + 758407572*x^12 + 700068528*x^11 + 641729484*x^10 + 583390440*x^9 + 525051396*x^8 + 466712352*x^7 + 408373308*x^6 + 350034264*x^5 + 291695220*x^4 + 233356176*x^3 + 175017132*x^2 + 116678088*x + 58339044
	// w, when evaluated at B over ZZ is not (B^18 - 1)^2, but rather 61562232534809899595626336280385657414772343257462496793641565566385924959055658638577155425927463708066943966948951047146639523708527871913
$$

For a low enough $B$, the $modpow$ function will never fault, however that would be exceptionally inefficient. To see how the carry overflow problem is fixed, check out the Schönhage–Strassen algorithm.

# Abusing the fault 
The rest of the challenge is pretty straight forward, the RSA encryption is calculated using CRT as follows
$$
	encp = data^e \pmod{p}
	encq = data^e \pmod{q}
	enc = CRT(encp, encq)
$$
However, if either part, but not both, gets corrupted, then we get
$$
	encp = data^e \pmod{p}
	encq = 1232131232123 \pmod{q} // assume this got corrupted
	enc = CRT(encp, 1232131232123)
$$
And thus we can calculate
$$
	mult = data^e - enc \pmod{N}
$$
Notice that normally, $mult = 0 \pmod{p}$ and $mult = 0 \pmod{p}$, and thus $mult = 0 \pmod{N}$. However since encryption mod q got corrupted, we have $mult = 0 \pmod{p}$ and $mult = -1232131232123 \pmod{q}$. Therefore we can recover $p$ by calculating $gcd(mult, N)$
From there, just recover the private key, solve the challenge response, and decrypt the flag. Ez.

FLAG: `x3{so_l0ng_and_th4nks_for_all_the_NTT_43274987298472398}`
