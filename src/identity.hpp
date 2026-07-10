/*-------------------------------------------------------------------------------

	PROJECT UMBRA
	File: identity.hpp
	Desc: central place for the game's public identity (name, window title).

	This project is a fork of Barony (c) 2013-2020 Turning Wheel LLC,
	used under the BSD 2-Clause License. See LICENSE.txt and NOTICE.md.

	Keep every user-visible occurrence of the game's name behind these
	macros so a rename is a one-line change. Internal/save-format strings
	(e.g. VERSION in game.hpp) are intentionally NOT tied to these while
	we still develop against retail Barony assets.

-------------------------------------------------------------------------------*/

#pragma once

// User-visible product name: window title, crash dialogs, log banner.
#define GAME_TITLE "Project Umbra"

// Short id for file/registry-ish uses we introduce ourselves (no spaces).
#define GAME_SHORT_NAME "umbra"

// Fork attribution shown in logs/about screens.
#define GAME_FORK_NOTICE "Based on Barony (c) Turning Wheel LLC (BSD 2-Clause)"
