package combat

import (
	"testing"
	"time"
)

func TestExitScanDecision_RoundOnce(t *testing.T) {
	// First hit at round 4 should scan and consume.
	scan, consume := exitScanDecision(4, 4, -1, time.Millisecond, false)
	if !scan || !consume {
		t.Fatalf("round 4 first: scan=%v consume=%v", scan, consume)
	}
	// Same round already consumed: no re-fire from round trigger.
	scan, consume = exitScanDecision(4, 4, 4, time.Millisecond, false)
	if scan || consume {
		t.Fatalf("round 4 again: scan=%v consume=%v want false,false", scan, consume)
	}
	// Next cadence round.
	scan, consume = exitScanDecision(8, 4, 4, time.Millisecond, false)
	if !scan || !consume {
		t.Fatalf("round 8: scan=%v consume=%v", scan, consume)
	}
}

func TestExitScanDecision_TimeCadence(t *testing.T) {
	scan, consume := exitScanDecision(5, 4, 4, 3*time.Second, false)
	if !scan || consume {
		t.Fatalf("time cadence: scan=%v consume=%v want true,false", scan, consume)
	}
	scan, consume = exitScanDecision(5, 4, 4, time.Second, false)
	if scan || consume {
		t.Fatalf("within window: scan=%v consume=%v want false,false", scan, consume)
	}
}

func TestExitScanDecision_Force(t *testing.T) {
	scan, consume := exitScanDecision(0, 4, -1, 0, true)
	if !scan || consume {
		t.Fatalf("force: scan=%v consume=%v want true,false", scan, consume)
	}
}

func TestOppositeDir(t *testing.T) {
	cases := []struct {
		in, want walkDir
	}{
		{dirW, dirS},
		{dirS, dirW},
		{dirA, dirD},
		{dirD, dirA},
		{dirNone, dirW},
	}
	for _, c := range cases {
		if got := oppositeDir(c.in); got != c.want {
			t.Fatalf("oppositeDir(%v)=%v want %v", c.in, got, c.want)
		}
	}
}
