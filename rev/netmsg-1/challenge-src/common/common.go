package common

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"crypto/md5"
	"encoding/binary"
	"errors"
	"net"

	"github.com/howeyc/crc16"
)

type MsgType byte

const (
	// print(''.join('\\x' + bytes([b]).hex() for b in os.urandom(16)))
	KEX_KEY = "\x11\x4a\x5b\xc7\x0c\xac\xd5\x8c\xa5\x4d\x70\xc4\x79\x7a\xed\x13"
)

const (
	MSG_HELLO        = iota + 1 // dummy hello message
	MSG_CRYPTED_WRAP            // crypted wrapper (crypted with exchanged AES key)

	MSG_KEX_RSA // kex message (crypted with KEX_KEY, contains RSA pubkey)
	MSG_KEX_AES // kex message (crypted with KEX_KEY, contains RSA-encrypted shared AES key)

	MSG_INNER_USERNAME_PASSWORD // wrapped, contains username and password

	MSG_INNER_GET_MAILBOX     // wrapped, get mailbox info
	MSG_INNER_MAILBOX_RESULTS // mailbox info (just string lol)

	MSG_INNER_FLAG // wrapped, get flag from server lol

	MSG_INNER_GET_MSG // get msg from mailbox by msg_ident
	MSG_INNER_MSG_BODY

	MSG_INNER_SEND_MSG
	MSG_INNER_SEND_MSG_SUCCESS

	MSG_INNER_ERROR

	MSG_CLOSE
)

type PrivMsg struct {
	UserName [16]byte
	MsgIdent [16]byte
	Msg      [256]byte
}

type Msg struct {
	Type MsgType
	ID   uint16
	// Length uint16
	Payload []byte
	// Crc uint16
}

type PayloadRsaPubkey struct {
	E uint32 // 0x10001 lol
	N uint32
}

type PayloadCipheredKey struct {
	Parts [8]uint32
}

type PayloadAuth struct {
	Username [16]byte
	Password [16]byte
}

type Connection struct {
	Conn     net.Conn
	ID       uint16
	CryptKey []byte
}

func (c *Connection) SendWrapped(msg Msg) error {
	msg.ID = c.ID
	serialized, err := msg.MarshalBinary()
	if err != nil {
		return err
	}

	wrapMsg := Msg{Type: MSG_CRYPTED_WRAP, Payload: serialized, ID: msg.ID}
	err = wrapMsg.EncryptPayload(c.CryptKey)
	if err != nil {
		return err
	}

	err = c.SendMsg(wrapMsg)
	if err != nil {
		return err
	}

	return nil
}

var ErrWrap = errors.New("invalid wrapped message")

func (c *Connection) RecvWrapped() (Msg, error) {
	wrapMsg, err := c.RecvMsg()
	if err != nil {
		return wrapMsg, err
	}

	if wrapMsg.Type != MSG_CRYPTED_WRAP {
		return wrapMsg, ErrWrap
	}

	err = wrapMsg.DecryptPayload(c.CryptKey)
	if err != nil {
		return wrapMsg, err
	}

	var wrappedMsg Msg
	err = wrappedMsg.UnmarshalBinary(wrapMsg.Payload)
	if err != nil {
		return wrappedMsg, err
	}

	return wrappedMsg, nil
}

func (c *Connection) RecvWrappedID() (Msg, error) {
	wrapMsg, err := c.RecvMsgID()
	if err != nil {
		return wrapMsg, err
	}

	if wrapMsg.Type != MSG_CRYPTED_WRAP {
		return wrapMsg, ErrWrap
	}

	err = wrapMsg.DecryptPayload(c.CryptKey)
	if err != nil {
		return wrapMsg, err
	}

	var wrappedMsg Msg
	err = wrappedMsg.UnmarshalBinary(wrapMsg.Payload)
	if err != nil {
		return wrappedMsg, err
	}

	if wrappedMsg.ID != c.ID {
		return wrappedMsg, ErrIDMismatch
	}

	return wrappedMsg, nil
}

func (c *Connection) SendMsg(msg Msg) error {
	msg.ID = c.ID
	serialized, err := msg.MarshalBinary()
	if err != nil {
		return err
	}

	_, err = c.Conn.Write(serialized)
	if err != nil {
		return err
	}

	return nil
}

func (c *Connection) RecvMsg() (Msg, error) {
	var ret Msg
	// type, id, length
	initialBuf := make([]byte, 5)
	_, err := c.Conn.Read(initialBuf)
	if err != nil {
		return ret, err
	}

	payloadLen := binary.LittleEndian.Uint16(initialBuf[3:])
	payloadCRC := make([]byte, payloadLen+2)
	_, err = c.Conn.Read(payloadCRC)
	if err != nil {
		return ret, err
	}

	buf := append(initialBuf, payloadCRC...)
	err = ret.UnmarshalBinary(buf)
	if err != nil {
		return ret, err
	}

	return ret, nil
}

var ErrIDMismatch = errors.New("msg ID mismatch")

func (c *Connection) RecvMsgID() (Msg, error) {
	msg, err := c.RecvMsg()
	if err != nil {
		return msg, err
	}

	if msg.ID != c.ID {
		return msg, ErrIDMismatch
	}

	return msg, nil
}

var ErrMarshalFormat = errors.New("failed to marshal message")

func (m *Msg) checksummable() (data []byte, err error) {
	data = append(data, byte(m.Type))
	data, err = BinaryAppend(data, binary.LittleEndian, m.ID)
	if err != nil {
		return nil, err
	}

	payloadLen := len(m.Payload)
	if payloadLen > 0xffff {
		// too large for field
		return nil, ErrMarshalFormat
	}
	data, err = BinaryAppend(data, binary.LittleEndian, uint16(payloadLen))
	if err != nil {
		return nil, err
	}

	data = append(data, m.Payload...)

	return data, nil
}

// aes-ctr-128
func (m *Msg) EncryptPayload(key []byte) error {
	// lol get IV from md5 of ID
	data, err := BinaryAppend(nil, binary.LittleEndian, m.ID)
	if err != nil {
		return err
	}

	hasher := md5.New()
	_, err = hasher.Write(data)
	if err != nil {
		return err
	}

	iv := hasher.Sum(nil)
	block, err := aes.NewCipher(key)
	if err != nil {
		return err
	}

	cipher := cipher.NewCTR(block, iv)
	cipher.XORKeyStream(m.Payload, m.Payload)

	return nil
}

func (m *Msg) DecryptPayload(key []byte) error {
	// xor lol
	return m.EncryptPayload(key)
}

func (m *Msg) MarshalBinary() (data []byte, err error) {
	data, err = m.checksummable()
	if err != nil {
		return nil, err
	}

	cksum := crc16.ChecksumCCITT(data)
	data, err = BinaryAppend(data, binary.LittleEndian, cksum)
	if err != nil {
		return nil, err
	}

	return data, nil
}

var ErrUnmarshalFormat = errors.New("failed to unmarshal message")

func (m *Msg) UnmarshalBinary(data []byte) error {
	if len(data) < 5 {
		return ErrUnmarshalFormat
	}

	m.Type = MsgType(data[0])
	data = data[1:]

	m.ID = binary.LittleEndian.Uint16(data[:2])
	data = data[2:]

	payloadLen := binary.LittleEndian.Uint16(data[:2])
	data = data[2:]

	if len(data) != int(payloadLen)+2 {
		return ErrUnmarshalFormat
	}

	m.Payload = data[:payloadLen]
	data = data[payloadLen:]

	dataCRC := binary.LittleEndian.Uint16(data)

	checksummable, err := m.checksummable()
	if err != nil {
		return err
	}

	calcCRC := crc16.ChecksumCCITT(checksummable)

	if dataCRC != calcCRC {
		return ErrUnmarshalFormat
	}

	return nil
}

// https://en.wikipedia.org/wiki/Modular_exponentiation#Pseudocode
func PowMod(base, exp, mod uint64) uint64 {
	if mod == 1 {
		return 0
	}

	ret := uint64(1)
	base %= mod

	for exp > 0 {
		if exp&1 == 1 {
			ret = (ret * base) % mod
		}
		exp >>= 1
		base = (base * base) % mod
	}

	return ret
}

func (p *PayloadCipheredKey) PutKey(aesKey []byte, e, n uint32) {
	for i := range 8 {
		p.Parts[i] = uint32(binary.LittleEndian.Uint16(aesKey[i*2 : i*2+2]))
	}
	p.encrypt(e, n)
}

func (p *PayloadCipheredKey) GetKey(d, n uint32) []byte {
	p.decrypt(d, n)
	key := make([]byte, 0, 16)

	for _, part := range p.Parts {
		key = binary.LittleEndian.AppendUint16(key, uint16(part))
	}

	return key
}

func (p *PayloadCipheredKey) encrypt(e, n uint32) {
	for i, m := range p.Parts {
		p.Parts[i] = uint32(PowMod(uint64(m), uint64(e), uint64(n)))
	}
}

func (p *PayloadCipheredKey) decrypt(d, n uint32) {
	// lol
	p.encrypt(d, n)
}

// fill in for go1.23 i guess
func BinaryAppend(b []byte, order binary.ByteOrder, data any) ([]byte, error) {
	var buf bytes.Buffer
	err := binary.Write(&buf, order, data)
	if err != nil {
		return nil, err
	}

	return append(b, buf.Bytes()...), nil
}

func BinaryDecode(b []byte, order binary.ByteOrder, data any) (int, error) {
	var buf bytes.Buffer
	n, err := buf.Write(b)
	if err != nil {
		return n, err
	}
	err = binary.Read(&buf, order, data)
	if err != nil {
		return n, err
	}

	return n, nil
}
