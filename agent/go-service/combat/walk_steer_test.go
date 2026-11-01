package combat

import (
	"testing"
	"time"
)

func steer(cx, cy int, last walkDir, centered bool) (walkDir, bool) {
	return steerDecision(steerInput{
		BoxCX: cx, BoxCY: cy, LastDir: last, Centered: centered,
		XThreshold: 90, YOffset: 36,
	})
}

func TestSteerStrafesUntilCentered(t *testing.T) {
	if d, c := steer(900, 360, dirNone, false); d != dirD || c {
		t.Fatalf("right of center: %v %v", d, c)
	}
	if d, c := steer(300, 360, dirNone, false); d != dirA || c {
		t.Fatalf("left of center: %v %v", d, c)
	}
}

func TestSteerTighterThresholdBeforeMoving(t *testing.T) {
	// dx=70: inside x_threshold(90) but outside the 50px start threshold.
	if d, c := steer(710, 360, dirNone, false); c || d != dirD {
		t.Fatalf("not moving yet should still strafe: %v %v", d, c)
	}
	// Once moving, 70px is acceptable.
	if _, c := steer(710, 360, dirA, false); !c {
		t.Fatal("moving: dx=70 should count as centered")
	}
}

func TestSteerVerticalBands(t *testing.T) {
	// centered, marker high (cy small) -> forward
	if d, _ := steer(640, 200, dirW, true); d != dirW {
		t.Fatalf("high marker: %v", d)
	}
	// centered, marker low -> back
	if d, _ := steer(640, 600, dirS, true); d != dirS {
		t.Fatalf("low marker: %v", d)
	}
	// centered stays latched even if dx drifts
	if _, c := steer(900, 300, dirW, true); !c {
		t.Fatal("centered must latch")
	}
}

func TestSearchPlanNoFlipFlop(t *testing.T) {
	// No two consecutive legs may be exact opposites held for <1s each
	// (that was the W/S flip-flop that netted ~zero motion).
	for i := 0; i < len(searchPlan); i++ {
		a, b := searchSegment(i), searchSegment(i+1)
		if b.Dir == oppositeDir(a.Dir) && (a.Dur < time.Second || b.Dur < time.Second) {
			t.Fatalf("legs %d/%d flip-flop: %v %v", i, i+1, a, b)
		}
		if a.Dur < time.Second {
			t.Fatalf("leg %d too short: %v", i, a.Dur)
		}
	}
	if searchSegment(0).Dir != dirW {
		t.Fatal("search must start forward")
	}
	if searchSegment(len(searchPlan)) != searchSegment(0) {
		t.Fatal("search plan must wrap")
	}
}

func TestNeedsRewriteSteadyHold(t *testing.T) {
	hold := 700 * time.Millisecond
	// 100ms elapsed of a 700ms hold -> 600ms remaining: no rewrite.
	if needsRewrite(600*time.Millisecond, hold) {
		t.Fatal("too early to refresh")
	}
	// 450ms elapsed -> 250ms remaining (<280ms): refresh before expiry.
	if !needsRewrite(250*time.Millisecond, hold) {
		t.Fatal("should refresh before expiry")
	}
	// Already expired (negative remaining) must rewrite.
	if !needsRewrite(-10*time.Millisecond, hold) {
		t.Fatal("expired hold must be rewritten")
	}
}

// 700ms steer hold, 500ms elapsed, then a same-direction 2200ms search leg is requested.
// The old hold only has 200ms left, so it must be rewritten (otherwise it expires and the
// stick recenters mid-leg).
func TestNeedsRewriteSteerToLongSearch(t *testing.T) {
	oldRemaining := 700*time.Millisecond - 500*time.Millisecond
	newHold := clampHold(2200 * time.Millisecond)
	if newHold != 2000*time.Millisecond {
		t.Fatalf("clamp: %v", newHold)
	}
	if !needsRewrite(oldRemaining, newHold) {
		t.Fatal("old 200ms remaining must trigger rewrite for a 2000ms leg")
	}
	// The pre-fix rule (elapsed >= 60% of the NEW hold) would have skipped it.
	if 500*time.Millisecond >= newHold*6/10 {
		t.Fatal("test premise broken: old rule should have skipped")
	}
}

func TestClampHold(t *testing.T) {
	if clampHold(10*time.Millisecond) != minStickHold || clampHold(5*time.Second) != maxStickHold {
		t.Fatal("clamp bounds wrong")
	}
	if clampHold(700*time.Millisecond) != 700*time.Millisecond {
		t.Fatal("in-range hold must pass through")
	}
	// Must match what the pump receives.
	if _, ms := stickPayload(0, -30000, 5*time.Second); ms != maxStickHold.Milliseconds() {
		t.Fatalf("payload clamp %d", ms)
	}
}

func TestFrameStats(t *testing.T) {
	var s frameStats
	if s.avg(true) != 0 || s.avg(false) != 0 {
		t.Fatal("empty avg must be 0")
	}
	s.add(false, 100*time.Millisecond)
	s.add(false, 300*time.Millisecond)
	s.add(true, 700*time.Millisecond)
	if s.avg(false) != 200*time.Millisecond || s.avg(true) != 700*time.Millisecond {
		t.Fatalf("avg plain=%v ocr=%v", s.avg(false), s.avg(true))
	}
	if s.plainN != 2 || s.ocrN != 1 {
		t.Fatalf("counts %d %d", s.plainN, s.ocrN)
	}
}

func TestMarkerFresh(t *testing.T) {
	ttl := 1500 * time.Millisecond
	if !markerFresh(time.Second, ttl) || markerFresh(2*time.Second, ttl) {
		t.Fatal("ttl boundary wrong")
	}
}

func TestCadence(t *testing.T) {
	if !cadence(1, 5) || cadence(2, 5) || !cadence(5, 5) || !cadence(10, 5) {
		t.Fatal("cadence wrong")
	}
	if !cadence(3, 1) || !cadence(3, 0) {
		t.Fatal("every<=1 must always run")
	}
}

func TestParseWalkTreasureParamDefaultsAndOverride(t *testing.T) {
	p := parseWalkTreasureParam("")
	if p.GateMs != 2500 || p.OCREvery != 5 || len(p.TreasureOCRNodes) != 1 {
		t.Fatalf("defaults: %+v", p)
	}
	p = parseWalkTreasureParam(`{"gate_ms":1000,"ocr_every":3,"treasure_nodes":["X"]}`)
	if p.GateMs != 1000 || p.OCREvery != 3 || len(p.TreasureNodes) != 1 || p.TreasureNodes[0] != "X" {
		t.Fatalf("override: %+v", p)
	}
	if len(p.ClaimNodes) != 1 { // untouched default
		t.Fatalf("claim defaults lost: %+v", p)
	}
}
