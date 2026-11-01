package combat

import (
	"testing"
	"time"
)

func TestTimerWatch_DisabledAndNeverSeen(t *testing.T) {
	if w := newTimerWatch("", time.Second); w != nil {
		t.Fatal("empty node should disable")
	}
	if w := newTimerWatch("N", 0); w != nil {
		t.Fatal("zero duration should disable")
	}
	var nilW *timerWatch
	if nilW.observe(time.Now(), false) {
		t.Fatal("nil watch must never report gone")
	}
	// Timer never seen (e.g. an instance without a countdown): never gone.
	w := newTimerWatch("N", 12*time.Second)
	t0 := time.Unix(1000, 0)
	for i := 0; i < 100; i++ {
		if w.observe(t0.Add(time.Duration(i)*time.Second), false) {
			t.Fatalf("gone reported without ever seeing the timer (i=%d)", i)
		}
	}
}

func TestTimerWatch_MidFightGapsDoNotEndFight(t *testing.T) {
	w := newTimerWatch("N", 12*time.Second)
	t0 := time.Unix(1000, 0)
	w.observe(t0, true)
	// 6.5s OCR gap observed in the real log must not trigger.
	if w.observe(t0.Add(6500*time.Millisecond), false) {
		t.Fatal("6.5s gap must not count as gone")
	}
	if w.observe(t0.Add(11900*time.Millisecond), false) {
		t.Fatal("11.9s < 12s must not count as gone")
	}
	// Timer reappears: clock restarts from the new sighting.
	w.observe(t0.Add(12*time.Second), true)
	if w.observe(t0.Add(23*time.Second), false) {
		t.Fatal("gap restarts after reappearing")
	}
}

func TestTimerWatch_GoneAfterSustainedAbsence(t *testing.T) {
	w := newTimerWatch("N", 12*time.Second)
	t0 := time.Unix(1000, 0)
	w.observe(t0, true)
	w.observe(t0.Add(2*time.Second), false)
	if !w.observe(t0.Add(12*time.Second), false) {
		t.Fatal("12s absence after a sighting should be gone")
	}
	// Stays gone on later scans.
	if !w.observe(t0.Add(20*time.Second), false) {
		t.Fatal("should remain gone")
	}
}
