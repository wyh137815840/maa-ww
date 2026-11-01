package combat

import (
	"fmt"
	"os"
	"runtime"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

func stickNeutral(ctrl *maa.Controller) {
	_ = pulseSticks(ctrl, stickVec{}, minStickHold)
}

// pulseStickHold sets the left stick only (legacy 3-field protocol; works with older pumps).
func pulseStickHold(ctrl *maa.Controller, x, y int, hold time.Duration) bool {
	return pulseSticks(ctrl, stickVec{LX: x, LY: y}, hold)
}

// stickPayload kept for left-stick-only callers/tests.
func stickPayload(x, y int, hold time.Duration) (string, int64) {
	return stickPayloadVec(stickVec{LX: x, LY: y}, hold)
}

// stickPayloadVec is one command line for GamepadForwarder.
//
//	left stick only : "lx ly holdMs\n"           (older pumps understand this)
//	with camera     : "lx ly rx ry holdMs\n"     (needs the right-stick-capable pump)
func stickPayloadVec(v stickVec, hold time.Duration) (string, int64) {
	ms := clampHold(hold).Milliseconds()
	if v.hasCamera() {
		return fmt.Sprintf("%d %d %d %d %d\n", v.LX, v.LY, v.RX, v.RY, ms), ms
	}
	return fmt.Sprintf("%d %d %d\n", v.LX, v.LY, ms), ms
}

// stickShellCmdLine publishes atomically on the device: full write to .tmp, then mv over the live path.
func stickShellCmdLine(line string) string {
	tmp := stickCmdPath + ".tmp"
	return fmt.Sprintf("echo %s > %s && mv -f %s %s", line, tmp, tmp, stickCmdPath)
}

// stickShellCmd kept for left-stick-only callers/tests.
func stickShellCmd(x, y int, ms int64) string {
	return stickShellCmdLine(fmt.Sprintf("%d %d %d", x, y, ms))
}

// writeStickLocal publishes on the same filesystem as the pump (GOOS=android agent only).
func writeStickLocal(payload string) error {
	tmp := stickCmdPath + ".tmp"
	if err := os.WriteFile(tmp, []byte(payload), 0o666); err != nil {
		return err
	}
	if err := os.Rename(tmp, stickCmdPath); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

// pulseSticks asks GamepadForwarder to set left (+ optional right/camera) stick, atomic publish.
// GOOS=android: local tmp+rename. Host + ADB: PostShell only — never os.WriteFile on the PC.
func pulseSticks(ctrl *maa.Controller, v stickVec, hold time.Duration) bool {
	if ctrl == nil {
		return false
	}
	payload, _ := stickPayloadVec(v, hold)

	if runtime.GOOS == "android" {
		if err := writeStickLocal(payload); err != nil {
			log.Error().Err(err).Str("path", stickCmdPath).Msg("pulseStick: on-device write failed")
			return false
		}
		time.Sleep(25 * time.Millisecond)
		return true
	}

	line := payload[:len(payload)-1] // drop trailing \n; echo adds one
	job := ctrl.PostShell(stickShellCmdLine(line), 800*time.Millisecond).Wait()
	if job == nil || !job.Success() {
		log.Error().Int("lx", v.LX).Int("ly", v.LY).Int("rx", v.RX).Int("ry", v.RY).
			Msg("pulseStick: device PostShell failed")
		return false
	}
	time.Sleep(25 * time.Millisecond)
	return true
}
