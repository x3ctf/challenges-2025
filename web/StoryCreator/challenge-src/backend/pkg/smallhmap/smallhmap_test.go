package smallhmap_test

import (
	"context"
	"testing"

	"github.com/boxmein/cwte2024-chall/pkg/smallhmap"
	"github.com/stretchr/testify/assert"
)

func TestSmallHmap(t *testing.T) {
	key := "queries:MyQuery:asdfasdfasdfasdfasdf"
	value := "query MyQuery { foo }"
	ctx := context.Background()

	s := smallhmap.New()
	s.Add(ctx, key, value)

	v, ok := s.Get(ctx, key)

	assert.True(t, ok)
	assert.Equal(t, value, v)
}

func TestInvalidKey(t *testing.T) {
	key := "queries:MyQuery:asdfasdfasdfasdfasdf"
	ctx := context.Background()

	s := smallhmap.New()

	v, ok := s.Get(ctx, key)

	assert.False(t, ok)
	assert.Equal(t, nil, v)
}

func TestCollides(t *testing.T) {
	key := "queries:MyQuery:asdfasdfasdfasdfasdf"
	key2 := "queries:MyQuery:asdfasdfasdfasdfasee"
	value := "query MyQuery { foo }"
	value2 := "changed query"
	ctx := context.Background()

	s := smallhmap.New()
	s.Add(ctx, key, value)
	s.Add(ctx, key2, value2)

	v, ok := s.Get(ctx, key)

	assert.True(t, ok)
	assert.Equal(t, value2, v)
}
func makeKeySmaller(key string) uint64 {
	sum := uint64(0)
	for _, c := range key {
		sum += uint64(c)
	}
	return sum % 255
}
func TestHash(t *testing.T) {
	assert.Equal(t, uint64(137), makeKeySmaller("f5aa747aa1829967120df469ba2d07e956bd2d6728a97872a8df468b3f8c2f9c"))
}
