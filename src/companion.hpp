/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: companion.hpp
	Desc: solo-mode AI companion. When a fresh singleplayer game starts,
	the player is joined by a loyal follower who takes orders through the
	existing FollowerMenu / ALLY_CMD system.

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#pragma once

// Stat attribute key marking the solo companion (persists through level
// transitions along with the rest of the follower's stats).
#define COMPANION_ATTRIBUTE "UMBRA_COMPANION"

// Called at the end of assignActions() after players are placed on the map.
// Spawns the companion next to player 0 on a fresh singleplayer run:
// no-op for clients, multiplayer games, splitscreen, savegame loads,
// non-default game modes, later floors, or if the player already has
// followers (including a previously spawned companion).
void companionSpawnAtGameStart();

// Called once per frame from gameLogic(); rate-limits itself to one
// evaluation per second. Drives the companion's spoken barks (darkness,
// the player's rising dread, his own wounds) and detects his death.
// Server-side only.
void companionUpdate();

// Called after each map is populated (next to dreadOnMapLoad): resets the
// death-detection tracking on a fresh run so a previous run's state can't
// trigger false grief.
void companionOnMapLoad();
