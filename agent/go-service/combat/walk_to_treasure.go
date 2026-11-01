package combat

import (
	"encoding/json"
	"fmt"
	"image"
	"os"
	"runtime"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// WalkToTacetTreasureAction ports ok-ww BaseWWTask.walk_to_treasure → walk_to_box.
//
// ok-ww logic (do_walk_to_box):
//  1. wait_until(end_condition or marker): do NOT move until the chest marker / F prompt is seen
//  2. Hold WASD continuously (send_key_down), only change when direction changes
//  3. Strafe a/d until |dx| small (centered), then w/s by vertical position
//  4. Remember last_target if recognition flickers (here with a TTL)
//  5. End on claim F text, then pick_f
//
// Pad adaptations:
//   - cheap template checks every frame, OCR only every ocr_every frames (OCR made frames ~0.7s)
//   - no marker after the gate: follow a fixed search path instead of W/S flip-flop (net zero motion)
type WalkToTacetTreasureAction struct{}

var _ maa.CustomActionRunner = &WalkToTacetTreasureAction{}

type walkTreasureParam struct {
	TimeoutMs        int64    `json:"timeout_ms"`
	ClaimNodes       []string `json:"claim_nodes"`        // cheap (template) — every frame
	ClaimOCRNodes    []string `json:"claim_ocr_nodes"`    // OCR — every ocr_every frames
	TreasureNodes    []string `json:"treasure_nodes"`     // cheap (template) — every frame
	TreasureOCRNodes []string `json:"treasure_ocr_nodes"` // OCR — only when templates miss, every ocr_every frames
	XThreshold       int      `json:"x_threshold"`        // pixels; ok-ww ~0.07*1280≈90
	YOffset          int      `json:"y_offset"`           // pixels; ok-ww 0.05*720≈36, aim slightly above marker
	GateMs           int64    `json:"gate_ms"`            // stand still waiting for marker/claim before searching
	MarkerTTLMs      int64    `json:"marker_ttl_ms"`      // remembered marker expiry
	OCREvery         int      `json:"ocr_every"`          // run OCR nodes on frame 1 and every N frames
}

func defaultWalkTreasureParam() walkTreasureParam {
	return walkTreasureParam{
		TimeoutMs:        60000,
		ClaimNodes:       []string{"TacetClaimReward"},
		ClaimOCRNodes:    []string{"TacetClaimRewardByOCR"},
		TreasureNodes:    []string{"TacetTreasureSeen", "TacetTreasureAim", "TacetTreasureDist"},
		TreasureOCRNodes: []string{"TacetTreasureDistOCR"},
		XThreshold:       90,
		YOffset:          36,
		GateMs:           2500,
		MarkerTTLMs:      1500,
		OCREvery:         5,
	}
}

func parseWalkTreasureParam(raw string) walkTreasureParam {
	p := defaultWalkTreasureParam()
	if raw == "" {
		return p
	}
	var override walkTreasureParam
	if err := json.Unmarshal([]byte(raw), &override); err != nil {
		log.Warn().Err(err).Msg("WalkToTacetTreasure: bad param, using defaults")
		return p
	}
	if override.TimeoutMs > 0 {
		p.TimeoutMs = override.TimeoutMs
	}
	if len(override.ClaimNodes) > 0 {
		p.ClaimNodes = override.ClaimNodes
	}
	if len(override.ClaimOCRNodes) > 0 {
		p.ClaimOCRNodes = override.ClaimOCRNodes
	}
	if len(override.TreasureNodes) > 0 {
		p.TreasureNodes = override.TreasureNodes
	}
	if len(override.TreasureOCRNodes) > 0 {
		p.TreasureOCRNodes = override.TreasureOCRNodes
	}
	if override.XThreshold > 0 {
		p.XThreshold = override.XThreshold
	}
	if override.YOffset > 0 {
		p.YOffset = override.YOffset
	}
	if override.GateMs > 0 {
		p.GateMs = override.GateMs
	}
	if override.MarkerTTLMs > 0 {
		p.MarkerTTLMs = override.MarkerTTLMs
	}
	if override.OCREvery > 0 {
		p.OCREvery = override.OCREvery
	}
	return p
}

const stickCmdPath = "/data/local/tmp/maaww_stick"

// stick axes (Xbox ABS): Y negative = forward (W), positive = back (S); X positive = right (D).
type walkDir int

const (
	dirNone walkDir = iota
	dirW
	dirA
	dirS
	dirD
)

func (a *WalkToTacetTreasureAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("WalkToTacetTreasure: tasker nil")
		return false
	}
	ctrl := tasker.GetController()
	if ctrl == nil {
		log.Error().Msg("WalkToTacetTreasure: controller nil")
		return false
	}

	param := defaultWalkTreasureParam()
	if arg != nil {
		param = parseWalkTreasureParam(arg.CustomActionParam)
	}

	pad := NewPad(ctrl)
	log.Info().
		Int64("timeout_ms", param.TimeoutMs).
		Strs("treasure_nodes", param.TreasureNodes).
		Strs("treasure_ocr_nodes", param.TreasureOCRNodes).
		Int("x_threshold", param.XThreshold).
		Int64("gate_ms", param.GateMs).
		Msg("WalkToTacetTreasure: start (ok-ww walk_to_box)")

	start := time.Now()
	deadline := start.Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	gateEnd := start.Add(time.Duration(param.GateMs) * time.Millisecond)
	markerTTL := time.Duration(param.MarkerTTLMs) * time.Millisecond

	const holdDur = 700 * time.Millisecond

	var (
		lastDir   walkDir
		lastBox   *maa.Rect
		lastName  string
		lastSeen  time.Time
		lastWrite time.Time
		centered  bool
		frames    int
		missed    int
		searchIdx int
		segStart  time.Time
		searching bool
	)

	// setDir holds `d` continuously: rewrite only on direction change or near hold expiry.
	setDir := func(d walkDir, hold time.Duration) bool {
		now := time.Now()
		if d == lastDir && !shouldRefreshHold(now.Sub(lastWrite), hold) {
			return true
		}
		if d != lastDir && lastDir != dirNone {
			stickNeutral(ctrl)
			time.Sleep(15 * time.Millisecond)
		}
		lastDir = d
		lastWrite = now
		if d == dirNone {
			return pulseStickHold(ctrl, 0, 0, 50*time.Millisecond)
		}
		x, y := dirStick(d)
		return pulseStickHold(ctrl, x, y, hold)
	}

	release := func() {
		stickNeutral(ctrl)
		lastDir = dirNone
	}

	for time.Now().Before(deadline) {
		if tasker.Stopping() {
			release()
			return false
		}

		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			time.Sleep(80 * time.Millisecond)
			continue
		}
		frames++
		ocrFrame := cadence(frames, param.OCREvery)

		// End condition first (ok-ww end_condition): claim prompt. Cheap template every frame,
		// OCR fallback on cadence only.
		claimNodes := param.ClaimNodes
		if ocrFrame {
			claimNodes = append(append([]string{}, param.ClaimNodes...), param.ClaimOCRNodes...)
		}
		if hit, name := anyExitHit(ctx, img, claimNodes); hit {
			release()
			log.Info().Str("node", name).Int("frames", frames).
				Dur("elapsed", time.Since(start)).
				Msg("WalkToTacetTreasure: claim prompt → Interact(B)")
			pad.Interact()
			time.Sleep(500 * time.Millisecond)
			return true
		}

		box, name := firstTreasureBox(ctx, img, param.TreasureNodes)
		if box == nil && ocrFrame {
			box, name = firstTreasureBox(ctx, img, param.TreasureOCRNodes)
		}
		now := time.Now()
		if box != nil {
			if lastBox == nil || searching {
				log.Info().Str("node", name).Int("frames", frames).
					Dur("elapsed", now.Sub(start)).Msg("WalkToTacetTreasure: marker acquired")
			}
			lastBox, lastName, lastSeen = box, name, now
			missed = 0
			searching = false
			searchIdx = 0
			segStart = time.Time{}
		} else {
			missed++
			if lastBox != nil && !markerFresh(now.Sub(lastSeen), markerTTL) {
				log.Info().Int("missed", missed).Msg("WalkToTacetTreasure: marker expired")
				lastBox = nil
				centered = false
			}
		}

		switch {
		case lastBox != nil:
			next, c := steerDecision(steerInput{
				BoxCX:      lastBox.X() + lastBox.Width()/2,
				BoxCY:      lastBox.Y() + lastBox.Height()/2,
				LastDir:    lastDir,
				Centered:   centered,
				XThreshold: param.XThreshold,
				YOffset:    param.YOffset,
			})
			centered = c
			if frames%8 == 1 {
				log.Info().
					Str("node", lastName).
					Int("cx", lastBox.X()+lastBox.Width()/2).
					Int("cy", lastBox.Y()+lastBox.Height()/2).
					Bool("centered", centered).
					Str("dir", dirName(next)).
					Msg("WalkToTacetTreasure: steer")
			}
			if !setDir(next, holdDur) {
				release()
				return false
			}

		case lastDir == dirNone && !searching && now.Before(gateEnd):
			// ok-ww wait_until(end_condition or find_function): stand still while waiting.
			if frames == 1 {
				log.Info().Msg("WalkToTacetTreasure: gate — waiting for marker/claim (no movement)")
			}

		default:
			// Gate expired, no marker: follow a fixed search path (continuous legs).
			if !searching {
				searching = true
				searchIdx = 0
				segStart = now
				log.Info().Int("missed", missed).Msg("WalkToTacetTreasure: no marker → search path")
			}
			seg := searchSegment(searchIdx)
			if now.Sub(segStart) >= seg.Dur {
				searchIdx++
				segStart = now
				seg = searchSegment(searchIdx)
			}
			remain := seg.Dur - now.Sub(segStart)
			if remain > 2000*time.Millisecond {
				remain = 2000 * time.Millisecond
			}
			if !setDir(seg.Dir, remain+200*time.Millisecond) {
				release()
				return false
			}
			if missed%15 == 0 {
				pad.Interact() // may already be in F range without a claim template hit
			}
		}

		time.Sleep(20 * time.Millisecond)
	}

	release()
	ctrl.PostScreencap().Wait()
	if img, err := ctrl.CacheImage(); err == nil && img != nil {
		all := append(append([]string{}, param.ClaimNodes...), param.ClaimOCRNodes...)
		if hit, name := anyExitHit(ctx, img, all); hit {
			log.Info().Str("node", name).Msg("WalkToTacetTreasure: claim at timeout")
			pad.Interact()
			return true
		}
	}
	log.Warn().Int("frames", frames).
		Dur("elapsed", time.Since(start)).
		Msg("WalkToTacetTreasure: timeout without claim")
	return false
}

func dirStick(d walkDir) (x, y int) {
	switch d {
	case dirW:
		return 0, -30000
	case dirS:
		return 0, 25000
	case dirA:
		return -28000, -6000 // strafe L + slight forward (ok-ww pure A; pad needs slight W to move)
	case dirD:
		return 28000, -6000
	default:
		return 0, 0
	}
}

func oppositeDir(d walkDir) walkDir {
	switch d {
	case dirW:
		return dirS
	case dirS:
		return dirW
	case dirA:
		return dirD
	case dirD:
		return dirA
	default:
		return dirW
	}
}

func dirName(d walkDir) string {
	switch d {
	case dirW:
		return "w"
	case dirA:
		return "a"
	case dirS:
		return "s"
	case dirD:
		return "d"
	default:
		return "-"
	}
}

func firstTreasureBox(ctx *maa.Context, img image.Image, nodes []string) (*maa.Rect, string) {
	for _, name := range nodes {
		if name == "" {
			continue
		}
		detail, err := ctx.RunRecognition(name, img)
		if err != nil || detail == nil || !detail.Hit {
			continue
		}
		b := detail.Box
		return &b, name
	}
	return nil, ""
}

func absInt(v int) int {
	if v < 0 {
		return -v
	}
	return v
}

func stickNeutral(ctrl *maa.Controller) {
	_ = pulseStickHold(ctrl, 0, 0, 50*time.Millisecond)
}

// stickPayload is one command line for GamepadForwarder: "absX absY holdMs\n".
func stickPayload(x, y int, hold time.Duration) (string, int64) {
	ms := hold.Milliseconds()
	if ms < 50 {
		ms = 50
	}
	if ms > 2000 {
		ms = 2000
	}
	return fmt.Sprintf("%d %d %d\n", x, y, ms), ms
}

// stickShellCmd publishes atomically on the device: full write to .tmp, then mv over the live path.
func stickShellCmd(x, y int, ms int64) string {
	tmp := stickCmdPath + ".tmp"
	return fmt.Sprintf("echo %d %d %d > %s && mv -f %s %s", x, y, ms, tmp, tmp, stickCmdPath)
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

// pulseStickHold asks GamepadForwarder to set left stick (atomic publish, no truncate-in-place).
// GOOS=android: local tmp+rename. Host + ADB: PostShell only — never os.WriteFile on the PC.
func pulseStickHold(ctrl *maa.Controller, x, y int, hold time.Duration) bool {
	if ctrl == nil {
		return false
	}
	payload, ms := stickPayload(x, y, hold)

	if runtime.GOOS == "android" {
		if err := writeStickLocal(payload); err != nil {
			log.Error().Err(err).Str("path", stickCmdPath).Msg("pulseStick: on-device write failed")
			return false
		}
		time.Sleep(25 * time.Millisecond)
		return true
	}

	job := ctrl.PostShell(stickShellCmd(x, y, ms), 800*time.Millisecond).Wait()
	if job == nil || !job.Success() {
		log.Error().Int("x", x).Int("y", y).Msg("pulseStick: device PostShell failed")
		return false
	}
	time.Sleep(25 * time.Millisecond)
	return true
}
