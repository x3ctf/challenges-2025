package main

import (
	"bufio"
	crand "crypto/rand"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"os"
	"strings"

	"x3c/common"
)

func genPrime(bits int) int64 {
	num := check1(crand.Prime(crand.Reader, bits))
	return num.Int64()
}

type rsaKeypair struct {
	n, e, d uint32
}

func genRSA() rsaKeypair {
	p := genPrime(16)
	q := genPrime(16)

	n := p * q
	tot := lcm(p-1, q-1)

	e := int64(65537)
	d := modInv(e, tot)

	return rsaKeypair{
		n: uint32(n),
		e: uint32(e),
		d: uint32(d),
	}
}

func connect(hostPort string) common.Connection {
	conn := check1(net.Dial("tcp4", hostPort))
	serverConn := common.Connection{Conn: conn, CryptKey: []byte(common.KEX_KEY)}

	// exchange hello
	check(serverConn.SendMsg(common.Msg{Type: common.MSG_HELLO, Payload: nil}))
	helloResp := check1(serverConn.RecvMsg())

	if helloResp.Type != common.MSG_HELLO {
		panic("hello fail")
	}

	serverConn.ID = helloResp.ID

	kp := genRSA()
	rsaPayload := common.PayloadRsaPubkey{E: kp.e, N: kp.n}
	rsaPayloadB := check1(common.BinaryAppend(nil, binary.LittleEndian, &rsaPayload))

	check(serverConn.SendWrapped(common.Msg{Type: common.MSG_KEX_RSA, Payload: rsaPayloadB}))
	kexResp := check1(serverConn.RecvWrapped())

	if kexResp.Type != common.MSG_KEX_AES {
		panic("kex fail")
	}

	var cipheredKey common.PayloadCipheredKey
	check1(common.BinaryDecode(kexResp.Payload, binary.LittleEndian, &cipheredKey))
	serverConn.CryptKey = cipheredKey.GetKey(kp.d, kp.n)

	check(serverConn.SendWrapped(common.Msg{Type: common.MSG_HELLO}))
	cipheredResp := check1(serverConn.RecvWrapped())

	if cipheredResp.Type != common.MSG_HELLO {
		panic("ciphered hello fail")
	}

	return serverConn
}

func getLine(prompt string) string {
	fmt.Print(prompt)
	reader := bufio.NewReader(os.Stdin)
	s := check1(reader.ReadString('\n'))
	s = strings.Trim(s, "\r\n ")
	return s
}

func login(conn common.Connection) {
	var auth common.PayloadAuth
	username := getLine("username: ")
	password := getLine("password: ")

	copy(auth.Username[:], []byte(username))
	copy(auth.Password[:], []byte(password))
	encoded := check1(common.BinaryAppend(nil, binary.LittleEndian, &auth))

	check(conn.SendWrapped(common.Msg{Type: common.MSG_INNER_USERNAME_PASSWORD, Payload: encoded}))

	loginResp := check1(conn.RecvWrapped())
	if loginResp.Type != common.MSG_HELLO {
		panic("login failed")
	}
}

func main() {
	if len(os.Args) < 3 {
		fmt.Printf("usage: %s <host> <port>", os.Args[1])
		return
	}

	host := os.Args[1]
	port := os.Args[2]
	hostPort := net.JoinHostPort(host, port)

	conn := connect(hostPort)
	defer conn.Conn.Close()

	login(conn)

	for {
		fmt.Print("\nselect option\n[m] view message box\n[f] get flag\n[r] read message from message box\n")
		fmt.Print("[s] send message to another user\n[q] quit\n\n")
		var input string
		for len(input) == 0 {
			input = getLine("> ")
		}

		switch input {
		default:
			fmt.Println("unexpected input")

		case "q":
			check(conn.SendWrapped(common.Msg{Type: common.MSG_CLOSE}))
			return

		case "m":
			check(conn.SendWrapped(common.Msg{Type: common.MSG_INNER_GET_MAILBOX}))
			resp := check1(conn.RecvWrapped())
			if resp.Type != common.MSG_INNER_MAILBOX_RESULTS {
				panic("expected mailbox results")
			}

			fmt.Printf("mailbox results\n%s\n", string(resp.Payload))

		case "f":
			fmt.Println("functionality temporarily disabled")

		case "r":
			ident := getLine("enter message identifier of message to fetch: ")

			check(conn.SendWrapped(common.Msg{Type: common.MSG_INNER_GET_MSG, Payload: []byte(ident)}))

			resp := check1(conn.RecvWrapped())
			if resp.Type == common.MSG_INNER_MSG_BODY {
				fmt.Printf("message %q:\n%s\n", ident, string(resp.Payload))
			} else if resp.Type == common.MSG_INNER_ERROR {
				fmt.Printf("error getting message %q: %s\n", ident, string(resp.Payload))
			} else {
				log.Panicf("unexpected type %d", resp.Type)
			}

		case "s":
			username := getLine("enter username of recipient: ")
			ident := getLine("enter message identifier (16 chars max): ")
			body := getLine("enter message body (single line, 256 chars max): ")

			var privMsg common.PrivMsg
			copy(privMsg.UserName[:], []byte(username))
			copy(privMsg.MsgIdent[:], []byte(ident))
			copy(privMsg.Msg[:], []byte(body))

			payload := check1(common.BinaryAppend(nil, binary.LittleEndian, &privMsg))

			check(conn.SendWrapped(common.Msg{Type: common.MSG_INNER_SEND_MSG, Payload: payload}))
			resp := check1(conn.RecvWrapped())
			if resp.Type == common.MSG_INNER_SEND_MSG_SUCCESS {
				fmt.Println("message sent")
			} else if resp.Type == common.MSG_INNER_ERROR {
				fmt.Printf("error sending message: %s\n", string(resp.Payload))
			} else {
				log.Panicf("unexpected message type %d", resp.Type)
			}
		}
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
