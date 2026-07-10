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
#include "draw.hpp"
#include "colors.hpp"
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
static const float DREAD_CURSED_ITEM_RISE = 0.4f; // extra rise per equipped cursed item
static const float DREAD_LIGHT_CIRCLE_FALL = 2.f; // extra fall near a brightly lit ally
static const real_t DREAD_LIGHT_CIRCLE_RANGE = 4 * 16.0; // "near" = within 4 tiles

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

// Mind scars (idea #22): surviving the Consumed stage and calming back down
// leaves a mark - the dark frightens less, but the light comforts less too.
static const float DREAD_SCAR_FACTOR = 0.85f;
static const float DREAD_SCAR_CALM_THRESHOLD = 20.f;
static bool everConsumed[MAXPLAYERS] = { false };
static bool scarred[MAXPLAYERS] = { false };

// Grief (idea #11): the companion's death makes the dark press harder
// for the rest of the run.
static const float DREAD_GRIEF_FACTOR = 1.25f;
static bool grieving[MAXPLAYERS] = { false };

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

// Cursed equipment feeds the dark: each equipped item with negative
// beatitude speeds up dread growth.
static int cursedEquipmentCount(int player)
{
	if ( !stats[player] )
	{
		return 0;
	}
	Item* slots[] = {
		stats[player]->helmet, stats[player]->breastplate, stats[player]->gloves,
		stats[player]->shoes, stats[player]->shield, stats[player]->weapon,
		stats[player]->cloak, stats[player]->amulet, stats[player]->ring,
		stats[player]->mask,
	};
	int count = 0;
	for ( Item* item : slots )
	{
		if ( item && item->beatitude < 0 )
		{
			++count;
		}
	}
	return count;
}

// Huddling in a brightly lit ally's circle of light calms the nerves faster.
static bool litAllyIsNear(int player)
{
	if ( !players[player] || !players[player]->entity )
	{
		return false;
	}
	for ( int j = 0; j < MAXPLAYERS; ++j )
	{
		if ( j == player || client_disconnected[j] || !players[j] || !players[j]->entity || !stats[j] )
		{
			continue;
		}
		if ( stats[j]->HP <= 0 )
		{
			continue;
		}
		const real_t dx = players[j]->entity->x - players[player]->entity->x;
		const real_t dy = players[j]->entity->y - players[player]->entity->y;
		if ( dx * dx + dy * dy > DREAD_LIGHT_CIRCLE_RANGE * DREAD_LIGHT_CIRCLE_RANGE )
		{
			continue;
		}
		if ( players[j]->entity->entityLight() >= DREAD_LIGHT_BRIGHT )
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

void dreadRelieve(int player, float ceiling)
{
	if ( player < 0 || player >= MAXPLAYERS )
	{
		return;
	}
	if ( dread[player] > ceiling )
	{
		dread[player] = std::max(0.f, ceiling);
		dreadStage[player] = dreadStageForValue(dread[player]);
		dreadDamageCountdown[player] = 0;
	}
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

void dreadClientSetValue(int player, float value)
{
	if ( player < 0 || player >= MAXPLAYERS )
	{
		return;
	}
	dread[player] = std::min(std::max(0.f, value), DREAD_MAX);
}

void dreadOnCompanionDeath(int player)
{
	if ( player < 0 || player >= MAXPLAYERS || grieving[player] )
	{
		return;
	}
	grieving[player] = true;
	messagePlayer(player, MESSAGE_STATUS, "Albert is gone. The dark feels heavier now.");
}

void dreadOnMapLoad()
{
	const bool freshRun = (currentlevel == startfloor && !loadingsavegame);
	for ( int i = 0; i < MAXPLAYERS; ++i )
	{
		if ( freshRun )
		{
			dreadReset(i);
			everConsumed[i] = false;
			scarred[i] = false;
			grieving[i] = false;
		}
		else
		{
			dread[i] /= 2.f;
			dreadStage[i] = dreadStageForValue(dread[i]);
			dreadDamageCountdown[i] = 0;
		}
	}
}

void dreadDrawVignette(int player)
{
	if ( player < 0 || player >= MAXPLAYERS || !players[player] || !players[player]->isLocalPlayer() )
	{
		return;
	}
	const float value = dread[player];
	if ( value < DREAD_STAGE_THRESHOLDS[DREAD_STAGE_UNEASY] )
	{
		return;
	}

	// concentric darkening frames approximate a soft vignette without any
	// texture assets; thickness and opacity both scale with dread.
	const float intensity = std::min(1.f, value / DREAD_MAX);
	const int x1 = players[player]->camera_x1();
	const int y1 = players[player]->camera_y1();
	const int w = players[player]->camera_width();
	const int h = players[player]->camera_height();
	const int rings = 6;
	const int maxThickness = (std::min(w, h) / 5) * intensity;
	const Uint32 color = makeColorRGB(4, 2, 8); // near-black with a violet cast
	for ( int r = 0; r < rings; ++r )
	{
		const int inset = maxThickness * r / rings;
		const int thickness = std::max(1, maxThickness / rings + 1);
		const Uint8 alpha = static_cast<Uint8>(intensity * 110.f * (rings - r) / rings);
		if ( alpha == 0 )
		{
			continue;
		}
		SDL_Rect top = { x1 + inset, y1 + inset, w - inset * 2, thickness };
		SDL_Rect bottom = { x1 + inset, y1 + h - inset - thickness, w - inset * 2, thickness };
		SDL_Rect left = { x1 + inset, y1 + inset + thickness, thickness, h - (inset + thickness) * 2 };
		SDL_Rect right = { x1 + w - inset - thickness, y1 + inset + thickness, thickness, h - (inset + thickness) * 2 };
		drawRect(&top, color, alpha);
		drawRect(&bottom, color, alpha);
		drawRect(&left, color, alpha);
		drawRect(&right, color, alpha);
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
			rise += DREAD_CURSED_ITEM_RISE * cursedEquipmentCount(i);
			if ( companionIsNear(i) )
			{
				rise *= DREAD_COMPANION_FACTOR;
			}
			if ( scarred[i] )
			{
				rise *= DREAD_SCAR_FACTOR;
			}
			if ( grieving[i] )
			{
				rise *= DREAD_GRIEF_FACTOR;
			}
			value += rise;
		}
		else
		{
			float fall = (light >= DREAD_LIGHT_BRIGHT) ? DREAD_FALL_BRIGHT : DREAD_FALL_DIM;
			if ( litAllyIsNear(i) )
			{
				fall += DREAD_LIGHT_CIRCLE_FALL;
			}
			if ( scarred[i] )
			{
				fall *= DREAD_SCAR_FACTOR; // the light comforts less, too
			}
			value -= fall;
		}
		value = std::min(std::max(0.f, value), DREAD_MAX);

		// mind scars: survive the deepest stage, then find calm
		if ( value >= DREAD_STAGE_THRESHOLDS[DREAD_STAGE_CONSUMED] )
		{
			everConsumed[i] = true;
		}
		else if ( everConsumed[i] && !scarred[i] && value <= DREAD_SCAR_CALM_THRESHOLD )
		{
			scarred[i] = true;
			messagePlayer(i, MESSAGE_HINT,
				"The dark has left its mark on you. You fear it less... and the light warms you less.");
		}

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

		// keep remote clients' vignette in sync (1 byte, once a second;
		// lossy delivery is fine - the next tick self-heals)
		if ( multiplayer == SERVER && i > 0 && !players[i]->isLocalPlayer()
			&& net_packet && net_packet->data )
		{
			strcpy((char*)net_packet->data, "UMBD");
			net_packet->data[4] = static_cast<Uint8>(lround(value));
			net_packet->address.host = net_clients[i - 1].host;
			net_packet->address.port = net_clients[i - 1].port;
			net_packet->len = 5;
			sendPacket(net_sock, -1, net_packet, i - 1);
		}
	}
}
