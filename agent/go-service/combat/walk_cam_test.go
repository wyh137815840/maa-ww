package combat

import (
	"strings"
	"testing"
	"time"
)

func TestStickPayloadVecProtocol(t *testing.T) {
	// Left stick only stays on the 3-field protocol (older pumps).
	p, ms := stickPayloadVec(stickVec{LX: 1, LY: -2}, 700*time.Millisecond)
	if p != "1 -2 700\n" || ms != 700 {
		t.Fatalf("left-only: %q %d", p, ms)
	}
	// Camera input switches to 5 fields.
	p, ms = stickPayloadVec(stickVec{LY: -30000, RX: 20000}, 5*time.Second)
	if p != "0 -30000 20000 0 2000\n" || ms != 2000 {
		t.Fatalf("camera: %q %d", p, ms)
	}
}

func TestStickShellCmdLineAtomic(t *testing.T) {
	c := stickShellCmdLine("0 0 20000 0 300")
	if !strings.Contains(c, "maaww_stick.tmp && mv -f ") || !strings.HasPrefix(c, "echo 0 0 20000 0 300 > ") {
		t.Fatalf("got %q", c)
	}
}

func TestVecDirKeepsStrafeDirections(t *testing.T) {
	for _, d := range []walkDir{dirW, dirA, dirS, dirD} {
		if got := vecDir(dirVec(d)); got != d {
			t.Fatalf("vecDir(dirVec(%v))=%v", d, got)
		}
	}
	if vecDir(stickVec{}) != dirNone {
		t.Fatal("zero must be none")
	}
}

func TestCameraScanPlanShape(t *testing.T) {
	plan := cameraScanPlan(8, 3*time.Second, 20000)
	if len(plan) != 8*2+1 {
		t.Fatalf("len=%d", len(plan))
	}
	var yaw time.Duration
	for i := 0; i < 8; i++ {
		turn, look := plan[2*i], plan[2*i+1]
		if turn.Vec.RX != 20000 || turn.Vec.LX != 0 || turn.Vec.LY != 0 || turn.Look {
			t.Fatalf("turn leg %d: %+v", i, turn)
		}
		if !look.Look || !look.Vec.zero() || look.Dur != scanLookPause {
			t.Fatalf("look leg %d: %+v", i, look)
		}
		yaw += turn.Dur
	}
	if yaw != 3*time.Second {
		t.Fatalf("slices must sum to one full turn, got %v", yaw)
	}
	if last := plan[len(plan)-1]; last.Vec != dirVec(dirW) {
		t.Fatalf("circle must end with a forward leg: %+v", last)
	}
	// Defensive defaults.
	if p := cameraScanPlan(0, 0, 0); len(p) != 2*2+1 || p[0].Vec.RX != 20000 {
		t.Fatalf("defaults: %+v", p)
	}
}

func TestScanLegAtWraps(t *testing.T) {
	plan := cameraScanPlan(4, time.Second, 10000)
	if scanLegAt(plan, len(plan)) != plan[0] || scanLegAt(plan, -3) != plan[0] {
		t.Fatal("wrap/negative index wrong")
	}
	if l := scanLegAt(nil, 3); !l.Look || l.Dur <= 0 {
		t.Fatalf("empty plan fallback: %+v", l)
	}
}

func TestWalkSearchLegsMatchPlan(t *testing.T) {
	legs := walkSearchLegs()
	if len(legs) != len(searchPlan) {
		t.Fatal("length mismatch")
	}
	if legs[0].Vec != dirVec(dirW) || legs[0].Dur != searchPlan[0].Dur {
		t.Fatalf("first leg: %+v", legs[0])
	}
}

func TestYawStickX(t *testing.T) {
	if yawStickX(40, 60, 200, 8000, 22000) != 0 {
		t.Fatal("inside dead zone must be 0")
	}
	if got := yawStickX(61, 60, 200, 8000, 22000); got <= 8000 || got > 8100 {
		t.Fatalf("just outside dead zone should be ~min: %d", got)
	}
	if yawStickX(900, 60, 200, 8000, 22000) != 22000 {
		t.Fatal("far error must saturate at max")
	}
	if yawStickX(-900, 60, 200, 8000, 22000) != -22000 {
		t.Fatal("negative error turns left")
	}
	// monotonic ramp
	prev := 0
	for dx := 61; dx <= 400; dx += 20 {
		v := yawStickX(dx, 60, 200, 8000, 22000)
		if v < prev {
			t.Fatalf("not monotonic at %d: %d<%d", dx, v, prev)
		}
		prev = v
	}
}

func aim(cx, cy int) (stickVec, bool) {
	return aimYaw(aimInput{
		BoxCX: cx, BoxCY: cy, YOffset: 36,
		DeadPx: 60, WidePx: 260, YawMin: 8000, YawMax: 22000,
	})
}

func TestAimYawTurnsAndWalksTogether(t *testing.T) {
	// Marker right of center, within wide band: curve right while walking forward.
	v, aligned := aim(800, 300)
	if v.RX <= 0 || v.LY >= 0 || aligned {
		t.Fatalf("curve right: %+v aligned=%v", v, aligned)
	}
	// Aligned: straight forward, no yaw.
	v, aligned = aim(650, 300)
	if v.RX != 0 || v.LY >= 0 || !aligned {
		t.Fatalf("aligned forward: %+v aligned=%v", v, aligned)
	}
}

func TestAimYawRotatesInPlaceWhenFarOffAxis(t *testing.T) {
	v, _ := aim(1200, 300)
	if v.LY != 0 || v.RX <= 0 {
		t.Fatalf("far right: rotate only: %+v", v)
	}
	v, _ = aim(80, 300)
	if v.LY != 0 || v.RX >= 0 {
		t.Fatalf("far left: rotate only: %+v", v)
	}
}

func TestAimYawVerticalBands(t *testing.T) {
	// cy-36: 300 → forward; 480 (→444) dead band; 600 (→564) back.
	if v, _ := aim(640, 300); v.LY >= 0 {
		t.Fatalf("high marker should go forward: %+v", v)
	}
	if v, _ := aim(640, 480); v.LY != 0 {
		t.Fatalf("dead band should hold: %+v", v)
	}
	if v, _ := aim(640, 600); v.LY <= 0 {
		t.Fatalf("overshot should back off: %+v", v)
	}
}

func TestParseWalkTreasureParamCamera(t *testing.T) {
	p := parseWalkTreasureParam("")
	if p.ScanMode != "camera" || p.AimMode != "strafe" || p.YawFullMs != 3000 || p.ScanSteps != 8 {
		t.Fatalf("defaults: %+v", p)
	}
	p = parseWalkTreasureParam(`{"scan_mode":"walk","aim_mode":"yaw","yaw_full_ms":2400,"scan_steps":6}`)
	if p.ScanMode != "walk" || p.AimMode != "yaw" || p.YawFullMs != 2400 || p.ScanSteps != 6 {
		t.Fatalf("override: %+v", p)
	}
	// Invalid enum values are ignored.
	p = parseWalkTreasureParam(`{"scan_mode":"spin","aim_mode":"x"}`)
	if p.ScanMode != "camera" || p.AimMode != "strafe" {
		t.Fatalf("invalid enums must fall back: %+v", p)
	}
}
