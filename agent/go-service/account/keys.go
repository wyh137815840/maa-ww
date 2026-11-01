package account

import (
	"encoding/json"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// HoldKeyAction holds one Android keycode down for hold_ms (e.g. Start=108 to open the
// 「是否确定退出游戏？」dialog from the Terminal page — the page footer says "(长按) 退出游戏").
type HoldKeyAction struct{}

var _ maa.CustomActionRunner = &HoldKeyAction{}

type holdKeyParam struct {
	Key    int32 `json:"key"`
	HoldMs int64 `json:"hold_ms"`
}

func (a *HoldKeyAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	p := holdKeyParam{HoldMs: 1500}
	if arg != nil && arg.CustomActionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomActionParam), &p); err != nil {
			log.Error().Err(err).Msg("AccountHoldKey: bad param")
			return false
		}
	}
	if p.Key == 0 {
		log.Error().Msg("AccountHoldKey: key missing")
		return false
	}
	tasker := ctx.GetTasker()
	if tasker == nil || tasker.GetController() == nil {
		log.Error().Msg("AccountHoldKey: no controller")
		return false
	}
	ctrl := tasker.GetController()
	log.Info().Int32("key", p.Key).Int64("hold_ms", p.HoldMs).Msg("AccountHoldKey")
	ctrl.PostKeyDown(p.Key).Wait()
	time.Sleep(time.Duration(p.HoldMs) * time.Millisecond)
	ctrl.PostKeyUp(p.Key).Wait()
	return true
}

// FailAction always fails: ends a pipeline branch as a failed task so RunTask reports failure.
type FailAction struct{}

var _ maa.CustomActionRunner = &FailAction{}

func (a *FailAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	log.Warn().Msg("AccountFail: switch pipeline gave up")
	return false
}
