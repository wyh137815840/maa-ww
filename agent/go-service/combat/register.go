package combat

import "github.com/MaaXYZ/maa-framework-go/v4"

// Register registers combat CustomAction components.
func Register() {
	maa.AgentServerRegisterCustomAction("CombatLoop", &CombatLoopAction{})
	maa.AgentServerRegisterCustomAction("WalkToTacetTreasure", &WalkToTacetTreasureAction{})
	maa.AgentServerRegisterCustomAction("NestKinds", &NestKindsAction{})
	maa.AgentServerRegisterCustomAction("NestApproach", &NestApproachAction{})
	maa.AgentServerRegisterCustomAction("NestAbsorbSearch", &NestAbsorbSearchAction{})
}
