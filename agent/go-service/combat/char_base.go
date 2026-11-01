package combat

import (
	"time"

	"github.com/rs/zerolog/log"
)

// BaseChar is a timing-only port of ok-ww BaseChar.do_perform under gamepad mode.
// ok-ww default rotation: wait_intro → echo → liberation → resonance else heavy → switch.
// Continues normal attack during short waits (ok-ww continues_normal_attack), instead of
// long idle sleeps that make combat feel "hit once then stall".
type BaseChar struct {
	pad  *Pad
	slot int
	// pickNext chooses the slot to swap to (skips dead teammates). nil = cyclic.
	pickNext func(cur int) int
}

func NewBaseChar(pad *Pad, slot int) *BaseChar {
	return &BaseChar{pad: pad, slot: slot}
}

// Perform runs one field rotation then returns (nextSlot, stoppedEarly).
// stop is checked sparingly (ok-ww checks combat between skills via next_frame,
// not a full settle-node scan after every key).
func (c *BaseChar) Perform(stop func() bool) (int, bool) {
	if c == nil || c.pad == nil {
		return 0, false
	}

	log.Debug().Int("slot", c.slot).Msg("BaseChar.Perform")
	aborted := false
	check := func() bool {
		if stop != nil && stop() {
			aborted = true
			return true
		}
		return false
	}

	// Intro settle: keep attacking (ok-ww wait_intro / continues_normal_attack).
	c.continuesAttack(400*time.Millisecond, 90*time.Millisecond, check)
	if aborted {
		return c.slot, true
	}

	c.pad.Echo()
	c.continuesAttack(180*time.Millisecond, 80*time.Millisecond, check)
	if aborted {
		return c.slot, true
	}

	c.pad.Liberation()
	// Liberation cutscene: keep clicking instead of blank waitHUD(5s).
	c.continuesAttack(900*time.Millisecond, 100*time.Millisecond, check)
	if aborted {
		return c.slot, true
	}

	c.pad.Resonance()
	c.continuesAttack(200*time.Millisecond, 80*time.Millisecond, check)
	if aborted {
		return c.slot, true
	}

	// Forte-ish heavy (ok-ww heavy_click_forte when resonance not available — we always tap once).
	c.pad.Heavy(380 * time.Millisecond)
	c.continuesAttack(120*time.Millisecond, 80*time.Millisecond, check)
	if aborted {
		return c.slot, true
	}

	next := (c.slot + 1) % 3
	if c.pickNext != nil {
		next = c.pickNext(c.slot)
	}
	if next == c.slot {
		// Nobody else alive: keep fighting with the current character.
		c.continuesAttack(220*time.Millisecond, 90*time.Millisecond, check)
		return c.slot, aborted
	}
	c.pad.SwapSlot(next)
	// Brief swap recovery with attacks (ok-ww may add continues_normal_attack when swap too fast).
	c.continuesAttack(220*time.Millisecond, 90*time.Millisecond, check)
	return next, aborted
}

func (c *BaseChar) continuesAttack(duration, interval time.Duration, stop func() bool) {
	deadline := time.Now().Add(duration)
	for time.Now().Before(deadline) {
		if stop != nil && stop() {
			return
		}
		c.pad.Attack()
		time.Sleep(interval)
	}
}
