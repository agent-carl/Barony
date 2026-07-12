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
#include "items.hpp"
#include "player.hpp"
#include "net.hpp"
#include "scores.hpp"
#include "mod_tools.hpp"
#include "dread.hpp"
#include "companion.hpp"

// Archetypes (idea #12): the retainer is picked to complement the
// player's class - martial classes get a medic, casters get a soldier,
// everyone else gets an occultist.
enum CompanionRole : int
{
	COMPANION_SOLDIER,
	COMPANION_MEDIC,
	COMPANION_OCCULTIST,
};

struct CompanionRoleDef
{
	const char* key;        // stored in COMPANION_ROLE_ATTRIBUTE
	const char* name;
	float dreadRiseFactor;  // aura strength (lower = calmer)
};

static const CompanionRoleDef COMPANION_ROLES[] = {
	{ "soldier",   "Sergeant Briggs", 0.85f },
	{ "medic",     "Doctor Rosalind", 0.75f },
	{ "occultist", "Mordecai",        0.60f },
};

static const real_t COMPANION_AURA_RANGE = 8 * 16.0; // 8 tiles

static CompanionRole companionRoleForPlayerClass(int playerClass)
{
	switch ( playerClass )
	{
		case CLASS_WIZARD:
		case CLASS_ARCANIST:
		case CLASS_CONJURER:
		case CLASS_ACCURSED:
		case CLASS_MESMER:
		case CLASS_SHAMAN:
			return COMPANION_SOLDIER; // casters lack a frontline
		case CLASS_BARBARIAN:
		case CLASS_WARRIOR:
		case CLASS_ROGUE:
		case CLASS_NINJA:
		case CLASS_MONK:
		case CLASS_PUNISHER:
		case CLASS_HUNTER:
		case CLASS_SAPPER:
		case CLASS_MACHINIST:
			return COMPANION_MEDIC; // fighters lack healing
		default:
			return COMPANION_OCCULTIST; // everyone else gets steadier nerves
	}
}

static const CompanionRoleDef* companionRoleFromStats(Stat* companionStats)
{
	if ( !companionStats )
	{
		return nullptr;
	}
	const std::string role = companionStats->getAttribute(COMPANION_ROLE_ATTRIBUTE);
	for ( const auto& def : COMPANION_ROLES )
	{
		if ( role == def.key )
		{
			return &def;
		}
	}
	return nullptr;
}

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

	const CompanionRole role = companionRoleForPlayerClass(client_classes[0]);
	const CompanionRoleDef& roleDef = COMPANION_ROLES[role];
	strcpy(companionStats->name, roleDef.name);
	companionStats->setAttribute(COMPANION_ATTRIBUTE, "1");
	companionStats->setAttribute(COMPANION_ROLE_ATTRIBUTE, roleDef.key);
	switch ( role )
	{
		case COMPANION_SOLDIER: // a proper frontline
			companionStats->STR += 3;
			companionStats->CON += 2;
			companionStats->MAXHP += 30;
			companionStats->HP = companionStats->MAXHP;
			break;
		case COMPANION_MEDIC:
			companionStats->INT += 2;
			break;
		case COMPANION_OCCULTIST:
			companionStats->INT += 3;
			break;
	}

	// the lantern-bearer: the companion carries a dependable light so a
	// solo player keeps both hands free. initHuman only rolls random gear
	// for empty slots, so this pre-set lantern survives his first AI tick.
	// Carried lights burn down for players only - this lamp is the
	// reliable one.
	if ( !companionStats->shield )
	{
		companionStats->shield = newItem(TOOL_LANTERN, EXCELLENT, 0, 1, 0, true, nullptr);
	}

	if ( !forceFollower(*leader, *companion) )
	{
		printlog("[companion] forceFollower failed, removing companion");
		list_RemoveNode(companion->mynode);
		return;
	}
	companion->monsterAllyPickupItems = 0; // don't hoover the floor by default

	messagePlayer(0, MESSAGE_HINT, "%s joins you. Interact with them to give orders.",
		roleDef.name);
	printlog("[companion] %s (%s) spawned as follower of player 0", roleDef.name, roleDef.key);
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

// Death detection: followers are recreated with fresh uids on every level
// transition, so instead of tracking uids we count consecutive seconds
// without a living companion. A transition restores him within a tick;
// three missing seconds after having had him means he is dead.
static bool hadCompanion[MAXPLAYERS] = { false };
static int companionMissingSeconds[MAXPLAYERS] = { 0 };
static const int COMPANION_DEATH_CONFIRM_SECONDS = 3;

// role ability cooldowns
static const int MEDIC_HEAL_COOLDOWN = 45;   // seconds
static const int MEDIC_HEAL_AMOUNT = 8;
static const int OCCULTIST_MANA_PERIOD = 10; // seconds
static int medicHealCooldown[MAXPLAYERS] = { 0 };
static int occultistManaCountdown[MAXPLAYERS] = { 0 };

// Trust (idea #10): time spent together (and care received) deepens the
// bond - each tier steadies the player's nerves a little more and earns
// a new line. Trust is per-run.
static const int TRUST_SECONDS_PER_POINT = 60; // a point per minute together
static const int TRUST_TIER1 = 3;              // ~3 minutes
static const int TRUST_TIER2 = 6;              // ~6 minutes
static const float TRUST_TIER_AURA_BONUS = 0.05f; // extra rise reduction per tier
static int trust[MAXPLAYERS] = { 0 };
static int trustAccumSeconds[MAXPLAYERS] = { 0 };
static int trustTierAnnounced[MAXPLAYERS] = { 0 };

static int trustTier(int player)
{
	if ( trust[player] >= TRUST_TIER2 )
	{
		return 2;
	}
	if ( trust[player] >= TRUST_TIER1 )
	{
		return 1;
	}
	return 0;
}

void companionOnMapLoad()
{
	if ( currentlevel == startfloor && !loadingsavegame )
	{
		for ( int i = 0; i < MAXPLAYERS; ++i )
		{
			hadCompanion[i] = false;
			companionMissingSeconds[i] = 0;
			barkedDread[i] = false;
			barkDarknessCooldown[i] = 0;
			barkWoundedCooldown[i] = 0;
			trust[i] = 0;
			trustAccumSeconds[i] = 0;
			trustTierAnnounced[i] = 0;
		}
	}
}

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

static void bark(int player, Stat* companionStats, const char* line)
{
	messagePlayer(player, MESSAGE_WORLD, "%s: \"%s\"",
		companionStats ? companionStats->name : "Companion", line);
}

static bool companionIsNearPlayer(int player, Entity* companion)
{
	if ( !companion || !players[player] || !players[player]->entity )
	{
		return false;
	}
	const real_t dx = companion->x - players[player]->entity->x;
	const real_t dy = companion->y - players[player]->entity->y;
	return dx * dx + dy * dy <= COMPANION_AURA_RANGE * COMPANION_AURA_RANGE;
}

float companionDreadRiseFactor(int player)
{
	if ( player < 0 || player >= MAXPLAYERS )
	{
		return 1.f;
	}
	Entity* companion = companionForPlayer(player);
	if ( !companion || !companionIsNearPlayer(player, companion) )
	{
		return 1.f;
	}
	const CompanionRoleDef* def = companionRoleFromStats(companion->getStats());
	float factor = def ? def->dreadRiseFactor : 0.75f;
	factor *= (1.f - TRUST_TIER_AURA_BONUS * trustTier(player)); // the bond steadies nerves
	return factor;
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
			if ( hadCompanion[i] )
			{
				if ( ++companionMissingSeconds[i] >= COMPANION_DEATH_CONFIRM_SECONDS )
				{
					hadCompanion[i] = false;
					companionMissingSeconds[i] = 0;
					dreadOnCompanionDeath(i);
				}
			}
			continue;
		}
		hadCompanion[i] = true;
		companionMissingSeconds[i] = 0;
		Stat* companionStats = companion->getStats();
		const CompanionRoleDef* roleDef = companionRoleFromStats(companionStats);
		const bool near = companionIsNearPlayer(i, companion);

		// trust deepens with time spent together
		if ( near && ++trustAccumSeconds[i] >= TRUST_SECONDS_PER_POINT )
		{
			trustAccumSeconds[i] = 0;
			++trust[i];
		}
		const int tier = trustTier(i);
		if ( tier > trustTierAnnounced[i] )
		{
			trustTierAnnounced[i] = tier;
			bark(i, companionStats, tier == 1
				? "I'm glad it's you down here with me, sir."
				: "Whatever waits in that dark - we face it together.");
		}

		// role abilities
		if ( medicHealCooldown[i] > 0 )
		{
			--medicHealCooldown[i];
		}
		if ( roleDef && near )
		{
			if ( roleDef->key[0] == 'm' ) // medic
			{
				if ( medicHealCooldown[i] <= 0 && stats[i]->HP < stats[i]->MAXHP / 2 )
				{
					medicHealCooldown[i] = MEDIC_HEAL_COOLDOWN;
					players[i]->entity->modHP(MEDIC_HEAL_AMOUNT);
					++trust[i]; // care received deepens the bond
					bark(i, companionStats, "Hold still, sir. This will sting.");
				}
			}
			else if ( roleDef->key[0] == 'o' ) // occultist
			{
				if ( --occultistManaCountdown[i] <= 0 )
				{
					occultistManaCountdown[i] = OCCULTIST_MANA_PERIOD;
					if ( stats[i]->MP < stats[i]->MAXMP )
					{
						players[i]->entity->modMP(1);
					}
				}
			}
		}

		// his own wounds come first
		if ( companionStats && companionStats->HP < companionStats->MAXHP / 3
			&& barkWoundedCooldown[i] <= 0 )
		{
			barkWoundedCooldown[i] = BARK_WOUNDED_COOLDOWN;
			bark(i, companionStats, "I'm... I'm hurt, sir. Don't leave me behind.");
			continue;
		}

		// the player's fraying nerves (once per crossing)
		if ( dreadGet(i) >= BARK_DREAD_THRESHOLD )
		{
			if ( !barkedDread[i] )
			{
				barkedDread[i] = true;
				bark(i, companionStats, "Your hands are shaking, sir. We should find a lamp.");
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
			bark(i, companionStats, "Stay close, sir. And mind the dark.");
		}
	}
}
