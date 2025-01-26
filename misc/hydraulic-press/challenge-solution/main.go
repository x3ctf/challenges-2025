package main

import (
	"bytes"
	"compress/zlib"
	"encoding/ascii85"
	"fmt"
	"io"
	"log"
	"os"
)

func decompressN(r io.Reader, n int) io.Reader {
	for range n {
		zr := check1(zlib.NewReader(r))
		r = zr
		// defer zr.Close()
	}

	return r
}

func decodeB(b []byte) []byte {
	ret := make([]byte, len(b))

	ndst, _ := check2(ascii85.Decode(ret, b, true))
	ret = ret[:ndst]
	return ret
}

func allZeroes(b []byte) bool {
	for _, c := range b {
		if c != 0 {
			return false
		}
	}
	return true
}

func getNumCompressions(b []byte) int {
	for i := range 100 {
		var buf bytes.Buffer
		check1(buf.Write(b))

		r := decompressN(&buf, i)
		testBuf := make([]byte, 2)
		check1(r.Read(testBuf))
		if testBuf[0] == 0 && testBuf[1] == 0 {
			return i
		}
	}
	panic("wut")
}

func main() {
	b := check1(os.ReadFile("flag.txt"))
	b = decodeB(b)

	// quickly figure out number of compression layers applied
	compN := getNumCompressions(b)

	var buf bytes.Buffer
	check1(buf.Write(b))
	r := decompressN(&buf, compN)

	// go through the stream until it's not all zeroes
	rBuf := make([]byte, 4096)
	var length int
	for {
		length = check1(r.Read(rBuf))
		if !allZeroes(rBuf[:length]) {
			break
		}
	}

	// get next chunk to ensure flag is not cut off
	rbuf2 := make([]byte, 4096)
	check1(r.Read(rbuf2))
	rBuf = append(rBuf[:length], rbuf2...)

	fmt.Println(string(bytes.Trim(rBuf, "\x00")))

}

func check(err error) {
	if err != nil {
		log.Panicf("error: %s", err)
	}
}

func check1[T any](arg T, err error) T {
	check(err)
	return arg
}

func check2[T any, U any](arg1 T, arg2 U, err error) (T, U) {
	check(err)
	return arg1, arg2
}
