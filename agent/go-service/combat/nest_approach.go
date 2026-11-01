package combat

import (
	"encoding/json"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// NestApproachAction walks straight ahead (left stick forward) after a nest fast-travel until one
// of the gate nodes hits (default: the nest quest bar "清剿残象聚落 / 已击败残象"), then hands off.
//
// 残象聚落 lands the character a short way from the enemies and they only aggro once close, so the
// run has to move first (user-confirmed; 梦魇祛除 spawns with the enemies already in view and does
// not use this). Camera is not steered: straight ahead, as in ok-ww run_until(in_combat, 'w').
type NestApproachAction struct{}

var _ maa.CustomActionRunner = &NestApproachAction{}

type nestApproachParam struct {
	GateNodes []string `json:"gate_nodes"`
	TimeoutMs int64    `json:"timeout_ms"`
	StepMs    int64    `json:"step_ms"`  // one stick command length
	Forward   int      `json:"forward"`  // |left-stick Y| magnitude, 1..32767
	CheckMs   int64    `json:"check_ms"` // frame check cadence while walking
}

func defaultNestApproachParam() nestApproachParam {
	return nestApproachParam{
		GateNodes: []string{"NestInCombat"},
		TimeoutMs: 90000,
		StepMs:    900,
		Forward:   30000,
		CheckMs:   500,
	}
}

func parseNestApproachParam(raw string) nestApproachParam {
	p := defaultNestApproachParam()
	if raw == "" {
		return p
	}
	var o nestApproachParam
	if err := json.Unmarshal([]byte(raw), &o); err != nil {
		log.Warn().Err(err).Str("raw", raw).Msg("NestApproach: bad param, using defaults")
		return p
	}
	if len(o.GateNodes) > 0 {
		p.GateNodes = o.GateNodes
	}
	if o.TimeoutMs > 0 {
		p.TimeoutMs = o.TimeoutMs
	}
	if o.StepMs > 0 {
		p.StepMs = o.StepMs
	}
	if o.Forward > 0 {
		p.Forward = o.Forward
	}
	if p.Forward > 32767 {
		p.Forward = 32767
	}
	if o.CheckMs > 0 {
		p.CheckMs = o.CheckMs
	}
	return p
}

func (a *NestApproachAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("NestApproach: tasker is nil")
		return false
	}
	ctrl := tasker.GetController()
	if ctrl == nil {
		log.Error().Msg("NestApproach: controller is nil")
		return false
	}
	param := defaultNestApproachParam()
	if arg != nil {
		param = parseNestApproachParam(arg.CustomActionParam)
	}
	log.Info().Strs("gate_nodes", param.GateNodes).Int64("timeout_ms", param.TimeoutMs).Msg("NestApproach: start")

	step := time.Duration(param.StepMs) * time.Millisecond
	check := time.Duration(param.CheckMs) * time.Millisecond
	deadline := time.Now().Add(time.Duration(param.TimeoutMs) * time.Millisecond)
	defer stickNeutral(ctrl)

	var holdUntil time.Time
	for {
		if tasker.Stopping() {
			return false
		}
		if time.Now().After(deadline) {
			log.Warn().Msg("NestApproach: timeout without reaching the nest")
			return false
		}
		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err == nil && img != nil {
			if hit, name := anyExitHit(ctx, img, param.GateNodes); hit {
				log.Info().Str("node", name).Msg("NestApproach: gate hit")
				return true
			}
		}
		// Refresh the forward command before the previous hold lapses (no stop-and-go).
		if time.Until(holdUntil) < step*4/10 {
			pulseSticks(ctrl, stickVec{LY: -param.Forward}, step)
			holdUntil = time.Now().Add(clampHold(step))
		}
		time.Sleep(check)
	}
}
