/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: dread.hpp
	Desc: the Dread meter — the core light-vs-darkness horror mechanic.
	Darkness raises each player's dread; light lowers it. High dread
	whispers, shakes, and finally wounds (but never kills by itself).
	See docs/LIGHT_AND_DREAD.md for the full design.

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#pragma once

// Called once per frame from gameLogic(); rate-limits itself to one
// evaluation per second. No-op on network clients, on the main menu,
// while paused, and outside the default game mode.
void dreadUpdate();

// Current dread of a player, 0..100 (for future UI/effects hooks).
float dreadGet(int player);

// Called after each map is populated (assignActions): zeroes dread on a
// fresh run's start floor, halves it on ordinary level transitions.
void dreadOnMapLoad();
void dreadReset(int player);
