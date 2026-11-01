package combat

import "testing"

func TestParseNestApproachParam(t *testing.T) {
	p := parseNestApproachParam("")
	if len(p.GateNodes) != 1 || p.GateNodes[0] != "NestInCombat" || p.TimeoutMs != 90000 || p.Forward != 30000 {
		t.Fatalf("defaults wrong: %+v", p)
	}
	p = parseNestApproachParam(`{"gate_nodes":["A","B"],"timeout_ms":5000,"forward":99999}`)
	if len(p.GateNodes) != 2 || p.TimeoutMs != 5000 {
		t.Fatalf("override wrong: %+v", p)
	}
	if p.Forward != 32767 {
		t.Fatalf("forward must clamp to 32767, got %d", p.Forward)
	}
	p = parseNestApproachParam("{bad json")
	if p.TimeoutMs != 90000 {
		t.Fatalf("bad json must fall back to defaults: %+v", p)
	}
}
