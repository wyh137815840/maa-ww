package combat

import (
	"testing"
	"time"
)

func TestStickPayloadClamp(t *testing.T) {
	p, ms := stickPayload(1, -2, 10*time.Millisecond)
	if ms != 50 || p != "1 -2 50\n" {
		t.Fatalf("got %q %d", p, ms)
	}
	_, ms = stickPayload(0, 0, 9*time.Second)
	if ms != 2000 {
		t.Fatalf("ms=%d", ms)
	}
}

func TestStickShellCmdAtomic(t *testing.T) {
	got := stickShellCmd(0, -30000, 600)
	want := "echo 0 -30000 600 > /data/local/tmp/maaww_stick.tmp && mv -f /data/local/tmp/maaww_stick.tmp /data/local/tmp/maaww_stick"
	if got != want {
		t.Fatalf("got %q", got)
	}
}
