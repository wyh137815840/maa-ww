package combat

import (
	"encoding/json"
	"fmt"
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
	LockEveryN        int      `json:"lock_every_n"` // 0 = only lock at start / retarget (ok-ww style)
	RetargetTimeoutMs int64    `json:"retarget_timeout_ms"`
	ExitCheckEveryN   int      `json:"exit_check_every_n"` // settle scan cadence; default 4 rounds
	// Countdown watch (see timer_watch.go): leave when the HUD timer was seen, then is gone this long.
	TimerNode   string `json:"timer_node"`
	TimerGoneMs int64  `json:"timer_gone_ms"`
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
		LockEveryN:        0, // was 3 — periodic R3 makes combat stutter
		RetargetTimeoutMs: 4000,
		ExitCheckEveryN:   4,
		TimerNode:         "TacetTimerOCR",
		TimerGoneMs:       12000,
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
	if n, ok := overrideInt(raw, "lock_every_n"); ok {
		p.LockEveryN = n
	}
	if override.RetargetTimeoutMs > 0 {
		p.RetargetTimeoutMs = override.RetargetTimeoutMs
	}
	if override.ExitCheckEveryN > 0 {
		p.ExitCheckEveryN = override.ExitCheckEveryN
	}
	var rawMap map[string]json.RawMessage
	if json.Unmarshal([]byte(raw), &rawMap) == nil {
		// Present-but-empty timer_node (or 0 ms) explicitly disables the watch.
		if _, ok := rawMap["timer_node"]; ok {
			p.TimerNode = override.TimerNode
		}
		if _, ok := rawMap["timer_gone_ms"]; ok {
			p.TimerGoneMs = override.TimerGoneMs
		}
	}
	return p
}

func overrideInt(raw, key string) (int, bool) {
	var m map[string]json.RawMessage
	if json.Unmarshal([]byte(raw), &m) != nil {
		return 0, false
	}
	v, ok := m[key]
	if !ok {
		return 0, false
	}
	var n int
	if json.Unmarshal(v, &n) != nil {
		return 0, false
	}
	return n, true
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
	if param.ExitCheckEveryN <= 0 {
		param.ExitCheckEveryN = 4
	}

	log.Info().
		Strs("exit_nodes", param.ExitNodes).
		Int64("max_duration_ms", param.MaxDurationMs).
		Int("lock_every_n", param.LockEveryN).
		Int("exit_check_every_n", param.ExitCheckEveryN).
		Str("timer_node", param.TimerNode).
		Int64("timer_gone_ms", param.TimerGoneMs).
		Msg("CombatLoop: start")
	timer := newTimerWatch(param.TimerNode, time.Duration(param.TimerGoneMs)*time.Millisecond)

	pad := NewPad(ctrl)
	slot := 0
	team := teamState{Current: -1}
	lastTeamLog := ""
	preSwapDumps := 0
	rounds := 0
	enteredCombat := false
	deadline := time.Now().Add(time.Duration(param.MaxDurationMs) * time.Millisecond)
	retargetTO := time.Duration(param.RetargetTimeoutMs) * time.Millisecond
	if retargetTO <= 0 {
		retargetTO = 4 * time.Second
	}

	// One initial lock (ok-ww wait_combat middle_click style), not every N rounds.
	pad.Lock()
	time.Sleep(120 * time.Millisecond)

	// Lightweight stop: settle scan on round cadence (once per round) or time cadence.
	lastExitCheck := time.Time{}
	lastExitRound := -1
	stop := func() bool {
		if tasker.Stopping() {
			return true
		}
		scan, consumeRound := exitScanDecision(rounds, param.ExitCheckEveryN, lastExitRound, time.Since(lastExitCheck), false)
		if !scan {
			return false
		}
		if consumeRound {
			lastExitRound = rounds
		}
		lastExitCheck = time.Now()
		hit, name := peekExit(ctx, ctrl, param.ExitNodes, timer)
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

		if scan, consumeRound := exitScanDecision(rounds, param.ExitCheckEveryN, lastExitRound, time.Since(lastExitCheck), rounds == 0); scan {
			if consumeRound {
				lastExitRound = rounds
			}
			lastExitCheck = time.Now()
			if hit, name := peekExit(ctx, ctrl, param.ExitNodes, timer); hit {
				log.Info().Str("node", name).Msg("CombatLoop: exit node hit")
				return true
			}
		}

		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			log.Warn().Err(err).Msg("CombatLoop: screencap failed")
			time.Sleep(80 * time.Millisecond)
			continue
		}

		// Switching onto a fallen teammate opens "选择复苏物品": close it (A = back), never confirm items.
		if nodeHit(ctx, img, NodeCombatRevivePopup) {
			log.Warn().Msg("CombatLoop: revive item popup, closing with A")
			dumpDebugFrame(img, "revive_popup")
			pad.Click(KeyJump)
			time.Sleep(500 * time.Millisecond)
			continue
		}

		combatNow := inCombat(ctx, img)
		if combatNow {
			enteredCombat = true
		} else {
			ok := ensureInCombat(ctx, ctrl, pad, retargetTO)
			if !ok {
				if hit, name := peekExit(ctx, ctrl, param.ExitNodes, timer); hit {
					log.Info().Str("node", name).Msg("CombatLoop: exit node hit after retarget fail")
					return true
				}
				if enteredCombat || rounds > 0 {
					log.Info().Int("rounds", rounds).Msg("CombatLoop: out of combat → hand off treasure")
					return true
				}
				time.Sleep(150 * time.Millisecond)
				continue
			}
			enteredCombat = true
		}

		if param.LockEveryN > 0 && rounds%param.LockEveryN == 0 {
			pad.Lock()
			time.Sleep(60 * time.Millisecond)
		}

		team = readTeam(img, &team)
		if logTeamChange(&lastTeamLog, team) && team.aliveCount() < 3 {
			dumpDebugFrame(img, "team_dead")
		}
		if team.Current >= 0 && team.Current != slot {
			log.Info().Int("tracked", slot).Int("hud", team.Current).Msg("CombatLoop: slot resync from HUD")
			slot = team.Current
		}

		char := NewBaseChar(pad, slot)
		char.pickNext = func(cur int) int {
			// Fresh frame: a teammate may have died during this rotation.
			ctrl.PostScreencap().Wait()
			if fresh, err := ctrl.CacheImage(); err == nil && fresh != nil {
				team = readTeam(fresh, &team)
			}
			n := team.nextAlive(cur)
			if preSwapDumps < 8 {
				preSwapDumps++
				if fresh, err := ctrl.CacheImage(); err == nil {
					dumpDebugFrame(fresh, fmt.Sprintf("preswap_%d_to%d", cur, n))
				}
			}
			if n != (cur+1)%3 {
				log.Info().Int("from", cur).Int("to", n).Msg("CombatLoop: skipped dead teammate")
			}
			return n
		}
		next, aborted := char.Perform(stop)
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
