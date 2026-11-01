package main

import (
	"os"
	"runtime"
	"runtime/debug"

	"github.com/rs/zerolog/log"
)

// Version is injected at build time via -ldflags.
var Version = "dev"

const usage = "Usage: go-service <identifier>"

func main() {
	if _, ok := os.LookupEnv("GOTRACEBACK"); !ok {
		debug.SetTraceback("crash")
	}
	debug.SetPanicOnFault(true)

	defer func() {
		if r := recover(); r != nil {
			buf := make([]byte, 64<<10)
			for {
				n := runtime.Stack(buf, true)
				if n < len(buf) {
					buf = buf[:n]
					break
				}
				buf = make([]byte, 2*len(buf))
			}
			log.Error().
				Interface("panic", r).
				Str("stack", string(buf)).
				Msg("FATAL: go-service panicked")
			panic(r)
		}
	}()

	initLogger()

	log.Info().
		Str("version", Version).
		Msg("MaaWW Agent Service")

	if len(os.Args) < 2 {
		log.Fatal().Msg(usage)
	}

	runAgent(os.Args[1])
}
