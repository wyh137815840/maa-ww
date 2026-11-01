package combat

import (
	"time"

	"github.com/rs/zerolog/log"
)

// BaseChar is a timing-only port of ok-ww BaseChar.do_perform under gamepad mode.
// No CD OCR / CharFactory — fire skills on cadence then swap.
type BaseChar struct {
	pad         *Pad
	slot        int
	attackCount int
	heavyHold   time.Duration
}

func NewBaseChar(pad *Pad, slot int) *BaseChar {
	return &BaseChar{
		pad:         pad,
		slot:        slot,
		attackCount: 4,
		heavyHold:   450 * time.Millisecond,
	}
}

// Perform runs one field rotation then returns (nextSlot, stoppedEarly).
// stop is checked between skills so settle/claim can abort mid-rotation.
func (c *BaseChar) Perform(waitHUD func(timeout time.Duration) bool, stop func() bool) (int, bool) {
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

	for i := 0; i < 2; i++ {
		if check() {
			return c.slot, true
		}
		c.pad.Attack()
		time.Sleep(80 * time.Millisecond)
	}

	if check() {
		return c.slot, true
	}
	c.pad.Echo()
	time.Sleep(120 * time.Millisecond)

	if check() {
		return c.slot, true
	}
	c.pad.Liberation()
	if waitHUD != nil {
		waitHUD(5 * time.Second)
	} else {
		time.Sleep(800 * time.Millisecond)
	}
	if check() {
		return c.slot, true
	}

	c.pad.Resonance()
	time.Sleep(150 * time.Millisecond)

	n := c.attackCount
	if n < 1 {
		n = 3
	}
	for i := 0; i < n; i++ {
		if check() {
			return c.slot, true
		}
		c.pad.Attack()
		time.Sleep(90 * time.Millisecond)
	}

	if check() {
		return c.slot, true
	}
	c.pad.Heavy(c.heavyHold)
	time.Sleep(80 * time.Millisecond)

	if check() {
		return c.slot, true
	}
	c.pad.Interact()
	time.Sleep(60 * time.Millisecond)

	if check() {
		return c.slot, true
	}
	next := (c.slot + 1) % 3
	c.pad.SwapSlot(next)
	time.Sleep(200 * time.Millisecond)
	return next, aborted
}
