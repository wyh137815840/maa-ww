// Package account drives multi-account runs: for every configured phone number it switches the
// Kuro login to that account (pipeline AccountSwitch*), then runs every enabled task once.
package account

import (
	"regexp"
	"strings"
)

var phoneSplit = regexp.MustCompile(`[,，;；、\s]+`)
var onlyDigits = regexp.MustCompile(`\D+`)

// Account is one configured login. The Kuro login sheet only shows a masked phone
// (138****1234), so the last four digits are what the pipeline matches on.
type Account struct {
	Raw      string // as typed (digits only)
	LastFour string
}

// ParsePhones turns the free-form input field into a de-duplicated account list.
//
// Accepted separators: comma / Chinese comma / semicolon / 、 / whitespace / newline.
// Each item may be a full phone number or just the last four digits. Items with fewer than
// four digits are returned in bad. Two items with the same last four collapse to the first,
// since the login list cannot tell them apart; the dropped one is reported in dup.
func ParsePhones(raw string) (accounts []Account, bad, dup []string) {
	seen := map[string]string{}
	for _, tok := range phoneSplit.Split(strings.TrimSpace(raw), -1) {
		if tok == "" {
			continue
		}
		digits := onlyDigits.ReplaceAllString(tok, "")
		if len(digits) < 4 {
			bad = append(bad, tok)
			continue
		}
		last := digits[len(digits)-4:]
		if first, ok := seen[last]; ok {
			if first != digits {
				dup = append(dup, tok)
			}
			continue
		}
		seen[last] = digits
		accounts = append(accounts, Account{Raw: digits, LastFour: last})
	}
	return accounts, bad, dup
}
