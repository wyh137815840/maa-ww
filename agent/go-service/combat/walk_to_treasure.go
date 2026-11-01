package combat

import (
	"encoding/json"
	"fmt"
	"image"
	"os"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// WalkToTacetTreasureAction ports ok-ww BaseWWTask.walk_to_treasure → walk_to_box.
//
// ok-ww logic (do_walk_to_box):
//  1. Hold WASD continuously (send_key_down), only change when direction changes
//  2. If marker lost: opposite of last direction — NOT always forward
//  3. Strafe a/d until |dx| small (centered), then w/s by vertical position
//  4. Remember last_target if recognition flickers
//  5. End on claim F text, then pick_f
//
type WalkToTacetTreasureAction struct{}

var _ maa.CustomActionRunner = &WalkToTacetTreasureAction{}

type walkTreasureParam struct {
	TimeoutMs     int64    `json:"timeout_ms"`
	ClaimNodes    []string `json:"claim_nodes"`
	TreasureNodes []string `json:"treasure_nodes"`
	XThreshold    int      `json:"x_threshold"` // pixels; ok-ww ~0.07*1280≈90
	YOffset       int      `json:"y_offset"`    // pixels; ok-ww 0.05*720≈36, aim slightly above marker
}

func defaultWalkTreasureParam() walkTreasureParam {
	return walkTreasureParam{
		TimeoutMs: 60000,
		ClaimNodes: []string{
			"TacetClaimReward",
			"TacetClaimRewardByOCR",
		},
		TreasureNodes: []string{
			"TacetTreasureDist",
			"TacetTreasureDistOCR",
			"TacetTreasureAim",
			"TacetTreasureSeen",
		},
		XThreshold: 90,
		YOffset:    36,
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
	if len(override.TreasureNodes) > 0 {
		p.TreasureNodes = override.TreasureNodes
	}
	if override.XThreshold > 0 {
		p.XThreshold = override.XThreshold
	}
	if override.YOffset > 0 {
		p.YOffset = override.YOffset
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
		Int("x_threshold", param.XThreshold).
		Msg("WalkToTacetTreasure: start (ok-ww walk_to_box)")

	deadline := time.Now().Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	centered := false
	var lastDir walkDir
	var lastBox *maa.Rect
	lastName := ""
	missed := 0
	frames := 0

	holdDir := func(d walkDir) bool {
		x, y := dirStick(d)
		// Refresh long hold; pump clamps to 50–2000ms. Do NOT neutral between same-dir frames.
		return pulseStickHold(ctrl, x, y, 600*time.Millisecond)
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

		if hit, name := anyExitHit(ctx, img, param.ClaimNodes); hit {
			release()
			log.Info().Str("node", name).Msg("WalkToTacetTreasure: claim prompt → Interact(B)")
			pad.Interact()
			time.Sleep(500 * time.Millisecond)
			return true
		}

		box, name := firstTreasureBox(ctx, img, param.TreasureNodes)
		if box != nil {
			lastBox = box
			lastName = name
			missed = 0
		} else {
			missed++
		}

		var next walkDir
		if lastBox == nil {
			// ok-ww: opposite of last_direction when find_function missing
			next = oppositeDir(lastDir)
			if next == dirNone {
				next = dirW
			}
			if missed == 1 || missed%8 == 0 {
				log.Info().Str("dir", dirName(next)).Int("missed", missed).Msg("WalkToTacetTreasure: no marker → opposite/search")
			}
		} else {
			cx := lastBox.X() + lastBox.Width()/2
			cy := lastBox.Y() + lastBox.Height()/2 - param.YOffset
			dx := cx - 640
			// ok-ww: tighter threshold before any direction, then x_threshold once moving
			thr := param.XThreshold
			if lastDir == dirNone {
				thr = 50
			}
			centered = centered || absInt(dx) <= thr
			if !centered {
				if dx > 0 {
					next = dirD
				} else {
					next = dirA
				}
			} else {
				// ok-ww vertical bands depend on last w/s
				centerY := 360
				switch lastDir {
				case dirS:
					centerY = int(0.45 * 720) // 324
				case dirW:
					centerY = int(0.6 * 720) // 432
				}
				if cy > centerY {
					next = dirS
				} else {
					next = dirW
				}
			}
			if frames%6 == 1 {
				log.Info().
					Str("node", lastName).
					Int("cx", cx).Int("cy", cy).Int("dx", dx).
					Bool("centered", centered).
					Str("dir", dirName(next)).
					Msg("WalkToTacetTreasure: steer")
			}
		}

		if next != lastDir {
			if lastDir != dirNone {
				stickNeutral(ctrl)
				time.Sleep(15 * time.Millisecond)
			}
			lastDir = next
			if !holdDir(next) {
				release()
				return false
			}
		} else {
			// keep holding same direction
			if !holdDir(next) {
				release()
				return false
			}
		}

		if missed > 0 && missed%6 == 0 {
			pad.Interact() // sometimes already in F range without claim template
		}
		time.Sleep(40 * time.Millisecond)
	}

	release()
	ctrl.PostScreencap().Wait()
	if img, err := ctrl.CacheImage(); err == nil && img != nil {
		if hit, name := anyExitHit(ctx, img, param.ClaimNodes); hit {
			log.Info().Str("node", name).Msg("WalkToTacetTreasure: claim at timeout")
			pad.Interact()
			return true
		}
	}
	log.Warn().Int("frames", frames).Msg("WalkToTacetTreasure: timeout without claim")
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
	_ = pulseStickHold(ctrl, 0, 0, 40*time.Millisecond)
}

// pulseStickHold writes stick command; does not sleep the full hold (caller paces).
// Sleep a short settle so pump can pick up the write.
func pulseStickHold(ctrl *maa.Controller, x, y int, hold time.Duration) bool {
	if ctrl == nil {
		return false
	}
	ms := hold.Milliseconds()
	if ms < 40 {
		ms = 40
	}
	if ms > 2000 {
		ms = 2000
	}
	payload := fmt.Sprintf("%d %d %d\n", x, y, ms)
	if err := os.WriteFile(stickCmdPath, []byte(payload), 0o666); err != nil {
		log.Error().Err(err).Str("path", stickCmdPath).Msg("pulseStick: WriteFile failed")
		return false
	}
	time.Sleep(25 * time.Millisecond)
	return true
}
