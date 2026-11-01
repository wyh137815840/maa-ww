package combat

import "time"

// timerWatch ends a timed challenge when its on-screen countdown disappears.
//
// Why: CombatHasTarget is a weak template (scores 0.50–0.65 whether or not an enemy is
// locked), so "still in combat" can stay true forever after the last enemy dies, and the
// 「挑战达成」banner is easy to miss between scans. The Tacet countdown (e.g. 04:28:55,
// top-centre) is shown for the whole fight and vanishes the moment it is cleared (20261101
// 18:36:00 run: timer gone, loop kept swinging for 70s until stopped by hand).
//
// OCR drops the timer for a few seconds mid-fight (observed gaps up to 6.5s), and cutscenes
// hide the HUD, so "gone" requires the timer to have been seen first and then be absent for
// at least goneAfter (default 12s).
type timerWatch struct {
	node      string
	goneAfter time.Duration
	seen      bool
	lastSeen  time.Time
}

func newTimerWatch(node string, goneAfter time.Duration) *timerWatch {
	if node == "" || goneAfter <= 0 {
		return nil
	}
	return &timerWatch{node: node, goneAfter: goneAfter}
}

// observe records one scan and reports whether the countdown has been gone long enough.
func (w *timerWatch) observe(now time.Time, present bool) bool {
	if w == nil {
		return false
	}
	if present {
		w.seen = true
		w.lastSeen = now
		return false
	}
	return w.seen && now.Sub(w.lastSeen) >= w.goneAfter
}
