# Project Umbra (форк Barony)

Кооп survival-horror (1–4 игрока), викторианская готика, механика света/тьмы.
Дизайн: `docs/GAME_DESIGN.md`, план: `docs/ROADMAP.md`, идеи: `docs/IDEAS.md`,
ядро хоррора: `docs/LIGHT_AND_DREAD.md`.

## ГЛАВНОЕ ПРАВИЛО: сначала ищи готовое в движке

Перед реализацией ЛЮБОЙ фичи или ассета — проверь, нет ли в движке готовой
или похожей системы, которую можно переиспользовать с малыми правками.
Кодовая база огромна (~170 файлов, 15 лет разработки) и в ней уже есть
почти всё. Каждая фича, построенная на готовом, стоила нам в 5–10 раз
дешевле выдуманной с нуля — а кейс с «воксельным пламенем» показал цену
невыполнения правила (движок рисует огонь частицами, модели статичны).

Как искать: `grep -rn "<ключевое слово>" src/` по глаголам (spawn, degrade,
consume, summon), по `act*.cpp` (поведения сущностей), по `EFF_` (эффекты),
по существующим механикам-аналогам.

## Карта проверенных систем движка (что уже переиспользовано)

| Система | Где | Использовано в |
|---|---|---|
| Союзники + приказы | `forceFollower`, `FollowerMenu`, `ALLY_CMD_*` (actmonster.cpp) | компаньон |
| Спавн монстров | `summonMonsterNoSmoke` (actmonster.cpp:~1292) | компаньон, Тень |
| Износ предметов + сетевой sync | `Entity::degradeArmor` (entity.cpp) | выгорание факелов |
| Освещённость клетки | `Entity::entityLight()` (entity.cpp:531), `lightmaps[0]` | шкала страха |
| Свет: поля и дефы | `addLight(x,y,"имя")`, lights.json-дефы (light.cpp) | — |
| Огонь | частицы-билборды `spawnFlame`/`actFlame` + мерцание света; модели без пламени | холодные крепления |
| Настенные факелы | `actTorch` (acttorch.cpp), skill[4] = наш UNLIT | возврат света |
| Костры | `actCampfire` (actcampfire.cpp): здоровье, тушение, котёл | база для святилищ (№4) |
| Призраки игроков | `Player::Ghost_t` (player.hpp, actplayer.cpp) | база для №19/№20 |
| Бонус урона заклинаний | `getBonusFromCasterOfSpellElement` (magic/spell.cpp) | тёмная магия |
| Сетевые пакеты клиенту | `clientPacketHandlers` map в net.cpp (4-символьные коды) | UMBD-синк страха |
| Эффекты статов | `EFF_*` (stat.hpp), `setEffect` | EFF_FEAR + `monsterFearfulOfUid` — Тень бежит от света |
| Камера-тряска | `cameravars[i].shakex/shakey` (main.hpp:686) | урон психики от тьмы |
| Проклятия | `beatitude < 0` на Item | проклятья кормят страх |
| Анимация тайлов | `animatedtiles[]` — кадры соседними индексами | кадры воды/огней |
| Монстры | составные: воксельная модель на конечность, анимация поворотами | впереди (Тень-модель) |

## Форматы ассетов (проверено по загрузчикам)

- **Тайлы мира**: 32×32 PNG-текстуры на 3D-геометрии → `tools/art/gen_textures.py`
- **Объекты мира**: slab `.vox` — int32 x,y,z; данные x-major, 255=пусто;
  палитра 256×3 (0–63) → `tools/art/gen_models.py` (см. `loadVoxel`, files.cpp:2249)
- **Иконки UI/инвентаря**: RGBA-спрайты → секция спрайтов gen_textures.py
- MagicaVoxel .vox движок ОТВЕРГАЕТ (магик-заголовок 542658390)

## Сборка

```
cmake -B build -S . -DFMOD_ENABLED=OFF -DOPENAL_ENABLED=ON \
  -DSTEAMWORKS_ENABLED=0 -DEOS_ENABLED=0 -DPLAYFAB_ENABLED=0 -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4    # бинарь: build/umbra
```
- Аудио: только OpenAL (FMOD-путь юридически нежелателен; порт реанимирован нами).
- CMake пишет `src/Config.hpp` В ДЕРЕВО ИСХОДНИКОВ — один build-каталог, не два.
- Windows: `docs/BUILDING_WINDOWS.md`. CI: `.github/workflows/build-umbra-linux.yml`.

## Конвенции проекта

- Наш новый код — в отдельных файлах (`companion.cpp`, `dread.cpp`, `stalker.cpp`,
  `lightfuel.cpp`), заголовок PROJECT UMBRA + BSD-нотис; в легаси — точечные правки.
- Серверные тики: guard-паттерн (CLIENT/intro/gamePaused/loading/GAME_MODE_DEFAULT
  + `ticks % TICKS_PER_SECOND`), см. dreadUpdate.
- Сейвы форка: `~/.umbra` (НЕ трогать `~/.barony`).
- Строки пока англ. литералы; локализация через lang/ позже.
- Ассеты Barony проприетарны: в репозиторий не коммитить, релиз только со своими.
