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
	{dirW, 2500 * time.Millisecond},
	{dirD, 1200 * time.Millisecond},
	{dirW, 1500 * time.Millisecond},
	{dirA, 2400 * time.Millisecond},
	{dirW, 1500 * time.Millisecond},
	{dirD, 1200 * time.Millisecond},
	{dirS, 2500 * time.Millisecond},
}

func searchSegment(i int) searchSeg {
	if i < 0 {
		i = 0
	}
	return searchPlan[i%len(searchPlan)]
}

// shouldRefreshHold decides whether to rewrite the stick file for an unchanged direction.
// The pump expires a hold after holdMs, so refresh at ~60% of it.
func shouldRefreshHold(sinceWrite, hold time.Duration) bool {
	return sinceWrite >= hold*6/10
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
