package combat

import (
	"testing"
	"time"
)

func TestParseNestAbsorbSearchParam(t *testing.T) {
	p := parseNestAbsorbSearchParam("")
	if len(p.PromptNodes) != 1 || p.PromptNodes[0] != "NestAbsorbPrompt" || p.TimeoutMs != 45000 || p.WalkMs != 1200 {
		t.Fatalf("defaults wrong: %+v", p)
	}
	p = parseNestAbsorbSearchParam(`{"timeout_ms":9000,"walk_ms":800,"prompt_nodes":["X"]}`)
	if p.TimeoutMs != 9000 || p.WalkMs != 800 || p.PromptNodes[0] != "X" || p.ScanSteps != 8 {
		t.Fatalf("override wrong: %+v", p)
	}
}

func TestNestAbsorbPlanCircleThenShortWalk(t *testing.T) {
	p := defaultNestAbsorbSearchParam()
	plan := nestAbsorbPlan(p)
	// 8 × (yaw slice + look pause) then one walk leg.
	if len(plan) != 8*2+1 {
		t.Fatalf("plan len = %d", len(plan))
	}
	var yaw time.Duration
	for _, l := range plan[:len(plan)-1] {
		if !l.Look {
			yaw += l.Dur
		}
	}
	if yaw != 3000*time.Millisecond {
		t.Fatalf("slices must sum to one circle, got %v", yaw)
	}
	walk := plan[len(plan)-1]
	if walk.Look || walk.Vec.LY >= 0 {
		t.Fatalf("last leg must walk forward: %+v", walk)
	}
	if walk.Dur != 1200*time.Millisecond {
		t.Fatalf("walk leg = %v, want 1.2s", walk.Dur)
	}
}
