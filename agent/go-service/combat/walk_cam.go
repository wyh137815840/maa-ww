package combat

import "time"

// Camera (right stick) helpers for WalkToTacetTreasure. Pure and unit-tested.
//
// GamepadForwarder maps the right stick to the Xbox node's ABS_Z (yaw, +right) and
// ABS_RZ (pitch). Yaw speed is proportional to deflection; `yaw_full_ms` is the time one full
// 360° turn takes at `yaw_deflect` and must be calibrated on the device.

// stickVec is left stick (move) + right stick (camera), raw Xbox ABS values (±32767).
type stickVec struct {
	LX, LY, RX, RY int
}

func (v stickVec) zero() bool { return v == stickVec{} }

func (v stickVec) hasCamera() bool { return v.RX != 0 || v.RY != 0 }

// dirVec converts a WASD-style direction into a left-stick vector.
func dirVec(d walkDir) stickVec {
	x, y := dirStick(d)
	return stickVec{LX: x, LY: y}
}

// scanLeg is one leg of the no-marker search: hold Vec for Dur. Look legs are stationary
// pauses so the next frame sees a settled camera before we decide to keep turning.
type scanLeg struct {
	Vec  stickVec
	Dur  time.Duration
	Look bool
}

// walkSearchLegs adapts the legacy walk-only search path.
func walkSearchLegs() []scanLeg {
	legs := make([]scanLeg, 0, len(searchPlan))
	for _, s := range searchPlan {
		legs = append(legs, scanLeg{Vec: dirVec(s.Dir), Dur: s.Dur})
	}
	return legs
}

const (
	scanLookPause = 350 * time.Millisecond
	scanWalkLeg   = 2000 * time.Millisecond
)

// cameraScanPlan: `steps` × (yaw slice, look pause) = one full circle, then walk forward a
// little and repeat. The marker is only drawn when on screen, so a full circle finds it if
// the chest is within draw range.
func cameraScanPlan(steps int, yawFull time.Duration, deflect int) []scanLeg {
	if steps < 2 {
		steps = 2
	}
	if deflect <= 0 {
		deflect = 20000
	}
	if yawFull <= 0 {
		yawFull = 3000 * time.Millisecond
	}
	// One slice must fit a single stick command (pump clamps holds to maxStickHold).
	if min := int((yawFull + maxStickHold - 1) / maxStickHold); steps < min {
		steps = min
	}
	slice := yawFull / time.Duration(steps)
	legs := make([]scanLeg, 0, steps*2+1)
	for i := 0; i < steps; i++ {
		legs = append(legs,
			scanLeg{Vec: stickVec{RX: deflect}, Dur: slice},
			scanLeg{Vec: stickVec{}, Dur: scanLookPause, Look: true},
		)
	}
	legs = append(legs, scanLeg{Vec: dirVec(dirW), Dur: scanWalkLeg})
	return legs
}

// scanSettle is how long after a Look leg starts before a frame counts as a settled
// observation (stick neutral written + camera stopped + one capture latency).
const scanSettle = 150 * time.Millisecond

type scanAction struct {
	Send bool
	Vec  stickVec
	Hold time.Duration
}

// scanSeq runs a scan plan with timing that does NOT depend on recognition cost:
//   - a motion leg is sent ONCE with hold == leg.Dur; the pump self-expires it, so a slow
//     frame cannot make the turn longer than planned (slices still sum to one circle);
//   - a Look leg sends neutral once and only completes after its duration elapsed AND at
//     least one frame captured after the settle delay was processed without a marker.
type scanSeq struct {
	plan     []scanLeg
	idx      int
	legStart time.Time
	started  bool
	sent     bool
	observed bool
}

func newScanSeq(plan []scanLeg) *scanSeq { return &scanSeq{plan: plan} }

func (s *scanSeq) reset() {
	s.idx, s.started, s.sent, s.observed = 0, false, false, false
	s.legStart = time.Time{}
}

// step is called once per frame in which no marker was found. `now` is after recognition,
// `frameStart` is when this frame's capture began.
func (s *scanSeq) step(now, frameStart time.Time) scanAction {
	if !s.started {
		s.started = true
		s.legStart = now
	}
	leg := scanLegAt(s.plan, s.idx)

	if leg.Look && !s.observed && !frameStart.Before(s.legStart.Add(scanSettle)) && s.sent {
		s.observed = true
	}
	if now.Sub(s.legStart) >= leg.Dur && (!leg.Look || s.observed) {
		s.idx++
		s.legStart = now
		s.sent, s.observed = false, false
		leg = scanLegAt(s.plan, s.idx)
	}
	if !s.sent {
		s.sent = true
		return scanAction{Send: true, Vec: leg.Vec, Hold: leg.Dur}
	}
	return scanAction{}
}

func scanLegAt(plan []scanLeg, i int) scanLeg {
	if len(plan) == 0 {
		return scanLeg{Dur: time.Second, Look: true}
	}
	if i < 0 {
		i = 0
	}
	return plan[i%len(plan)]
}

// yawStickX maps horizontal pixel error to a right-stick X value: dead zone, then a linear
// ramp from minDef to maxDef. dx>0 (marker right of center) turns right.
func yawStickX(dx, deadPx, rampPx, minDef, maxDef int) int {
	a := absInt(dx)
	if a <= deadPx {
		return 0
	}
	if rampPx <= 0 {
		rampPx = 1
	}
	frac := float64(a-deadPx) / float64(rampPx)
	if frac > 1 {
		frac = 1
	}
	v := minDef + int(frac*float64(maxDef-minDef))
	if dx < 0 {
		return -v
	}
	return v
}

const (
	aimFwdY  = 432 // ok-ww 0.6*720: forward while marker is above this
	aimBackY = 500 // back off only when clearly overshot
)

type aimInput struct {
	BoxCX, BoxCY int
	YOffset      int
	DeadPx       int // yaw dead zone (px)
	WidePx       int // beyond this, rotate in place (no forward)
	YawMin       int
	YawMax       int
}

// aimYaw steers by turning the camera instead of strafing: yaw toward the marker and walk
// forward once roughly aligned (ok-ww vertical band logic decides forward/back). Returns the
// stick vector and whether the marker is within the dead zone.
func aimYaw(in aimInput) (stickVec, bool) {
	dx := in.BoxCX - 640
	cy := in.BoxCY - in.YOffset
	if cy < 0 {
		cy = 0
	}
	rx := yawStickX(dx, in.DeadPx, in.WidePx-in.DeadPx, in.YawMin, in.YawMax)
	aligned := absInt(dx) <= in.DeadPx

	var ly int
	switch {
	case absInt(dx) > in.WidePx:
		ly = 0 // far off-axis: rotate first
	case cy > aimBackY: // marker low on screen → overshot/very close
		ly = 25000 // back
	case cy > aimFwdY: // dead band: hold position (avoids W/S chatter)
		ly = 0
	default:
		ly = -30000 // forward
	}
	return stickVec{LY: ly, RX: rx}, aligned
}
