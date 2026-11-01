package combat

import (
	"image"
	"time"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
)

// Pipeline node names for in-combat checks (defined in Tacet.json; not entry next).
const (
	NodeCombatHasTarget = "CombatHasTarget"
	NodeCombatEnemyHP   = "CombatEnemyHP"
)

// inCombat reports active combat (ok-ww style), with tighter rules than raw red pixels:
// has_target alone is enough; red HP only counts while quest bar still visible
// (avoids false positives on settle UI red accents after combat ends).
func inCombat(ctx *maa.Context, img image.Image) bool {
	if img == nil {
		return false
	}
	if nodeHit(ctx, img, NodeCombatHasTarget) {
		return true
	}
	quest := nodeHit(ctx, img, "InTacetCombat") || nodeHit(ctx, img, "InTacetCombatTpl")
	if quest && nodeHit(ctx, img, NodeCombatEnemyHP) {
		return true
	}
	return false
}

func nodeHit(ctx *maa.Context, img image.Image, name string) bool {
	if ctx == nil || name == "" {
		return false
	}
	detail, err := ctx.RunRecognition(name, img)
	if err != nil || detail == nil {
		return false
	}
	return detail.Hit
}

// ensureInCombat tries Lock (R3) until in-combat or timeout. Returns false if still out.
func ensureInCombat(ctx *maa.Context, ctrl *maa.Controller, pad *Pad, timeout time.Duration) bool {
	if ctrl == nil || pad == nil {
		return false
	}
	deadline := time.Now().Add(timeout)
	attempt := 0
	for time.Now().Before(deadline) {
		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err == nil && img != nil && inCombat(ctx, img) {
			if attempt > 0 {
				log.Info().Int("attempt", attempt).Msg("CombatLoop: retarget ok")
			}
			return true
		}
		pad.Lock()
		attempt++
		time.Sleep(200 * time.Millisecond)
	}
	log.Info().Int("attempt", attempt).Msg("CombatLoop: retarget failed / out of combat")
	return false
}

// waitForCombatHUD waits until in-combat or an exit node hits (liberation cutscene).
func waitForCombatHUD(ctx *maa.Context, ctrl *maa.Controller, tasker *maa.Tasker, exitNodes []string, timeout time.Duration) bool {
	if ctrl == nil {
		time.Sleep(timeout)
		return false
	}
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		if tasker != nil && tasker.Stopping() {
			return false
		}
		ctrl.PostScreencap().Wait()
		img, err := ctrl.CacheImage()
		if err != nil || img == nil {
			time.Sleep(100 * time.Millisecond)
			continue
		}
		if hit, _ := anyExitHit(ctx, img, exitNodes); hit {
			return true
		}
		if inCombat(ctx, img) {
			return true
		}
		time.Sleep(120 * time.Millisecond)
	}
	return false
}

// peekExit captures once and reports exit-node / settle hit without sleeping long.
func peekExit(ctx *maa.Context, ctrl *maa.Controller, exitNodes []string) (bool, string) {
	if ctrl == nil {
		return false, ""
	}
	ctrl.PostScreencap().Wait()
	img, err := ctrl.CacheImage()
	if err != nil || img == nil {
		return false, ""
	}
	return anyExitHit(ctx, img, exitNodes)
}
