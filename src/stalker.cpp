/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: stalker.cpp
	Desc: the Umbral Stalker (see stalker.hpp).

	Copyright (c) 2026 Project Umbra authors. BSD 2-Clause, see NOTICE.md.

-------------------------------------------------------------------------------*/

#include "main.hpp"
#include "game.hpp"
#include "stat.hpp"
#include "entity.hpp"
#include "monster.hpp"
#include "player.hpp"
#include "net.hpp"
#include "mod_tools.hpp"
#include "prng.hpp"
#include "dread.hpp"
#include "stalker.hpp"

static const float STALKER_SPAWN_DREAD = 100.f; // dread level that births a stalker
static const float STALKER_DISSOLVE_DREAD = 25.f; // dread below this dissolves it
static const float STALKER_CATHARSIS_DREAD = 50.f; // dread cap after surviving one
static const int STALKER_LIGHT_SEAR = 96;      // light level that burns the stalker
static const int STALKER_SEAR_DAMAGE = 20;     // damage per second in bright light
static const int STALKER_COOLDOWN_SECONDS = 90; // grace period between stalkers
static const int STALKER_SPAWN_DISTANCE_TILES = 6;

static Uint32 stalkerUid[MAXPLAYERS] = { 0 };
static int stalkerCooldown[MAXPLAYERS] = { 0 };
static int stalkerSearMessageCooldown[MAXPLAYERS] = { 0 };

static void stalkerSpawn(int player)
{
	Entity* leader = players[player]->entity;
	const real_t angle = (local_rng.rand() % 360) * PI / 180.0;
	const real_t dist = STALKER_SPAWN_DISTANCE_TILES * 16.0;
	const long x = static_cast<long>(leader->x + cos(angle) * dist);
	const long y = static_cast<long>(leader->y + sin(angle) * dist);

	Entity* stalker = summonMonsterNoSmoke(SHADOW, x, y, false);
	if ( !stalker )
	{
		return; // no room this second; dread stays at peak, we retry next tick
	}
	Stat* stalkerStats = stalker->getStats();
	if ( !stalkerStats )
	{
		list_RemoveNode(stalker->mynode);
		return;
	}
	stalkerStats->setAttribute(STALKER_ATTRIBUTE, "1");
	stalker->monsterAcquireAttackTarget(*leader, MONSTER_STATE_PATH);

	stalkerUid[player] = stalker->getUID();
	messagePlayer(player, MESSAGE_STATUS, "The darkness takes shape. Something is hunting you.");
	printlog("[stalker] spawned for player %d at (%ld, %ld)", player, x, y);
}

void stalkerUpdate()
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
		if ( stalkerCooldown[i] > 0 )
		{
			--stalkerCooldown[i];
		}
		if ( stalkerSearMessageCooldown[i] > 0 )
		{
			--stalkerSearMessageCooldown[i];
		}

		Entity* stalker = stalkerUid[i] ? uidToEntity(stalkerUid[i]) : nullptr;
		Stat* stalkerStats = stalker ? stalker->getStats() : nullptr;

		// stalker gone (killed or dissolved): catharsis
		if ( stalkerUid[i] && (!stalker || !stalkerStats || stalkerStats->HP <= 0) )
		{
			stalkerUid[i] = 0;
			stalkerCooldown[i] = STALKER_COOLDOWN_SECONDS;
			dreadRelieve(i, STALKER_CATHARSIS_DREAD);
			if ( !client_disconnected[i] )
			{
				messagePlayer(i, MESSAGE_HINT, "The shadow is gone. You can breathe again.");
			}
			continue;
		}

		if ( client_disconnected[i] || !players[i] || !players[i]->entity || !stats[i] )
		{
			continue;
		}
		if ( stats[i]->HP <= 0 )
		{
			continue;
		}

		if ( stalker && stalkerStats )
		{
			// bright light sears it - and the engine's own fear AI makes it
			// recoil from the light-bearer (EFF_FEAR + monsterFearfulOfUid)
			if ( stalker->entityLight() >= STALKER_LIGHT_SEAR )
			{
				stalker->modHP(-STALKER_SEAR_DAMAGE);
				stalker->setEffect(EFF_FEAR, true, 3 * TICKS_PER_SECOND, true);
				stalker->monsterFearfulOfUid = players[i]->entity->getUID();
				if ( stalkerSearMessageCooldown[i] <= 0 )
				{
					stalkerSearMessageCooldown[i] = 5;
					messagePlayer(i, MESSAGE_COMBAT, "The light sears the shadow!");
				}
			}
			// the hearth is anathema: reaching a sanctuary banishes it
			else if ( dreadNearSanctuary(i) )
			{
				stalkerStats->HP = 0;
				messagePlayer(i, MESSAGE_HINT, "The shadow cannot abide the hearth.");
			}
			// the player found calm: it loses its grip and dissolves
			else if ( dreadGet(i) < STALKER_DISSOLVE_DREAD )
			{
				stalkerStats->HP = 0; // let the monster death path handle cleanup + sync
			}
			continue;
		}

		if ( stalkerCooldown[i] <= 0 && dreadGet(i) >= STALKER_SPAWN_DREAD
			&& !dreadNearSanctuary(i) )
		{
			stalkerSpawn(i);
		}
	}
}
