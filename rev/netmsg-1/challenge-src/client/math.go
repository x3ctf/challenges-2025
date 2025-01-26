package main

func gcdExtended(a, b int64) (int64, int64, int64) {
	var u, y, v, x int64 = 1, 1, 0, 0
	for a > 0 {
		q := b / a
		x, u = u, x-q*u
		y, v = v, y-q*v
		b, a = a, b-q*a
	}
	return b, x, y
}

func gcd(a, b int64) int64 {
	ret, _, _ := gcdExtended(a, b)
	return ret
}

func lcm(a, b int64) int64 {
	return a * b / gcd(a, b)
}

func modInv(a, m int64) int64 {
	_, x, _ := gcdExtended(a, m)

	return (m + (x % m)) % m
}
