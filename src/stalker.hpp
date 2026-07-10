/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: stalker.hpp
	Desc: the Umbral Stalker. When a player's dread peaks (100), the
	darkness takes shape: a shadow creature spawns nearby and hunts that
	player. Bright light sears it. Killing it or outlasting it relieves
	dread — the catharsis that closes the horror loop.
	Design: docs/IDEAS.md idea #2, docs/LIGHT_AND_DREAD.md.

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#pragma once

// Stat attribute key marking a spawned stalker.
#define STALKER_ATTRIBUTE "UMBRA_STALKER"

// Called once per frame from gameLogic(); rate-limits itself to one
// evaluation per second. Server-side only.
void stalkerUpdate();
