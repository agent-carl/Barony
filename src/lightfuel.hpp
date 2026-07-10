/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: lightfuel.hpp
	Desc: carried light sources burn down over time. A torch or lantern
	held in the shield slot slowly loses status; at BROKEN the engine
	already unequips it and the light goes out. Spare torches reignite
	automatically via the existing degradeArmor torch handling.
	Design: docs/LIGHT_AND_DREAD.md §4 (light as a resource).

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#pragma once

// Called once per frame from gameLogic(); rate-limits itself to one
// evaluation per second. Server-side only.
void lightFuelUpdate();
