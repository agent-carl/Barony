/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: lightfuel.cpp
	Desc: carried light sources burn down (see lightfuel.hpp).

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#include "main.hpp"
#include "game.hpp"
#include "stat.hpp"
#include "entity.hpp"
#include "items.hpp"
#include "player.hpp"
#include "net.hpp"
#include "mod_tools.hpp"
#include "lightfuel.hpp"

// Seconds of burning per one status stage (EXCELLENT -> ... -> BROKEN is
// 4 stages, so a fresh torch lasts 4x this). Tuning constants; candidates
// for ConsoleVariable once the values settle in playtests.
static const int TORCH_SECONDS_PER_STAGE = 90;    // fresh torch ~6 minutes
static const int LANTERN_SECONDS_PER_STAGE = 240; // fresh lantern ~16 minutes
static const int SHIELD_SLOT_ARMORNUM = 4;        // degradeArmor slot id for shield

static int burnProgress[MAXPLAYERS] = { 0 };
static int lastShieldType[MAXPLAYERS] = { -1 };

void lightFuelUpdate()
{
	if ( multiplayer == CLIENT || intro || gamePaused || loading )
	{
		return;
	}
	if ( gameModeManager.getMode() != GameModeManager_t::GAME_MODE_DEFAULT )
	{
		return;
	}
	if ( ticks % TICKS_PER_SECOND != 0 )
	{
		return;
	}

	for ( int i = 0; i < MAXPLAYERS; ++i )
	{
		if ( client_disconnected[i] || !players[i] || !players[i]->entity || !stats[i] )
		{
			continue;
		}
		if ( stats[i]->HP <= 0 )
		{
			continue;
		}

		Item* shield = stats[i]->shield;
		int secondsPerStage = 0;
		if ( shield && shield->type == TOOL_TORCH )
		{
			secondsPerStage = TORCH_SECONDS_PER_STAGE;
		}
		else if ( shield && shield->type == TOOL_LANTERN )
		{
			secondsPerStage = LANTERN_SECONDS_PER_STAGE;
		}

		const int currentType = shield ? static_cast<int>(shield->type) : -1;
		if ( currentType != lastShieldType[i] )
		{
			lastShieldType[i] = currentType;
			burnProgress[i] = 0;
		}
		if ( secondsPerStage <= 0 )
		{
			continue;
		}

		if ( ++burnProgress[i] >= secondsPerStage )
		{
			burnProgress[i] = 0;
			players[i]->entity->degradeArmor(*stats[i], *shield, SHIELD_SLOT_ARMORNUM);
		}
	}
}
