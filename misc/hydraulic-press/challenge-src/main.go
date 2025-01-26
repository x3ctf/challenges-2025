package main

import (
	"bytes"
	"compress/zlib"
	"encoding/ascii85"
	"fmt"
	"io"
	"log"
)

type paddingReader struct {
	prePadding   int
	innerContent []byte
	postPadding  int
}

func (r *paddingReader) Read(p []byte) (n int, err error) {
	length := len(p)
	if length == 0 {
		return 0, nil
	}

	if r.prePadding > 0 {
		padRead := min(r.prePadding, length)
		n += padRead
		r.prePadding -= padRead
		length -= padRead
		copy(p, make([]byte, padRead))
		p = p[padRead:]
	}

	if length == 0 {
		return n, nil
	}

	if len(r.innerContent) > 0 {
		padRead := min(len(r.innerContent), length)
		length -= padRead
		n += padRead
		copy(p, r.innerContent)
		r.innerContent = r.innerContent[padRead:]
		p = p[padRead:]
	}

	if length == 0 {
		return n, nil
	}

	if r.postPadding > 0 {
		padRead := min(r.postPadding, length)
		r.postPadding -= padRead
		n += padRead
		length -= padRead
		copy(p, make([]byte, padRead))
	}

	if n == 0 {
		err = io.EOF
	}

	return n, err
}

func compressN(r io.Reader, w io.Writer, n int) {
	for range n {
		zw := check1(zlib.NewWriterLevel(w, zlib.BestCompression))
		w = zw
		defer zw.Close()
	}

	check1(io.Copy(w, r))
}

func decompressN(r io.Reader, n int) io.Reader {
	for range n {
		zr := check1(zlib.NewReader(r))
		r = zr
		// defer zr.Close()
	}

	return r
}

func trySize(i int) []byte {
	r := paddingReader{
		prePadding:   1 << 40,
		innerContent: []byte("x3c{nesting_is_fun_IDOWxzs3}"),
		postPadding:  1 << 40,
	}
	var buf bytes.Buffer
	compressN(&r, &buf, i)

	return buf.Bytes()
}

func encodeB(b []byte) string {
	out := make([]byte, ascii85.MaxEncodedLen(len(b)))
	length := ascii85.Encode(out, b)
	out = out[:length]
	return string(out)
}

func main() {
	prevResult := 0xfff_ffff_ffff_ffff
	for i := 4; i < 10000; i++ {
		result := trySize(i)
		// fmt.Printf("result for i=%d: %d\n", i, len(result))
		if len(result) >= prevResult {
			// fmt.Printf("best: i=%d, size=%d\n", i-1, prevResult)

			fmt.Println(encodeB(trySize(i - 1)))
			return
		}
		prevResult = len(result)
	}
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
