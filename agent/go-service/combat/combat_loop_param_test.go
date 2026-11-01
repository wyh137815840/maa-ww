package combat

import "testing"

func TestParseCombatLoopParam_TimerDefaults(t *testing.T) {
	p := parseCombatLoopParam("")
	if p.TimerNode != "TacetTimerOCR" || p.TimerGoneMs != 12000 {
		t.Fatalf("defaults: %q %d", p.TimerNode, p.TimerGoneMs)
	}
	// Pipeline passes params without the timer keys: defaults must survive.
	p = parseCombatLoopParam(`{"exit_nodes":["A"],"max_duration_ms":1000}`)
	if p.TimerNode != "TacetTimerOCR" || p.TimerGoneMs != 12000 {
		t.Fatalf("partial override lost timer defaults: %q %d", p.TimerNode, p.TimerGoneMs)
	}
}

func TestParseCombatLoopParam_TimerOverrideAndDisable(t *testing.T) {
	p := parseCombatLoopParam(`{"timer_node":"X","timer_gone_ms":5000}`)
	if p.TimerNode != "X" || p.TimerGoneMs != 5000 {
		t.Fatalf("override: %q %d", p.TimerNode, p.TimerGoneMs)
	}
	// Explicit empty node disables the watch (other instances without a countdown).
	p = parseCombatLoopParam(`{"timer_node":""}`)
	if newTimerWatch(p.TimerNode, 12000) != nil {
		t.Fatal("empty timer_node must disable the watch")
	}
	p = parseCombatLoopParam(`{"timer_gone_ms":0}`)
	if newTimerWatch(p.TimerNode, 0) != nil && p.TimerGoneMs != 0 {
		t.Fatal("zero timer_gone_ms must disable the watch")
	}
	if p.TimerGoneMs != 0 {
		t.Fatalf("timer_gone_ms=0 not honoured: %d", p.TimerGoneMs)
	}
}
