package main

import (
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func initLogger() {
	zerolog.TimeFieldFormat = time.RFC3339

	var writers []io.Writer
	writers = append(writers, zerolog.ConsoleWriter{
		Out:        os.Stderr,
		TimeFormat: time.RFC3339,
	})

	if dir := logDir(); dir != "" {
		_ = os.MkdirAll(dir, 0o755)
		path := filepath.Join(dir, "go-service.log")
		if f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644); err == nil {
			writers = append(writers, f)
		}
	}

	log.Logger = zerolog.New(io.MultiWriter(writers...)).With().Timestamp().Logger()
}

func logDir() string {
	if v := os.Getenv("MAAWW_AGENT_LOG_DIR"); v != "" {
		return v
	}
	if cwd, err := os.Getwd(); err == nil {
		return filepath.Join(cwd, "debug")
	}
	return ""
}
