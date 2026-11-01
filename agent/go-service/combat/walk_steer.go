package combat

import "time"

// Pure helpers for WalkToTacetTreasure (ok-ww walk_to_box steering + search plan).
// Kept free of maa types so they can be unit-tested.

type steerInput struct {
	BoxCX, BoxCY int // marker box center in 1280×720
	LastDir      walkDir
	Centered     bool
	XThreshold   int // px, ok-ww x_threshold (~0.07*1280)
	YOffset      int // px, aim above the marker
}

// steerDecision mirrors ok-ww do_walk_to_box: strafe a/d until centered, then w/s by vertical band.
func steerDecision(in steerInput) (next walkDir, centered bool) {
	cy := in.BoxCY - in.YOffset
	if cy < 0 {
		cy = 0
	}
	dx := in.BoxCX - 640

	thr := in.XThreshold
	if in.LastDir == dirNone {
		thr = 50 // ok-ww 0.04*1280 before any direction
	}
	centered = in.Centered || absInt(dx) <= thr
	if !centered {
		if dx > 0 {
			return dirD, false
		}
		return dirA, false
	}

	centerY := 360
	switch in.LastDir {
	case dirS:
		centerY = int(0.45 * 720)
	case dirW:
		centerY = int(0.6 * 720)
	}
	if cy > centerY {
		return dirS, true
	}
	return dirW, true
}

// searchSeg is one leg of the no-marker search path. Each leg is held continuously
// (no per-frame W/S flip-flop, which nets ~0 displacement).
type searchSeg struct {
	Dir walkDir
	Dur time.Duration
}

var searchPlan = []searchSeg{
	// Every leg <= maxStickHold so one exact-length command covers it.
	{dirW, 2000 * time.Millisecond},
	{dirD, 1200 * time.Millisecond},
	{dirW, 1500 * time.Millisecond},
	{dirA, 2000 * time.Millisecond},
	{dirW, 1500 * time.Millisecond},
	{dirD, 1200 * time.Millisecond},
	{dirS, 2000 * time.Millisecond},
}

func searchSegment(i int) searchSeg {
	if i < 0 {
		i = 0
	}
	return searchPlan[i%len(searchPlan)]
}

const (
	minStickHold = 50 * time.Millisecond
	maxStickHold = 2000 * time.Millisecond
)

// clampHold applies the same limits the pump enforces, so refresh decisions use the
// duration that was actually sent.
func clampHold(hold time.Duration) time.Duration {
	if hold < minStickHold {
		return minStickHold
	}
	if hold > maxStickHold {
		return maxStickHold
	}
	return hold
}

// needsRewrite decides whether to rewrite the stick file for an unchanged direction.
// `remaining` is the time left on the previously sent (clamped) hold, i.e. holdUntil-now;
// `hold` is the clamped duration being requested. Rewrite when the live command would expire
// before ~40% of the new request has elapsed. Judging by the old deadline (not the new
// duration) is what lets a 700ms steer hold hand over to a long same-direction search leg.
func needsRewrite(remaining, hold time.Duration) bool {
	return remaining < hold*4/10
}

// frameStats accumulates per-frame cost, split by whether OCR nodes ran that frame.
type frameStats struct {
	plainSum, ocrSum time.Duration
	plainN, ocrN     int
}

func (s *frameStats) add(ocr bool, d time.Duration) {
	if ocr {
		s.ocrSum += d
		s.ocrN++
		return
	}
	s.plainSum += d
	s.plainN++
}

func (s *frameStats) avg(ocr bool) time.Duration {
	if ocr {
		if s.ocrN == 0 {
			return 0
		}
		return s.ocrSum / time.Duration(s.ocrN)
	}
	if s.plainN == 0 {
		return 0
	}
	return s.plainSum / time.Duration(s.plainN)
}

// markerFresh reports whether a remembered marker is still trustworthy (ok-ww last_target
// has no expiry, but at pad frame rates a stale box keeps steering after we walk past it).
func markerFresh(sinceSeen, ttl time.Duration) bool {
	return sinceSeen <= ttl
}

// cadence returns true on frames where the expensive (OCR) checks should run.
func cadence(frame, every int) bool {
	if every <= 1 {
		return true
	}
	return frame == 1 || frame%every == 0
}
