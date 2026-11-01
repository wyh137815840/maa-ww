package combat

import (
	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// NestKindsAction runs the nest chain (NestMain) once per selected kind: 残象聚落 and/or 梦魇祛除.
//
// Which kinds are selected comes from the NestKind checkbox option. Each case turns on its own
// gate node (attach.on = true); separate nodes because overrides on the same node field replace
// each other. A kind that fails does not stop the next one.
type NestKindsAction struct{}

var _ maa.CustomActionRunner = &NestKindsAction{}

type nestKind struct {
	name string
	gate string
	// override picks the left-column tab; the swipe is only needed to reveal 梦魇祛除.
	override map[string]any
}

var nestKinds = []nestKind{
	{
		name: "Canxiang",
		gate: "NestKindCanxiang",
		override: map[string]any{
			"NestTabCanxiang":   map[string]any{"enabled": true},
			"NestTabNightmare":  map[string]any{"enabled": false},
			"NestLeftListSwipe": map[string]any{"enabled": false},
		},
	},
	{
		name: "Nightmare",
		gate: "NestKindNightmare",
		override: map[string]any{
			"NestTabCanxiang":   map[string]any{"enabled": false},
			"NestTabNightmare":  map[string]any{"enabled": true},
			"NestLeftListSwipe": map[string]any{"enabled": true},
		},
	},
}

func nestGateOn(ctx *maa.Context, gate string) bool {
	n, err := ctx.GetNode(gate)
	if err != nil || n == nil {
		log.Warn().Err(err).Str("gate", gate).Msg("NestKinds: gate node unreadable, treating as off")
		return false
	}
	on, _ := n.Attach["on"].(bool)
	return on
}

func (a *NestKindsAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("NestKinds: tasker is nil")
		return false
	}
	ran, ok := 0, 0
	for _, k := range nestKinds {
		if tasker.Stopping() {
			return false
		}
		if !nestGateOn(ctx, k.gate) {
			continue
		}
		ran++
		log.Info().Str("kind", k.name).Msg("NestKinds: run")
		d, err := ctx.RunTask("NestMain", k.override)
		success := err == nil && d != nil && d.Status.Success()
		log.Info().Str("kind", k.name).Bool("ok", success).Msg("NestKinds: done")
		if success {
			ok++
		}
	}
	if ran == 0 {
		log.Warn().Msg("NestKinds: no nest kind selected")
		return false
	}
	return ok > 0
}
