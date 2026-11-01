package account

import "testing"

func TestParsePhones(t *testing.T) {
	accs, bad, dup := ParsePhones("13800001234，139-0000-5678;\n1234\nabc, 99")
	if len(accs) != 2 || accs[0].LastFour != "1234" || accs[1].LastFour != "5678" {
		t.Fatalf("accounts = %+v", accs)
	}
	// "1234" duplicates the first account's last four with different digits.
	if len(dup) != 1 || dup[0] != "1234" {
		t.Fatalf("dup = %v", dup)
	}
	if len(bad) != 2 {
		t.Fatalf("bad = %v", bad)
	}
}

func TestParsePhonesEmpty(t *testing.T) {
	accs, bad, dup := ParsePhones("  \n ")
	if len(accs)+len(bad)+len(dup) != 0 {
		t.Fatalf("expected empty, got %v %v %v", accs, bad, dup)
	}
}

func TestPickOverride(t *testing.T) {
	ov := pickOverride("0075", "AccountPickRow", "AccountCurrentIsTarget", "")
	if len(ov) != 2 {
		t.Fatalf("override = %v", ov)
	}
	exp := ov["AccountPickRow"].(map[string]any)["expected"].([]string)
	if len(exp) != 1 || exp[0] != "0075" {
		t.Fatalf("expected = %v", exp)
	}
}

func TestParseLoopParamKeepsDefaultTasks(t *testing.T) {
	p := parseLoopParam(`{"phones":"0075"}`)
	if p.Phones != "0075" || len(p.Tasks) != len(defaultTasks) {
		t.Fatalf("got %+v", p)
	}
}
