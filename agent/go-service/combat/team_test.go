package combat

import (
	"image"
	"image/draw"
	"image/png"
	"os"
	"testing"
)

// loadHUDStrip pastes a right-edge strip (x 1080.., y 80..) back onto a 1280x720 canvas.
func loadHUDStrip(t *testing.T, name string) image.Image {
	t.Helper()
	f, err := os.Open("testdata/" + name)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	strip, err := png.Decode(f)
	if err != nil {
		t.Fatal(err)
	}
	canvas := image.NewRGBA(image.Rect(0, 0, 1280, 720))
	draw.Draw(canvas, image.Rect(1080, 80, 1080+strip.Bounds().Dx(), 80+strip.Bounds().Dy()), strip, strip.Bounds().Min, draw.Src)
	return canvas
}

func TestReadTeamAllAlive(t *testing.T) {
	st := readTeam(loadHUDStrip(t, "hud_alive.png"), nil)
	want := [3]string{"hiyuki", "lucilla", "suisui"}
	for i, w := range want {
		if st.Slots[i].Name != w {
			t.Errorf("slot %d name=%q want %q (score %.2f)", i, st.Slots[i].Name, w, st.Slots[i].Score)
		}
		if st.Slots[i].Dead {
			t.Errorf("slot %d should be alive (bar px %d)", i, st.Slots[i].BarPx)
		}
	}
	if st.Current != 0 {
		t.Errorf("current=%d want 0 (no badge)", st.Current)
	}
}

func TestReadTeamOneDead(t *testing.T) {
	alive := readTeam(loadHUDStrip(t, "hud_alive.png"), nil)
	st := readTeam(loadHUDStrip(t, "hud_dead.png"), &alive)
	if !st.Slots[1].Dead {
		t.Errorf("lucilla (slot 1) should be dead, bar px %d", st.Slots[1].BarPx)
	}
	if st.Slots[0].Dead || st.Slots[2].Dead {
		t.Errorf("slots 0/2 should be alive: %+v", st.Slots)
	}
	if st.Slots[1].Name != "lucilla" || st.Slots[2].Name != "suisui" {
		t.Errorf("names: %+v", st.Slots)
	}
	if st.Slots[0].Name != "hiyuki" {
		t.Errorf("hiyuki must survive via prev roster: %+v", st.Slots[0])
	}
	if st.Current != 0 {
		t.Errorf("current=%d want 0", st.Current)
	}
	if got := st.nextAlive(0); got != 2 {
		t.Errorf("nextAlive(0)=%d want 2 (skip dead lucilla)", got)
	}
	if got := st.nextAlive(2); got != 0 {
		t.Errorf("nextAlive(2)=%d want 0", got)
	}
	if st.aliveCount() != 2 {
		t.Errorf("aliveCount=%d", st.aliveCount())
	}
}

func TestReadTeamDimmedHUDKeepsPrevious(t *testing.T) {
	alive := readTeam(loadHUDStrip(t, "hud_alive.png"), nil)
	blank := image.NewRGBA(image.Rect(0, 0, 1280, 720))
	st := readTeam(blank, &alive)
	if st.aliveCount() != 3 || st.Slots[1].Name != "lucilla" {
		t.Errorf("dimmed HUD must keep previous roster, got %+v", st.Slots)
	}
	if st.Current != -1 {
		t.Errorf("current must be unknown, got %d", st.Current)
	}
	fresh := readTeam(blank, nil)
	if fresh.aliveCount() != 3 {
		t.Errorf("unreadable HUD without prev must not report deaths: %+v", fresh.Slots)
	}
	if got := fresh.nextAlive(0); got != 1 {
		t.Errorf("unreadable HUD nextAlive(0)=%d want cyclic 1", got)
	}
}
