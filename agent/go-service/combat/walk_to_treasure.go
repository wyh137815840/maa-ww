package combat

import (
	"encoding/json"
	"fmt"
	"image"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// WalkToTacetTreasureAction ports ok-ww walk_to_treasure under pad mode.
// Movement: write stick pulses to /data/local/tmp/maaww_stick for GamepadForwarder
// (shell/input group) — app PostShell sendevent has no permission and is a no-op.
type WalkToTacetTreasureAction struct{}

var _ maa.CustomActionRunner = &WalkToTacetTreasureAction{}

type walkTreasureParam struct {
	TimeoutMs     int64    `json:"timeout_ms"`
	ClaimNodes    []string `json:"claim_nodes"`
	TreasureNodes []string `json:"treasure_nodes"`
	XThreshold    int      `json:"x_threshold"`
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
	return p
}

const stickCmdPath = "/data/local/tmp/maaww_stick"

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
		Msg("WalkToTacetTreasure: start")

	deadline := time.Now().Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	centered := false
	missed := 0
	pulses := 0

	for time.Now().Before(deadline) {
		if tasker.Stopping() {
			stickNeutral(ctrl)
			return false
		}

		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		if hit, name := anyExitHit(ctx, img, param.ClaimNodes); hit {
			stickNeutral(ctrl)
			log.Info().Str("node", name).Msg("WalkToTacetTreasure: claim prompt → Interact(B)")
			pad.Interact()
			time.Sleep(500 * time.Millisecond)
			return true
		}

		box, name := firstTreasureBox(ctx, img, param.TreasureNodes)
		if box == nil {
			missed++
			stickNeutral(ctrl)
			// no marker: short forward + occasional left look via right-stick file (ABS_Z not pumped; use forward only)
			pulseStick(ctrl, 0, -28000, 350*time.Millisecond)
			pulses++
			if missed%5 == 0 {
				pad.Interact() // already in range sometimes without claim OCR
			}
			time.Sleep(100 * time.Millisecond)
			continue
		}
		missed = 0

		cx := box.X() + box.Width()/2
		cy := box.Y() + box.Height()/2
		dx := cx - 640
		dy := cy - 360
		log.Info().
			Str("node", name).
			Int("cx", cx).Int("cy", cy).
			Int("dx", dx).Int("dy", dy).
			Bool("centered", centered).
			Int("pulses", pulses).
			Msg("WalkToTacetTreasure: treasure")

		if absInt(dx) > param.XThreshold && !centered {
			if dx > 0 {
				pulseStick(ctrl, 25000, -8000, 280*time.Millisecond) // strafe R + slight forward
			} else {
				pulseStick(ctrl, -25000, -8000, 280*time.Millisecond)
			}
		} else {
			centered = true
			if dy > 100 {
				pulseStick(ctrl, 0, 18000, 220*time.Millisecond) // back
			} else {
				pulseStick(ctrl, 0, -30000, 400*time.Millisecond) // forward hard
			}
		}
		pulses++
		time.Sleep(60 * time.Millisecond)
	}

	stickNeutral(ctrl)
	ctrl.PostScreencap().Wait()
	if img, err := ctrl.CacheImage(); err == nil && img != nil {
		if hit, name := anyExitHit(ctx, img, param.ClaimNodes); hit {
			log.Info().Str("node", name).Msg("WalkToTacetTreasure: claim at timeout")
			pad.Interact()
			return true
		}
	}
	// Last-ditch: spam B while pulsing forward (often already ≤6m).
	log.Warn().Int("pulses", pulses).Msg("WalkToTacetTreasure: timeout — forward+B burst")
	for i := 0; i < 6; i++ {
		pulseStick(ctrl, 0, -30000, 350*time.Millisecond)
		pad.Interact()
		time.Sleep(200 * time.Millisecond)
	}
	stickNeutral(ctrl)
	return true
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
	pulseStick(ctrl, 0, 0, 40*time.Millisecond)
}

// pulseStick asks GamepadForwarder to hold left stick, then waits for the pulse.
func pulseStick(ctrl *maa.Controller, x, y int, hold time.Duration) {
	if ctrl == nil {
		return
	}
	ms := hold.Milliseconds()
	if ms < 40 {
		ms = 40
	}
	cmd := fmt.Sprintf("printf '%%s' '%d %d %d' > %s", x, y, ms, stickCmdPath)
	ctrl.PostShell(cmd, 800*time.Millisecond).Wait()
	time.Sleep(hold + 80*time.Millisecond)
}
