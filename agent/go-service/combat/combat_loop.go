package combat

import (
	"encoding/json"
	"image"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// CombatLoopAction holds the Tacet (and future instance) combat loop until settle.
type CombatLoopAction struct{}

var _ maa.CustomActionRunner = &CombatLoopAction{}

type combatLoopParam struct {
	ExitNodes         []string `json:"exit_nodes"`
	MaxDurationMs     int64    `json:"max_duration_ms"`
	HUDNode           string   `json:"hud_node"`
	LockEveryN        int      `json:"lock_every_n"`
	RetargetTimeoutMs int64    `json:"retarget_timeout_ms"`
}

func defaultCombatLoopParam() combatLoopParam {
	return combatLoopParam{
		ExitNodes: []string{
			"TacetSettleSuccessOCR",
			"TacetChallengeComplete",
			"TacetClaimReward",
			"TacetClaimRewardByOCR",
			"TacetTreasureSeen",
		},
		MaxDurationMs:     300000,
		HUDNode:           "InTacetCombat",
		LockEveryN:        3,
		RetargetTimeoutMs: 4000,
	}
}

func parseCombatLoopParam(raw string) combatLoopParam {
	p := defaultCombatLoopParam()
	if raw == "" {
		return p
	}
	var override combatLoopParam
	if err := json.Unmarshal([]byte(raw), &override); err != nil {
		log.Warn().Err(err).Str("raw", raw).Msg("CombatLoop: bad custom_action_param, using defaults")
		return p
	}
	if len(override.ExitNodes) > 0 {
		p.ExitNodes = override.ExitNodes
	}
	if override.MaxDurationMs > 0 {
		p.MaxDurationMs = override.MaxDurationMs
	}
	if override.HUDNode != "" {
		p.HUDNode = override.HUDNode
	}
	if override.LockEveryN > 0 {
		p.LockEveryN = override.LockEveryN
	}
	if override.RetargetTimeoutMs > 0 {
		p.RetargetTimeoutMs = override.RetargetTimeoutMs
	}
	return p
}

func (a *CombatLoopAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("CombatLoop: tasker is nil")
		return false
	}
	ctrl := tasker.GetController()
	if ctrl == nil {
		log.Error().Msg("CombatLoop: controller is nil")
		return false
	}

	param := defaultCombatLoopParam()
	if arg != nil {
		param = parseCombatLoopParam(arg.CustomActionParam)
	}

	log.Info().
		Strs("exit_nodes", param.ExitNodes).
		Int64("max_duration_ms", param.MaxDurationMs).
		Int64("retarget_timeout_ms", param.RetargetTimeoutMs).
		Msg("CombatLoop: start")

	pad := NewPad(ctrl)
	slot := 0
	rounds := 0
	enteredCombat := false
	deadline := time.Now().Add(time.Duration(param.MaxDurationMs) * time.Millisecond)
	retargetTO := time.Duration(param.RetargetTimeoutMs) * time.Millisecond
	if retargetTO <= 0 {
		retargetTO = 4 * time.Second
	}

	pad.Lock()
	time.Sleep(150 * time.Millisecond)

	stop := func() bool {
		if tasker.Stopping() {
			return true
		}
		hit, name := peekExit(ctx, ctrl, param.ExitNodes)
		if hit {
			log.Info().Str("node", name).Msg("CombatLoop: exit during perform")
			return true
		}
		return false
	}

	for {
		if tasker.Stopping() {
			log.Info().Msg("CombatLoop: stopping")
			return false
		}
		if time.Now().After(deadline) {
			log.Warn().Msg("CombatLoop: max duration reached")
			return true
		}

		if hit, name := peekExit(ctx, ctrl, param.ExitNodes); hit {
			log.Info().Str("node", name).Msg("CombatLoop: exit node hit")
			return true
		}

		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			log.Warn().Err(err).Msg("CombatLoop: screencap failed")
			time.Sleep(100 * time.Millisecond)
			continue
		}

		combatNow := inCombat(ctx, img)
		if combatNow {
			enteredCombat = true
		} else {
			ok := ensureInCombat(ctx, ctrl, pad, retargetTO)
			if !ok {
				// Settle may appear while retargeting — check before declaring out-of-combat.
				if hit, name := peekExit(ctx, ctrl, param.ExitNodes); hit {
					log.Info().Str("node", name).Msg("CombatLoop: exit node hit after retarget fail")
					return true
				}
				if enteredCombat || rounds > 0 {
					log.Info().Int("rounds", rounds).Msg("CombatLoop: out of combat → hand off treasure")
					return true
				}
				time.Sleep(200 * time.Millisecond)
				continue
			}
			enteredCombat = true
		}

		waitHUD := func(timeout time.Duration) bool {
			return waitForCombatHUD(ctx, ctrl, tasker, param.ExitNodes, timeout)
		}

		if param.LockEveryN > 0 && rounds%param.LockEveryN == 0 {
			pad.Lock()
			time.Sleep(80 * time.Millisecond)
		}

		next, aborted := NewBaseChar(pad, slot).Perform(waitHUD, stop)
		slot = next
		rounds++
		if aborted {
			log.Info().Int("rounds", rounds).Msg("CombatLoop: aborted perform for exit")
			return true
		}
	}
}

func anyExitHit(ctx *maa.Context, img image.Image, nodes []string) (bool, string) {
	for _, name := range nodes {
		if name == "" {
			continue
		}
		detail, err := ctx.RunRecognition(name, img)
		if err != nil || detail == nil {
			continue
		}
		if detail.Hit {
			return true, name
		}
	}
	return false, ""
}
