// Code generated by github.com/99designs/gqlgen, DO NOT EDIT.

package model

import (
	"github.com/boxmein/cwte2024-chall/pkg/model"
)

type Mutation struct {
}

type Query struct {
}

type StoryExportInput struct {
	StoryID    int              `json:"storyId"`
	Dimensions model.Dimensions `json:"dimensions"`
}

type StoryInput struct {
	Text   string `json:"text"`
	Action string `json:"action"`
	Image  int    `json:"image"`
}
