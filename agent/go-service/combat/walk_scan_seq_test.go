package combat

import (
	"testing"
	"time"
)

type simSend struct {
	At   time.Duration // offset from t0 when the command was sent
	Vec  stickVec
	Hold time.Duration
}

// simulateScan drives scanSeq like Run does: each frame costs `cost` (capture+recognition),
// then step() runs with now=frameStart+cost; frames are back to back. Returns every send.
func simulateScan(plan []scanLeg, cost time.Duration, total time.Duration) []simSend {
	t0 := time.Unix(1000, 0)
	seq := newScanSeq(plan)
	var out []simSend
	for fs := t0; fs.Sub(t0) < total; fs = fs.Add(cost + 20*time.Millisecond) {
		now := fs.Add(cost)
		if a := seq.step(now, fs); a.Send {
			out = append(out, simSend{At: now.Sub(t0), Vec: a.Vec, Hold: a.Hold})
		}
	}
	return out
}

func yawSum(sends []simSend, upTo int) time.Duration {
	var d time.Duration
	for _, s := range sends[:upTo] {
		if s.Vec.RX != 0 {
			d += s.Hold
		}
	}
	return d
}

// Slice length must be exactly the planned length no matter how slow recognition is.
func TestScanSeqYawExactUnderSlowFrames(t *testing.T) {
	plan := cameraScanPlan(8, 3*time.Second, 20000)
	for _, cost := range []time.Duration{50 * time.Millisecond, 250 * time.Millisecond, 700 * time.Millisecond, 1500 * time.Millisecond} {
		sends := simulateScan(plan, cost, 120*time.Second)
		// First full circle = first 8 yaw sends.
		n, yaws := 0, 0
		for n < len(sends) && yaws < 8 {
			if sends[n].Vec.RX != 0 {
				yaws++
			}
			n++
		}
		if yaws != 8 {
			t.Fatalf("cost=%v: only %d yaw slices in sim", cost, yaws)
		}
		if got := yawSum(sends, n); got != 3*time.Second {
			t.Fatalf("cost=%v: yaw per circle=%v want 3s", cost, got)
		}
		for _, s := range sends[:n] {
			if s.Vec.RX != 0 && s.Hold != 375*time.Millisecond {
				t.Fatalf("cost=%v: slice hold %v want 375ms", cost, s.Hold)
			}
		}
	}
}

// Each Look leg must wait for a settled observation frame, even when frames are slow.
func TestScanSeqLookWaitsForSettledFrame(t *testing.T) {
	t0 := time.Unix(1000, 0)
	plan := []scanLeg{
		{Vec: stickVec{RX: 10000}, Dur: 100 * time.Millisecond},
		{Vec: stickVec{}, Dur: scanLookPause, Look: true},
		{Vec: stickVec{RX: 10000}, Dur: 100 * time.Millisecond},
	}
	seq := newScanSeq(plan)

	// Frame 1 (cost 40ms): starts the yaw leg.
	if a := seq.step(t0.Add(40*time.Millisecond), t0); !a.Send || a.Vec.RX == 0 {
		t.Fatalf("frame1 should send yaw: %+v", a)
	}
	// Frame 2 ends the yaw leg (>=100ms) → advances to Look and sends neutral.
	if a := seq.step(t0.Add(200*time.Millisecond), t0.Add(100*time.Millisecond)); !a.Send || !a.Vec.zero() {
		t.Fatalf("frame2 should send neutral: %+v", a)
	}
	lookStart := t0.Add(200 * time.Millisecond)

	// Frame 3 captured BEFORE settle (starts 50ms after lookStart): Dur elapsed but not observed.
	// now = lookStart+scanLookPause+10ms so duration is satisfied; frameStart < settle.
	a := seq.step(lookStart.Add(scanLookPause+10*time.Millisecond), lookStart.Add(50*time.Millisecond))
	if a.Send {
		t.Fatalf("must stay in Look leg: %+v", a)
	}
	if seq.idx != 1 {
		t.Fatalf("advanced too early, idx=%d", seq.idx)
	}
	// Frame 4 captured after settle → observed → advance to next yaw leg.
	a = seq.step(lookStart.Add(scanLookPause+500*time.Millisecond), lookStart.Add(scanSettle+10*time.Millisecond))
	if !a.Send || a.Vec.RX == 0 {
		t.Fatalf("settled observation should release the next turn: %+v", a)
	}
}

// Look leg also respects its minimum duration even if an observed frame arrives early.
func TestScanSeqLookMinimumDuration(t *testing.T) {
	t0 := time.Unix(1000, 0)
	plan := []scanLeg{
		{Vec: stickVec{}, Dur: scanLookPause, Look: true},
		{Vec: stickVec{RX: 10000}, Dur: 100 * time.Millisecond},
	}
	seq := newScanSeq(plan)
	seq.step(t0, t0) // sends neutral, legStart=t0
	// observed frame at +200ms (after settle) but only 200ms < 350ms elapsed
	if a := seq.step(t0.Add(220*time.Millisecond), t0.Add(200*time.Millisecond)); a.Send {
		t.Fatalf("must not advance before pause elapsed: %+v", a)
	}
	if a := seq.step(t0.Add(400*time.Millisecond), t0.Add(380*time.Millisecond)); !a.Send || a.Vec.RX == 0 {
		t.Fatalf("should advance after pause: %+v", a)
	}
}

func TestScanSeqResetRestartsPlan(t *testing.T) {
	t0 := time.Unix(1000, 0)
	seq := newScanSeq(cameraScanPlan(4, time.Second, 10000))
	seq.step(t0, t0)
	seq.step(t0.Add(time.Second), t0.Add(time.Second))
	seq.reset()
	if seq.idx != 0 || seq.started {
		t.Fatal("reset must rewind")
	}
	if a := seq.step(t0.Add(2*time.Second), t0.Add(2*time.Second)); !a.Send || a.Vec.RX == 0 {
		t.Fatalf("restart should begin with a yaw slice: %+v", a)
	}
}

func TestAllPlanLegsFitOneCommand(t *testing.T) {
	for _, plan := range [][]scanLeg{
		walkSearchLegs(),
		cameraScanPlan(8, 3*time.Second, 20000),
		cameraScanPlan(2, 8*time.Second, 20000), // slow turn: steps must be raised so slices fit
	} {
		for i, l := range plan {
			if l.Dur <= 0 || l.Dur > maxStickHold {
				t.Fatalf("leg %d duration %v outside (0, %v]", i, l.Dur, maxStickHold)
			}
		}
	}
	// Raising steps must keep the circle total intact.
	var yaw time.Duration
	for _, l := range cameraScanPlan(2, 8*time.Second, 20000) {
		if l.Vec.RX != 0 {
			yaw += l.Dur
		}
	}
	if yaw != 8*time.Second {
		t.Fatalf("slow-turn circle total %v want 8s", yaw)
	}
}
