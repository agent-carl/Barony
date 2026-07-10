/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: companion.cpp
	Desc: solo-mode AI companion (see companion.hpp).

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#include "main.hpp"
#include "game.hpp"
#include "stat.hpp"
#include "entity.hpp"
#include "monster.hpp"
#include "player.hpp"
#include "net.hpp"
#include "scores.hpp"
#include "mod_tools.hpp"
#include "dread.hpp"
#include "companion.hpp"

static const char* COMPANION_NAME = "Albert";

void companionSpawnAtGameStart()
{
	if ( multiplayer != SINGLE || splitscreen || intro )
	{
		return;
	}
	if ( loadingsavegame )
	{
		// the follower system already restores a living companion from the
		// save; a dead one stays dead.
		return;
	}
	if ( currentlevel != startfloor )
	{
		return;
	}
	if ( gameModeManager.getMode() != GameModeManager_t::GAME_MODE_DEFAULT )
	{
		return;
	}
	Entity* leader = players[0] ? players[0]->entity : nullptr;
	if ( !leader || !stats[0] )
	{
		return;
	}
	if ( list_Size(&stats[0]->FOLLOWERS) > 0 )
	{
		return;
	}

	Entity* companion = summonMonsterNoSmoke(HUMAN, leader->x + 16, leader->y, false);
	if ( !companion )
	{
		printlog("[companion] failed to spawn companion at (%d, %d)",
			static_cast<int>(leader->x + 16), static_cast<int>(leader->y));
		return;
	}
	Stat* companionStats = companion->getStats();
	if ( !companionStats )
	{
		printlog("[companion] spawned companion has no stats, removing");
		list_RemoveNode(companion->mynode);
		return;
	}

	strcpy(companionStats->name, COMPANION_NAME);
	companionStats->setAttribute(COMPANION_ATTRIBUTE, "1");

	if ( !forceFollower(*leader, *companion) )
	{
		printlog("[companion] forceFollower failed, removing companion");
		list_RemoveNode(companion->mynode);
		return;
	}
	companion->monsterAllyPickupItems = 0; // don't hoover the floor by default

	messagePlayer(0, MESSAGE_HINT, "%s joins you. Interact with him to give orders.",
		COMPANION_NAME);
	printlog("[companion] %s spawned as follower of player 0", COMPANION_NAME);
}

// --- Barks -------------------------------------------------------------------
// The companion speaks up about darkness, the player's nerves, and his own
// wounds, with per-topic cooldowns so he never turns into a metronome.

static const int BARK_DARKNESS_COOLDOWN = 45;   // seconds
static const int BARK_WOUNDED_COOLDOWN = 60;    // seconds
static const int BARK_DARK_LIGHT_LEVEL = 32;    // matches DREAD_LIGHT_DARK
static const float BARK_DREAD_THRESHOLD = 50.f;

static int barkDarknessCooldown[MAXPLAYERS] = { 0 };
static int barkWoundedCooldown[MAXPLAYERS] = { 0 };
static bool barkedDread[MAXPLAYERS] = { false };

static Entity* companionForPlayer(int player)
{
	if ( !stats[player] )
	{
		return nullptr;
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
		if ( followerStats && followerStats->HP > 0
			&& followerStats->getAttribute(COMPANION_ATTRIBUTE) != "" )
		{
			return follower;
		}
	}
	return nullptr;
}

static void bark(int player, const char* line)
{
	messagePlayer(player, MESSAGE_WORLD, "%s: \"%s\"", COMPANION_NAME, line);
}

void companionUpdate()
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
		if ( barkDarknessCooldown[i] > 0 )
		{
			--barkDarknessCooldown[i];
		}
		if ( barkWoundedCooldown[i] > 0 )
		{
			--barkWoundedCooldown[i];
		}

		if ( client_disconnected[i] || !players[i] || !players[i]->entity || !stats[i] )
		{
			continue;
		}
		if ( stats[i]->HP <= 0 )
		{
			continue;
		}
		Entity* companion = companionForPlayer(i);
		if ( !companion )
		{
			continue;
		}
		Stat* companionStats = companion->getStats();

		// his own wounds come first
		if ( companionStats && companionStats->HP < companionStats->MAXHP / 3
			&& barkWoundedCooldown[i] <= 0 )
		{
			barkWoundedCooldown[i] = BARK_WOUNDED_COOLDOWN;
			bark(i, "I'm... I'm hurt, sir. Don't leave me behind.");
			continue;
		}

		// the player's fraying nerves (once per crossing)
		if ( dreadGet(i) >= BARK_DREAD_THRESHOLD )
		{
			if ( !barkedDread[i] )
			{
				barkedDread[i] = true;
				bark(i, "Your hands are shaking, sir. We should find a lamp.");
				continue;
			}
		}
		else
		{
			barkedDread[i] = false;
		}

		// the dark itself
		if ( players[i]->entity->entityLight() < BARK_DARK_LIGHT_LEVEL
			&& barkDarknessCooldown[i] <= 0 )
		{
			barkDarknessCooldown[i] = BARK_DARKNESS_COOLDOWN;
			bark(i, "Stay close, sir. And mind the dark.");
		}
	}
}
