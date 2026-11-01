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

// Perform runs one field rotation then returns the next slot index to swap to.
// Sequence mirrors ok-ww BaseChar.do_perform:
//
//	echo → liberation → resonance → attacks → heavy → interact → swap
func (c *BaseChar) Perform(waitHUD func(timeout time.Duration) bool) int {
	if c == nil || c.pad == nil {
		return 0
	}

	log.Debug().Int("slot", c.slot).Msg("BaseChar.Perform")

	// Intro filler: a couple of attacks while landing.
	for i := 0; i < 2; i++ {
		c.pad.Attack()
		time.Sleep(80 * time.Millisecond)
	}

	c.pad.Echo()
	time.Sleep(120 * time.Millisecond)

	c.pad.Liberation()
	// Liberation cutscene hides HUD; wait it out before continuing.
	if waitHUD != nil {
		waitHUD(5 * time.Second)
	} else {
		time.Sleep(800 * time.Millisecond)
	}

	c.pad.Resonance()
	time.Sleep(150 * time.Millisecond)

	n := c.attackCount
	if n < 1 {
		n = 3
	}
	for i := 0; i < n; i++ {
		c.pad.Attack()
		time.Sleep(90 * time.Millisecond)
	}

	c.pad.Heavy(c.heavyHold)
	time.Sleep(80 * time.Millisecond)

	// Grapple / break QTE safety tap.
	c.pad.Interact()
	time.Sleep(60 * time.Millisecond)

	next := (c.slot + 1) % 3
	c.pad.SwapSlot(next)
	time.Sleep(200 * time.Millisecond)
	return next
}
