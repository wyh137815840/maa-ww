package account

import (
	"encoding/json"
	"regexp"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// Register registers the account CustomAction components.
func Register() {
	maa.AgentServerRegisterCustomAction("AccountLoop", &LoopAction{})
	maa.AgentServerRegisterCustomAction("AccountHoldKey", &HoldKeyAction{})
	maa.AgentServerRegisterCustomAction("AccountFail", &FailAction{})
}

// LoopAction runs "switch to account → run every enabled task" once per configured phone.
//
// Task options chosen on the MultiAccount task (NestKind, ...) are task-level pipeline overrides
// and are inherited by ctx.RunTask, so sub-tasks behave as if run standalone with those options.
type LoopAction struct{}

var _ maa.CustomActionRunner = &LoopAction{}

// TaskSpec is one sub-task run for every account.
type TaskSpec struct {
	Name  string `json:"name"`
	Entry string `json:"entry"`
	// Gate is a pipeline node whose attach.on mirrors the checkbox option case (default off, the
	// case's pipeline_override turns it on). Separate nodes, because several overrides on the same
	// node field replace each other instead of merging.
	Gate string `json:"gate"`
}

type loopParam struct {
	Phones      string     `json:"phones"`
	EnsureEntry string     `json:"ensure_entry"`
	SwitchEntry string     `json:"switch_entry"`
	PickNode    string     `json:"pick_node"`
	CurrentNode string     `json:"current_node"`
	Tasks       []TaskSpec `json:"tasks"`
}

// defaultTasks is the fixed per-account task order. It lives in Go, not in the node's
// custom_action_param, because the AccountPhones input option overrides that whole param object
// ({"phones": "..."}) and would wipe any other keys declared in the pipeline.
var defaultTasks = []TaskSpec{
	{Name: "Nest", Entry: "NestRun", Gate: "AccountTaskNest"},
	{Name: "Tacet", Entry: "TacetMain", Gate: "AccountTaskTacet"},
	// Daily last: the activity points it claims come from the tasks above.
	{Name: "Daily", Entry: "DailyMain", Gate: "AccountTaskDaily"},
}

func defaultLoopParam() loopParam {
	return loopParam{
		Tasks:       defaultTasks,
		EnsureEntry: "AccountEnsureGame",
		SwitchEntry: "AccountSwitchMain",
		PickNode:    "AccountPickRow",
		CurrentNode: "AccountCurrentIsTarget",
	}
}

func parseLoopParam(raw string) loopParam {
	p := defaultLoopParam()
	if raw == "" {
		return p
	}
	var o loopParam
	if err := json.Unmarshal([]byte(raw), &o); err != nil {
		log.Warn().Err(err).Str("raw", raw).Msg("AccountLoop: bad param")
		return p
	}
	p.Phones = o.Phones
	if len(o.Tasks) > 0 {
		p.Tasks = o.Tasks
	}
	if o.EnsureEntry != "" {
		p.EnsureEntry = o.EnsureEntry
	}
	if o.SwitchEntry != "" {
		p.SwitchEntry = o.SwitchEntry
	}
	if o.PickNode != "" {
		p.PickNode = o.PickNode
	}
	if o.CurrentNode != "" {
		p.CurrentNode = o.CurrentNode
	}
	return p
}

// gateOn reports whether the checkbox case behind gate is selected.
func gateOn(ctx *maa.Context, gate string) bool {
	if gate == "" {
		return true
	}
	n, err := ctx.GetNode(gate)
	if err != nil || n == nil {
		log.Warn().Err(err).Str("gate", gate).Msg("AccountLoop: gate node unreadable, treating as off")
		return false
	}
	on, _ := n.Attach["on"].(bool)
	log.Info().Str("gate", gate).Interface("attach", n.Attach).Bool("on", on).Msg("AccountLoop: gate")
	return on
}

// pickOverride makes the switch pipeline match the account whose masked phone ends in lastFour,
// both on the login sheet's current row and on the dropdown rows.
func pickOverride(lastFour string, nodes ...string) map[string]any {
	ov := map[string]any{}
	for _, n := range nodes {
		if n == "" {
			continue
		}
		ov[n] = map[string]any{"expected": []string{regexp.QuoteMeta(lastFour)}}
	}
	return ov
}

func succeeded(d *maa.TaskDetail, err error) bool {
	return err == nil && d != nil && d.Status.Success()
}

func (a *LoopAction) Run(ctx *maa.Context, arg *maa.CustomActionArg) bool {
	tasker := ctx.GetTasker()
	if tasker == nil {
		log.Error().Msg("AccountLoop: tasker is nil")
		return false
	}
	param := defaultLoopParam()
	if arg != nil {
		param = parseLoopParam(arg.CustomActionParam)
	}

	accounts, bad, dup := ParsePhones(param.Phones)
	for _, b := range bad {
		log.Warn().Str("item", b).Msg("AccountLoop: ignored (need a phone number or its last 4 digits)")
	}
	for _, d := range dup {
		log.Warn().Str("item", d).Msg("AccountLoop: ignored (same last 4 digits as an earlier account)")
	}
	if len(accounts) == 0 {
		log.Error().Msg("AccountLoop: no valid phone numbers configured")
		return false
	}

	var tasks []TaskSpec
	for _, t := range param.Tasks {
		if t.Entry != "" && gateOn(ctx, t.Gate) {
			tasks = append(tasks, t)
		}
	}
	log.Info().Int("accounts", len(accounts)).Int("tasks", len(tasks)).Msg("AccountLoop: start")

	failed := 0
	for i, acc := range accounts {
		if tasker.Stopping() {
			return false
		}
		log.Info().Int("index", i+1).Int("total", len(accounts)).Str("last4", acc.LastFour).Msg("AccountLoop: switching")

		// Make sure the game is up (cold device / crashed / black screen) before touching menus.
		if d, err := ctx.RunTask(param.EnsureEntry); !succeeded(d, err) {
			log.Error().Err(err).Msg("AccountLoop: could not bring the game up, skipping this account")
			failed++
			continue
		}
		d, err := ctx.RunTask(param.SwitchEntry, pickOverride(acc.LastFour, param.PickNode, param.CurrentNode))
		if !succeeded(d, err) {
			// Cannot trust any task to run on the wrong account.
			log.Error().Err(err).Str("last4", acc.LastFour).Msg("AccountLoop: switch failed, skipping this account")
			failed++
			continue
		}
		log.Info().Str("last4", acc.LastFour).Msg("AccountLoop: switched")
		for _, t := range tasks {
			if tasker.Stopping() {
				return false
			}
			start := time.Now()
			log.Info().Str("last4", acc.LastFour).Str("task", t.Name).Msg("AccountLoop: run task")
			d, err := ctx.RunTask(t.Entry)
			log.Info().Str("last4", acc.LastFour).Str("task", t.Name).Bool("ok", succeeded(d, err)).
				Dur("elapsed", time.Since(start)).Msg("AccountLoop: task done")
		}
	}
	if failed == len(accounts) {
		return false
	}
	log.Info().Int("failed_switches", failed).Msg("AccountLoop: finished")
	return true
}
