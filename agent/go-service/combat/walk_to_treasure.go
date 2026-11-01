package combat

import (
	"encoding/json"
	"image"
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
//   - no marker after the gate: camera scan (right stick yaw in slices) or a fixed walk path
//     instead of W/S flip-flop (net zero motion)
//   - aim_mode "yaw": turn the camera toward the marker and walk forward (no strafing)
type WalkToTacetTreasureAction struct{}

var _ maa.CustomActionRunner = &WalkToTacetTreasureAction{}

type walkTreasureParam struct {
	TimeoutMs        int64    `json:"timeout_ms"`
	ClaimNodes       []string `json:"claim_nodes"`        // cheap (template) — every frame
	ClaimOCRNodes    []string `json:"claim_ocr_nodes"`    // OCR — every ocr_every frames
	TreasureNodes    []string `json:"treasure_nodes"`     // cheap (template) — every frame
	TreasureOCRNodes []string `json:"treasure_ocr_nodes"` // OCR — only when templates miss, every ocr_every frames
	XThreshold       int      `json:"x_threshold"`        // pixels; ok-ww ~0.07*1280≈90 (strafe mode)
	YOffset          int      `json:"y_offset"`           // pixels; ok-ww 0.05*720≈36, aim slightly above marker
	GateMs           int64    `json:"gate_ms"`            // stand still waiting for marker/claim before searching
	MarkerTTLMs      int64    `json:"marker_ttl_ms"`      // remembered marker expiry
	OCREvery         int      `json:"ocr_every"`          // run OCR nodes on frame 1 and every N frames

	// Camera (right stick). Requires a GamepadForwarder build that parses `lx ly rx ry hold`.
	ScanMode      string `json:"scan_mode"`       // "camera" (yaw scan) | "walk" (legacy path)
	AimMode       string `json:"aim_mode"`        // "strafe" (ok-ww A/D) | "yaw" (turn camera + forward)
	YawFullMs     int64  `json:"yaw_full_ms"`     // 360° time at yaw_deflect — CALIBRATE on device
	YawDeflect    int    `json:"yaw_deflect"`     // scan yaw ABS value
	ScanSteps     int    `json:"scan_steps"`      // yaw slices per circle
	YawDeadPx     int    `json:"yaw_dead_px"`     // aim_mode yaw dead zone
	YawWidePx     int    `json:"yaw_wide_px"`     // beyond this: rotate in place first
	YawMinDeflect int    `json:"yaw_min_deflect"` // aim_mode yaw min stick
	YawMaxDeflect int    `json:"yaw_max_deflect"` // aim_mode yaw max stick
}

func defaultWalkTreasureParam() walkTreasureParam {
	return walkTreasureParam{
		TimeoutMs:        60000,
		ClaimNodes:       []string{"TacetClaimReward"},
		ClaimOCRNodes:    []string{"TacetClaimRewardByOCR"},
		TreasureNodes:    []string{"TacetTreasureSeen", "TacetTreasureDist"},
		TreasureOCRNodes: []string{"TacetTreasureDistOCR"},
		XThreshold:       90,
		YOffset:          36,
		GateMs:           2500,
		MarkerTTLMs:      1500,
		OCREvery:         5,
		ScanMode:         "camera",
		AimMode:          "strafe", // switch to "yaw" after yaw calibration
		YawFullMs:        3000,
		YawDeflect:       20000,
		ScanSteps:        8,
		YawDeadPx:        60,
		YawWidePx:        260,
		YawMinDeflect:    8000,
		YawMaxDeflect:    22000,
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
	if override.ScanMode == "camera" || override.ScanMode == "walk" {
		p.ScanMode = override.ScanMode
	}
	if override.AimMode == "strafe" || override.AimMode == "yaw" {
		p.AimMode = override.AimMode
	}
	if override.YawFullMs > 0 {
		p.YawFullMs = override.YawFullMs
	}
	if override.YawDeflect > 0 {
		p.YawDeflect = override.YawDeflect
	}
	if override.ScanSteps > 0 {
		p.ScanSteps = override.ScanSteps
	}
	if override.YawDeadPx > 0 {
		p.YawDeadPx = override.YawDeadPx
	}
	if override.YawWidePx > 0 {
		p.YawWidePx = override.YawWidePx
	}
	if override.YawMinDeflect > 0 {
		p.YawMinDeflect = override.YawMinDeflect
	}
	if override.YawMaxDeflect > 0 {
		p.YawMaxDeflect = override.YawMaxDeflect
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

// vecDir classifies a vector for logging / steerDecision's last-direction memory.
func vecDir(v stickVec) walkDir {
	// dirA/dirD carry a small forward bias (see dirStick), so compare magnitudes.
	if absInt(v.LX) > absInt(v.LY) {
		if v.LX > 0 {
			return dirD
		}
		return dirA
	}
	switch {
	case v.LY < 0:
		return dirW
	case v.LY > 0:
		return dirS
	default:
		return dirNone
	}
}

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
		Str("scan_mode", param.ScanMode).
		Str("aim_mode", param.AimMode).
		Int64("yaw_full_ms", param.YawFullMs).
		Msg("WalkToTacetTreasure: start (ok-ww walk_to_box)")

	start := time.Now()
	deadline := start.Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	gateEnd := start.Add(time.Duration(param.GateMs) * time.Millisecond)
	markerTTL := time.Duration(param.MarkerTTLMs) * time.Millisecond
	if param.AimMode == "yaw" && markerTTL > 500*time.Millisecond {
		// While the camera is turning a remembered box goes stale fast.
		markerTTL = 500 * time.Millisecond
	}

	scanPlan := walkSearchLegs()
	if param.ScanMode == "camera" {
		scanPlan = cameraScanPlan(param.ScanSteps, time.Duration(param.YawFullMs)*time.Millisecond, param.YawDeflect)
	}
	seq := newScanSeq(scanPlan)

	const (
		strafeHold = 700 * time.Millisecond
		yawHold    = 300 * time.Millisecond // short: a lost frame must not keep turning
	)

	var (
		lastDir   walkDir
		lastVec   stickVec
		lastBox   *maa.Rect
		lastName  string
		lastSeen  time.Time
		holdUntil time.Time // deadline of the last stick command actually sent (clamped hold)
		stats     frameStats
		centered  bool
		frames    int
		missed    int
		searching bool
	)

	// setVec holds `v` continuously. A changed vector is always (re)sent — the pump applies the
	// newest command immediately, so no neutral is needed between legs. An unchanged vector is
	// only refreshed near expiry of the last command actually sent.
	setVec := func(v stickVec, hold time.Duration) bool {
		now := time.Now()
		hold = clampHold(hold)
		if v == lastVec {
			if v.zero() {
				return true
			}
			if !needsRewrite(holdUntil.Sub(now), hold) {
				return true
			}
		}
		lastVec = v
		lastDir = vecDir(v)
		if v.zero() {
			holdUntil = time.Time{}
			return pulseSticks(ctrl, stickVec{}, minStickHold)
		}
		holdUntil = now.Add(hold)
		return pulseSticks(ctrl, v, hold)
	}

	// sendVec sends  unconditionally with an exact hold (scan legs): the pump self-expires
	// it, so the leg length does not depend on how slow the next frame is.
	sendVec := func(v stickVec, hold time.Duration) bool {
		hold = clampHold(hold)
		lastVec = v
		lastDir = vecDir(v)
		if v.zero() {
			holdUntil = time.Time{}
			return pulseSticks(ctrl, stickVec{}, minStickHold)
		}
		holdUntil = time.Now().Add(hold)
		return pulseSticks(ctrl, v, hold)
	}

	release := func() {
		stickNeutral(ctrl)
		lastDir = dirNone
		lastVec = stickVec{}
		holdUntil = time.Time{}
	}

	for time.Now().Before(deadline) {
		if tasker.Stopping() {
			release()
			return false
		}

		frameStart := time.Now()
		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			time.Sleep(80 * time.Millisecond)
			continue
		}
		capMs := time.Since(frameStart)
		frames++
		ocrFrame := cadence(frames, param.OCREvery)

		// End condition first (ok-ww end_condition): claim prompt. Cheap template every frame,
		// OCR fallback on cadence only.
		claimNodes := param.ClaimNodes
		if ocrFrame {
			claimNodes = append(append([]string{}, param.ClaimNodes...), param.ClaimOCRNodes...)
		}
		if hit, name := anyExitHit(ctx, img, claimNodes); hit {
			// Fix the frame cost (capture + recognition) before release() so the stick
			// write/wait is not counted; same definition as every other frame.
			claimFrameDur := time.Since(frameStart)
			stats.add(ocrFrame, claimFrameDur)
			release()
			log.Info().Str("node", name).Int("frames", frames).
				Dur("total", time.Since(start)).
				Dur("frame_ms", claimFrameDur).Dur("cap_ms", capMs).Bool("ocr", ocrFrame).
				Dur("plain_avg", stats.avg(false)).Dur("ocr_avg", stats.avg(true)).
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
		frameDur := now.Sub(frameStart) // capture + all recognition this frame (before actuation)
		stats.add(ocrFrame, frameDur)
		if frames%20 == 0 {
			log.Info().Int("frames", frames).
				Dur("plain_avg", stats.avg(false)).Int("plain_n", stats.plainN).
				Dur("ocr_avg", stats.avg(true)).Int("ocr_n", stats.ocrN).
				Msg("WalkToTacetTreasure: frame stats")
		}
		if box != nil {
			if lastBox == nil || searching {
				log.Info().Str("node", name).Int("frames", frames).
					Dur("total", now.Sub(start)).
					Dur("frame_ms", frameDur).Bool("ocr", ocrFrame).
					Msg("WalkToTacetTreasure: marker acquired")
			}
			lastBox, lastName, lastSeen = box, name, now
			missed = 0
			searching = false
			seq.reset()
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
			cx := lastBox.X() + lastBox.Width()/2
			cy := lastBox.Y() + lastBox.Height()/2
			var (
				vec  stickVec
				hold time.Duration
			)
			if param.AimMode == "yaw" {
				vec, centered = aimYaw(aimInput{
					BoxCX: cx, BoxCY: cy, YOffset: param.YOffset,
					DeadPx: param.YawDeadPx, WidePx: param.YawWidePx,
					YawMin: param.YawMinDeflect, YawMax: param.YawMaxDeflect,
				})
				hold = yawHold
			} else {
				var next walkDir
				next, centered = steerDecision(steerInput{
					BoxCX: cx, BoxCY: cy,
					LastDir:    lastDir,
					Centered:   centered,
					XThreshold: param.XThreshold,
					YOffset:    param.YOffset,
				})
				vec = dirVec(next)
				hold = strafeHold
			}
			if frames%8 == 1 {
				log.Info().
					Str("node", lastName).
					Int("cx", cx).Int("cy", cy).
					Bool("centered", centered).
					Str("aim", param.AimMode).
					Int("lx", vec.LX).Int("ly", vec.LY).Int("rx", vec.RX).
					Dur("frame_ms", frameDur).Dur("cap_ms", capMs).Bool("ocr", ocrFrame).
					Msg("WalkToTacetTreasure: steer")
			}
			if !setVec(vec, hold) {
				release()
				return false
			}

		case lastVec.zero() && !searching && now.Before(gateEnd):
			// ok-ww wait_until(end_condition or find_function): stand still while waiting.
			if frames == 1 {
				log.Info().Msg("WalkToTacetTreasure: gate — waiting for marker/claim (no movement)")
			}

		default:
			// Gate expired, no marker: scan the camera (or follow the walk path).
			if !searching {
				searching = true
				seq.reset()
				log.Info().Int("missed", missed).Str("scan_mode", param.ScanMode).
					Msg("WalkToTacetTreasure: no marker → search")
			}
			// Leg timing is independent of recognition cost (see scanSeq).
			if act := seq.step(now, frameStart); act.Send {
				if !sendVec(act.Vec, act.Hold) {
					release()
					return false
				}
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
		Dur("total", time.Since(start)).
		Dur("plain_avg", stats.avg(false)).Dur("ocr_avg", stats.avg(true)).
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
