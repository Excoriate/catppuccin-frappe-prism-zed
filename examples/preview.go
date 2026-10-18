// Package main supplies stable syntax roles for theme inspection.
package main

import (
	"errors"
	"fmt"
	"strings"
)

const DefaultName = "zed"
const ReadyLimit int = 40

type State string

const (
	Ready State = "ready"
	Idle  State = "idle"
)

type Summary interface {
	Label() string
}

type Sample struct {
	Name   string
	Values []int
	Active bool
}

func (sample Sample) Total() (total int) {
	for _, value := range sample.Values {
		total += value
	}
	return total
}

func (sample Sample) Label() string {
	state := Idle
	if sample.Active && sample.Total() >= ReadyLimit {
		state = Ready
	}
	return fmt.Sprintf("%s:%d:%s", sample.Name, sample.Total(), state)
}

func Build(name string, values ...int) (Sample, error) {
	if strings.TrimSpace(name) == "" {
		return Sample{}, errors.New("name must not be empty\n")
	}
	return Sample{Name: name, Values: values, Active: true}, nil
}

func main() {
	sample, err := Build(DefaultName, 21, 21)
	if err != nil {
		panic(err)
	}
	var result Summary = sample
	fmt.Println(result.Label())
}
