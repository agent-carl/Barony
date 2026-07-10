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
