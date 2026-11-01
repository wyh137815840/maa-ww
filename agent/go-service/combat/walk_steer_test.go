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

func TestShouldRefreshHold(t *testing.T) {
	hold := 700 * time.Millisecond
	if shouldRefreshHold(100*time.Millisecond, hold) {
		t.Fatal("too early to refresh")
	}
	if !shouldRefreshHold(450*time.Millisecond, hold) {
		t.Fatal("should refresh before expiry")
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
