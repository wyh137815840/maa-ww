package combat

import (
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/rs/zerolog/log"
)

const debugFrameMax = 40

var (
	debugFrameMu    sync.Mutex
	debugFrameCount int
)

// dumpDebugFrame saves the frame next to go-service.log (<log dir>/frames) so a run on the
// device (game on a virtual display, not screencap-able from ADB) can be inspected afterwards.
// Capped at debugFrameMax files per process.
func dumpDebugFrame(img image.Image, tag string) {
	if img == nil {
		return
	}
	debugFrameMu.Lock()
	if debugFrameCount >= debugFrameMax {
		debugFrameMu.Unlock()
		return
	}
	debugFrameCount++
	debugFrameMu.Unlock()

	dir := os.Getenv("MAAWW_AGENT_LOG_DIR")
	if dir == "" {
		cwd, err := os.Getwd()
		if err != nil {
			return
		}
		dir = filepath.Join(cwd, "debug")
	}
	dir = filepath.Join(dir, "frames")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return
	}
	p := filepath.Join(dir, fmt.Sprintf("%s_%s.png", time.Now().Format("150405"), tag))
	f, err := os.Create(p)
	if err != nil {
		return
	}
	defer f.Close()
	if err := png.Encode(f, img); err != nil {
		log.Warn().Err(err).Msg("dumpDebugFrame: encode failed")
		return
	}
	log.Info().Str("file", p).Msg("dumpDebugFrame")
}
