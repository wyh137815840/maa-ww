package combat

import (
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// Android KEYCODE_* for Xbox-mapped Wuthering Waves controller mode.
// See docs/zh_cn/ww-input-map.json.
const (
	KeyAttack      int32 = 99  // BUTTON_X
	KeyResonance   int32 = 100 // BUTTON_Y
	KeyLiberation  int32 = 105 // BUTTON_R2 (RT)
	KeyEcho        int32 = 104 // BUTTON_L2 (LT)
	KeyDodge       int32 = 103 // BUTTON_R1 (RB)
	KeyJump        int32 = 96  // BUTTON_A
	KeyInteract    int32 = 97  // BUTTON_B
	KeySwap1       int32 = 19  // DPAD_UP
	KeySwap2       int32 = 22  // DPAD_RIGHT
	KeySwap3       int32 = 20  // DPAD_DOWN
	KeyLock        int32 = 107 // BUTTON_THUMBR (R3)
	KeyModifierLB int32 = 102 // BUTTON_L1 (LB)
)

// Pad wraps controller key injection for gamepad combat.
type Pad struct {
	ctrl *maa.Controller
}

func NewPad(ctrl *maa.Controller) *Pad {
	return &Pad{ctrl: ctrl}
}

func (p *Pad) Click(key int32) {
	if p == nil || p.ctrl == nil {
		return
	}
	p.ctrl.PostClickKey(key).Wait()
}

func (p *Pad) Hold(key int32, duration time.Duration) {
	if p == nil || p.ctrl == nil {
		return
	}
	p.ctrl.PostKeyDown(key).Wait()
	time.Sleep(duration)
	p.ctrl.PostKeyUp(key).Wait()
}

func (p *Pad) Attack()           { p.Click(KeyAttack) }
func (p *Pad) Resonance()        { p.Click(KeyResonance) }
func (p *Pad) Liberation()       { p.Click(KeyLiberation) }
func (p *Pad) Echo()             { p.Click(KeyEcho) }
func (p *Pad) Dodge()            { p.Click(KeyDodge) }
func (p *Pad) Interact()         { p.Click(KeyInteract) }
func (p *Pad) Lock()             { p.Click(KeyLock) }
func (p *Pad) Swap1()            { p.Click(KeySwap1) }
func (p *Pad) Swap2()            { p.Click(KeySwap2) }
func (p *Pad) Swap3()            { p.Click(KeySwap3) }
func (p *Pad) Heavy(d time.Duration) {
	if d <= 0 {
		d = 450 * time.Millisecond
	}
	p.Hold(KeyAttack, d)
}

// SwapSlot presses D-Pad for slot 0/1/2.
func (p *Pad) SwapSlot(slot int) {
	switch slot % 3 {
	case 0:
		p.Swap1()
	case 1:
		p.Swap2()
	default:
		p.Swap3()
	}
}
