package combat

import "time"

// exitScanDecision decides whether CombatLoop should run a full settle-node scan.
// Round triggers are one-shot: the same rounds value will not re-fire until lastExitRound updates.
func exitScanDecision(rounds, everyN, lastExitRound int, sinceLast time.Duration, force bool) (scan, consumeRound bool) {
	if force {
		return true, false
	}
	if everyN > 0 && rounds > 0 && rounds%everyN == 0 && rounds != lastExitRound {
		return true, true
	}
	if sinceLast > 2*time.Second {
		return true, false
	}
	return false, false
}
