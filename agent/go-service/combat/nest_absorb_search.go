package combat

import (
	"encoding/json"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// NestAbsorbSearchAction looks for the "吸收" prompt after a nest is cleared.
//
// Echoes drop where the enemies died (user-confirmed), i.e. around where the fight happened, so
// the search starts in place: turn the camera one full circle (right stick, look pauses between
// slices), then walk a short leg forward and circle again. It returns true as soon as a prompt
// node hits (the pipeline node NestAbsorbPrompt then presses B), false on timeout.
type NestAbsorbSearchAction struct{}

var _ maa.CustomActionRunner = &NestAbsorbSearchAction{}

type nestAbsorbSearchParam struct {
	PromptNodes []string `json:"prompt_nodes"`
	TimeoutMs   int64    `json:"timeout_ms"`
	ScanSteps   int      `json:"scan_steps"`
	YawFullMs   int64    `json:"yaw_full_ms"`
	YawDeflect  int      `json:"yaw_deflect"`
	WalkMs      int64    `json:"walk_ms"`
}

func defaultNestAbsorbSearchParam() nestAbsorbSearchParam {
	return nestAbsorbSearchParam{
		PromptNodes: []string{"NestAbsorbPrompt"},
		TimeoutMs:   45000,
		ScanSteps:   8,
		YawFullMs:   3000,
		YawDeflect:  20000,
		WalkMs:      1200,
	}
}

func parseNestAbsorbSearchParam(raw string) nestAbsorbSearchParam {
	p := defaultNestAbsorbSearchParam()
	if raw == "" {
		return p
	}
	var o nestAbsorbSearchParam
	if err := json.Unmarshal([]byte(raw), &o); err != nil {
		log.Warn().Err(err).Str("raw", raw).Msg("NestAbsorbSearch: bad param, using defaults")
		return p
	}
	if len(o.PromptNodes) > 0 {
		p.PromptNodes = o.PromptNodes
	}
	if o.TimeoutMs > 0 {
		p.TimeoutMs = o.TimeoutMs
	}
	if o.ScanSteps > 0 {
		p.ScanSteps = o.ScanSteps
	}
	if o.YawFullMs > 0 {
		p.YawFullMs = o.YawFullMs
	}
	if o.YawDeflect > 0 {
		p.YawDeflect = o.YawDeflect
	}
	if o.WalkMs > 0 {
		p.WalkMs = o.WalkMs
	}
	return p
}

// nestAbsorbPlan is one search cycle: a full camera circle, then a short forward walk.
func nestAbsorbPlan(p nestAbsorbSearchParam) []scanLeg {
	legs := cameraScanPlan(p.ScanSteps, time.Duration(p.YawFullMs)*time.Millisecond, p.YawDeflect)
	if n := len(legs); n > 0 && !legs[n-1].Look && legs[n-1].Vec.LY < 0 {
		legs[n-1].Dur = clampHold(time.Duration(p.WalkMs) * time.Millisecond)
	}
	return legs
}

func (a *NestAbsorbSearchAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("NestAbsorbSearch: tasker is nil")
		return false
	}
	ctrl := tasker.GetController()
	if ctrl == nil {
		log.Error().Msg("NestAbsorbSearch: controller is nil")
		return false
	}
	param := defaultNestAbsorbSearchParam()
	if arg != nil {
		param = parseNestAbsorbSearchParam(arg.CustomActionParam)
	}
	log.Info().Strs("prompt_nodes", param.PromptNodes).Int64("timeout_ms", param.TimeoutMs).
		Msg("NestAbsorbSearch: start")

	seq := newScanSeq(nestAbsorbPlan(param))
	deadline := time.Now().Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	defer stickNeutral(ctrl)

	for {
		if tasker.Stopping() {
			return false
		}
		if time.Now().After(deadline) {
			log.Warn().Msg("NestAbsorbSearch: timeout, no absorb prompt found")
			return false
		}
		frameStart := time.Now()
		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err == nil && img != nil {
			if hit, name := anyExitHit(ctx, img, param.PromptNodes); hit {
				log.Info().Str("node", name).Msg("NestAbsorbSearch: prompt found")
				return true
			}
		}
		if act := seq.step(time.Now(), frameStart); act.Send {
			if !pulseSticks(ctrl, act.Vec, act.Hold) {
				return false
			}
		}
		time.Sleep(20 * time.Millisecond)
	}
}
