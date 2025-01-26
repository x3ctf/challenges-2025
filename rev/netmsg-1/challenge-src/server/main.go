package main

import (
	crand "crypto/rand"
	"encoding/binary"
	"errors"
	"fmt"
	"log"
	"math/big"
	"net"
	"strings"

	"x3c/common"
)

func main() {
	const ADDRESS = "0.0.0.0:5001"
	server := check1(net.Listen("tcp4", ADDRESS))
	log.Print("server started on " + ADDRESS + "\n")
	for {
		if conn, err := server.Accept(); err == nil {
			log.Printf("connection from %s\n", conn.RemoteAddr())
			go handleConn(conn)
		} else {
			log.Printf("error accepting conn: %s", err)
		}
	}
}

func connectClient(conn net.Conn) (common.Connection, error) {
	clientConn := common.Connection{Conn: conn, CryptKey: []byte(common.KEX_KEY)}

	helloMsg, err := clientConn.RecvMsgID()
	if err != nil {
		return clientConn, err
	}

	if helloMsg.Type != common.MSG_HELLO {
		err = fmt.Errorf("expected hello type, got %d", helloMsg.Type)
		return clientConn, err
	}
	if len(helloMsg.Payload) != 0 {
		err = fmt.Errorf("unexpected hello payload: %x", helloMsg.Payload)
		return clientConn, err
	}

	// generate new client ID
	num, err := crand.Int(crand.Reader, big.NewInt(0xffff))
	if err != nil {
		return clientConn, err
	}
	clientConn.ID = uint16(num.Uint64())

	// send hello + new ID
	err = clientConn.SendMsg(common.Msg{Type: common.MSG_HELLO})
	if err != nil {
		return clientConn, err
	}

	kexMsg, err := clientConn.RecvWrappedID()
	if err != nil {
		return clientConn, err
	}

	if kexMsg.Type != common.MSG_KEX_RSA {
		err = fmt.Errorf("expected KEX RSA message type, got %d", helloMsg.Type)
		return clientConn, err
	}

	var rsaParams common.PayloadRsaPubkey
	_, err = common.BinaryDecode(kexMsg.Payload, binary.LittleEndian, &rsaParams)
	if err != nil {
		return clientConn, err
	}

	newKey := make([]byte, 16)
	_, err = crand.Read(newKey)
	if err != nil {
		return clientConn, err
	}

	var cipheredKey common.PayloadCipheredKey
	cipheredKey.PutKey(newKey, rsaParams.E, rsaParams.N)

	cipheredKeyB, err := common.BinaryAppend(nil, binary.LittleEndian, &cipheredKey)
	if err != nil {
		return clientConn, err
	}

	err = clientConn.SendWrapped(common.Msg{Type: common.MSG_KEX_AES, Payload: cipheredKeyB})
	if err != nil {
		return clientConn, err
	}

	clientConn.CryptKey = newKey

	cryptedHello, err := clientConn.RecvWrappedID()
	if err != nil {
		return clientConn, err
	}

	if cryptedHello.Type != common.MSG_HELLO {
		err = fmt.Errorf("expected crypted hello type, got %d", helloMsg.Type)
		return clientConn, err
	}

	if len(cryptedHello.Payload) != 0 {
		err = fmt.Errorf("unexpected crypted hello payload: %x", cryptedHello.Payload)
		return clientConn, err
	}

	err = clientConn.SendWrapped(common.Msg{Type: common.MSG_HELLO})
	if err != nil {
		return clientConn, err
	}

	return clientConn, nil
}

var Errlogin = errors.New("invalid username/password")

func login(conn common.Connection) (string, error) {
	authMsg, err := conn.RecvWrappedID()
	if err != nil {
		return "", err
	}

	var authPayload common.PayloadAuth
	_, err = common.BinaryDecode(authMsg.Payload, binary.LittleEndian, &authPayload)
	if err != nil {
		return "", err
	}

	userS := strings.Trim(string(authPayload.Username[:]), "\x00")
	passS := strings.Trim(string(authPayload.Password[:]), "\x00")

	// lol hardcoded credentials
	var authedUser string

	if userS == USER1 && passS == PASS1 {
		authedUser = USER1
	}

	if userS == USER2 && passS == PASS2 {
		authedUser = USER2
	}

	if authedUser == "" {
		err = conn.SendWrapped(common.Msg{Type: common.MSG_INNER_ERROR})
		if err == nil {
			err = Errlogin
		}
	} else {
		err = conn.SendWrapped(common.Msg{Type: common.MSG_HELLO})
	}

	return authedUser, err
}

func handleConn(conn net.Conn) {
	defer conn.Close()

	clientConn, err := connectClient(conn)
	if err != nil {
		log.Printf("handshake err: %s", err)
		return
	}

	authedUser, err := login(clientConn)
	if err != nil {
		log.Printf("login err: %s", err)
		return
	}

	for {
		req, err := clientConn.RecvWrappedID()
		if err != nil {
			log.Printf("ui loop err: %s", err)
			return
		}

		switch req.Type {
		case common.MSG_CLOSE: // q
			return

		case common.MSG_INNER_GET_MAILBOX: // m
			var mailbox string
			switch authedUser {
			case USER1:
				mailbox = "hiiiii\nhint\nlole"
			case USER2:
				mailbox = "flag\ngz"
			}

			err = clientConn.SendWrapped(common.Msg{Type: common.MSG_INNER_MAILBOX_RESULTS, Payload: []byte(mailbox)})
			if err != nil {
				log.Printf("error sending mailbox results: %s", err)
				return
			}

		case common.MSG_INNER_GET_MSG: // r
			var body string
			ident := string(req.Payload)
			switch authedUser {
			case USER1:
				switch ident {
				case "hiiiii":
					body = "hello :3 welcome to da chall, hope u have fun"
				case "hint":
					body = "think there might be a way to figure out how to reimplement the flag command functionality based on the binary"
				case "lole":
					body = "hope nobody abuses this service too much :("
				}
			case USER2:
				switch ident {
				case "flag":
					body = "congrats, here is flag 2: " + FLAG2
				case "gz":
					body = "hope you got flag 1 too :)"
				}
			}

			var resp common.Msg
			if body == "" {
				resp = common.Msg{Type: common.MSG_INNER_ERROR, Payload: []byte("invalid ident")}
			} else {
				resp = common.Msg{Type: common.MSG_INNER_MSG_BODY, Payload: []byte(body)}
			}
			err = clientConn.SendWrapped(resp)
			if err != nil {
				log.Printf("error sending message box body: %s", err)
				return
			}

		case common.MSG_INNER_FLAG: // f
			err = clientConn.SendWrapped(common.Msg{Type: common.MSG_INNER_FLAG, Payload: []byte(FLAG1)})
			if err != nil {
				log.Printf("error sending flag: %s", err)
			}

		case common.MSG_INNER_SEND_MSG: // s
			// :)
			err = clientConn.SendWrapped(common.Msg{Type: common.MSG_INNER_ERROR, Payload: []byte("functionality disabled due to abuse")})
			if err != nil {
				log.Printf("error receiving msg: %s", err)
				return
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
