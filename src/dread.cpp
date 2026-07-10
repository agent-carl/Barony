/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: dread.cpp
	Desc: the Dread meter (see dread.hpp and docs/LIGHT_AND_DREAD.md).

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#include "main.hpp"
#include "game.hpp"
#include "stat.hpp"
#include "entity.hpp"
#include "player.hpp"
#include "net.hpp"
#include "mod_tools.hpp"
#include "scores.hpp"
#include "companion.hpp"
#include "dread.hpp"

// Tuning constants (candidates for ConsoleVariable once the values settle).
static const int DREAD_LIGHT_DARK = 32;       // light level below this = darkness
static const int DREAD_LIGHT_BRIGHT = 96;     // light level at or above this = safety
static const float DREAD_RISE_PER_SEC = 3.f;  // dread gain per second in darkness
static const float DREAD_RISE_PER_5_FLOORS = 1.f; // extra gain per 5 dungeon levels
static const float DREAD_FALL_DIM = 1.f;      // dread loss per second in dim light
static const float DREAD_FALL_BRIGHT = 5.f;   // dread loss per second in bright light
static const float DREAD_MAX = 100.f;
static const int DREAD_DAMAGE = 2;            // psychic damage at the highest stage
static const int DREAD_DAMAGE_PERIOD = 3;     // seconds between damage ticks
static const float DREAD_COMPANION_FACTOR = 0.75f; // rise multiplier with the companion nearby
static const real_t DREAD_COMPANION_RANGE = 8 * 16.0; // "nearby" = within 8 tiles

// Threshold stages. A message fires only when a stage is entered from below.
enum DreadStage : int
{
	DREAD_STAGE_CALM = 0,
	DREAD_STAGE_UNEASY,    // 25+
	DREAD_STAGE_SHAKEN,    // 50+
	DREAD_STAGE_TERRIFIED, // 75+
	DREAD_STAGE_CONSUMED   // 90+
};
static const float DREAD_STAGE_THRESHOLDS[] = { 0.f, 25.f, 50.f, 75.f, 90.f };

static const char* DREAD_STAGE_MESSAGES[] = {
	"",
	"The darkness presses in. You feel watched.",
	"Your hands tremble. The shadows are whispering.",
	"Terror claws at your mind. Find light!",
	"The dark is inside you now. It feeds.",
};

static float dread[MAXPLAYERS] = { 0.f };
static int dreadStage[MAXPLAYERS] = { DREAD_STAGE_CALM };
static int dreadDamageCountdown[MAXPLAYERS] = { 0 };

// A living companion close by steadies the nerves: dread rises slower.
static bool companionIsNear(int player)
{
	if ( !stats[player] || !players[player] || !players[player]->entity )
	{
		return false;
	}
	for ( node_t* node = stats[player]->FOLLOWERS.first; node != nullptr; node = node->next )
	{
		Uint32* uid = (Uint32*)node->element;
		Entity* follower = uid ? uidToEntity(*uid) : nullptr;
		if ( !follower )
		{
			continue;
		}
		Stat* followerStats = follower->getStats();
		if ( !followerStats || followerStats->HP <= 0 )
		{
			continue;
		}
		if ( followerStats->getAttribute(COMPANION_ATTRIBUTE) == "" )
		{
			continue;
		}
		const real_t dx = follower->x - players[player]->entity->x;
		const real_t dy = follower->y - players[player]->entity->y;
		if ( dx * dx + dy * dy <= DREAD_COMPANION_RANGE * DREAD_COMPANION_RANGE )
		{
			return true;
		}
	}
	return false;
}

static int dreadStageForValue(float value)
{
	int stage = DREAD_STAGE_CALM;
	for ( int s = DREAD_STAGE_CONSUMED; s > DREAD_STAGE_CALM; --s )
	{
		if ( value >= DREAD_STAGE_THRESHOLDS[s] )
		{
			stage = s;
			break;
		}
	}
	return stage;
}

float dreadGet(int player)
{
	if ( player < 0 || player >= MAXPLAYERS )
	{
		return 0.f;
	}
	return dread[player];
}

void dreadReset(int player)
{
	if ( player < 0 || player >= MAXPLAYERS )
	{
		return;
	}
	dread[player] = 0.f;
	dreadStage[player] = DREAD_STAGE_CALM;
	dreadDamageCountdown[player] = 0;
}

void dreadOnMapLoad()
{
	const bool freshRun = (currentlevel == startfloor && !loadingsavegame);
	for ( int i = 0; i < MAXPLAYERS; ++i )
	{
		if ( freshRun )
		{
			dreadReset(i);
		}
		else
		{
			dread[i] /= 2.f;
			dreadStage[i] = dreadStageForValue(dread[i]);
			dreadDamageCountdown[i] = 0;
		}
	}
}

void dreadUpdate()
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
			dreadReset(i);
			continue;
		}

		const int light = players[i]->entity->entityLight();
		float& value = dread[i];
		if ( light < DREAD_LIGHT_DARK )
		{
			float rise = DREAD_RISE_PER_SEC + DREAD_RISE_PER_5_FLOORS * (currentlevel / 5);
			if ( companionIsNear(i) )
			{
				rise *= DREAD_COMPANION_FACTOR;
			}
			value += rise;
		}
		else if ( light >= DREAD_LIGHT_BRIGHT )
		{
			value -= DREAD_FALL_BRIGHT;
		}
		else
		{
			value -= DREAD_FALL_DIM;
		}
		value = std::min(std::max(0.f, value), DREAD_MAX);

		const int newStage = dreadStageForValue(value);
		if ( newStage > dreadStage[i] && DREAD_STAGE_MESSAGES[newStage][0] )
		{
			messagePlayer(i, MESSAGE_HINT, DREAD_STAGE_MESSAGES[newStage]);
		}
		dreadStage[i] = newStage;

		if ( newStage >= DREAD_STAGE_CONSUMED )
		{
			if ( --dreadDamageCountdown[i] <= 0 )
			{
				dreadDamageCountdown[i] = DREAD_DAMAGE_PERIOD;
				// the dark wounds but never kills on its own
				const int damage = std::min(DREAD_DAMAGE, stats[i]->HP - 1);
				if ( damage > 0 )
				{
					players[i]->entity->modHP(-damage);
					messagePlayer(i, MESSAGE_STATUS, "The darkness gnaws at your flesh.");
				}
			}
		}
		else
		{
			dreadDamageCountdown[i] = 0;
		}
	}
}
