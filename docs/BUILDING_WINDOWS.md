# Project Umbra — запуск на Windows (инструкция плейтеста)

> Цель: собрать наш форк, запустить его на ассетах твоей Steam-копии Barony
> и прогнать чек-лист механик. Время: ~30–60 мин на первую сборку
> (в основном ждать vcpkg), дальше пересборки — минуты.

---

## Что понадобится

1. **Visual Studio 2022 Community** — при установке отметь workload
   **«Разработка классических приложений на C++»** (включает CMake и SDK).
2. **Git** — https://git-scm.com/download/win (настройки по умолчанию).
3. **Barony в Steam** — установленная (источник ассетов).
4. ~10 ГБ свободного места (vcpkg собирает библиотеки из исходников).

---

## Шаг 1. vcpkg и зависимости (один раз)

Открой **PowerShell** и выполни построчно:

```powershell
git clone https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
```

Затем зависимости (это долгий шаг — 20–40 минут, можно идти пить чай):

```powershell
C:\vcpkg\vcpkg install --triplet x64-windows sdl2 sdl2-image sdl2-net sdl2-ttf physfs rapidjson libpng zlib openal-soft libvorbis libogg opengl
```

## Шаг 2. Клонировать и собрать Umbra

```powershell
cd C:\
git clone https://github.com/agent-carl/Barony umbra
cd umbra
git checkout claude/game-customization-graphics-t0ykbi

cmake -B build -S . `
    -DCMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake `
    -DFMOD_ENABLED=OFF `
    -DOPENAL_ENABLED=ON `
    -DSTEAMWORKS_ENABLED=0 `
    -DEOS_ENABLED=0 `
    -DPLAYFAB_ENABLED=0

cmake --build build --config Release -j
```

Результат: `C:\umbra\build\Release\umbra.exe`.

**Если конфигурация или сборка упала** — не бейся с ошибкой сам:
скопируй последние ~30 строк вывода и пришли мне. Известные кандидаты:
- `GL/glu.h not found` → в vcpkg-командe выше уже есть `opengl`; если не
  помогло — пришли лог.
- `dirent.h not found` → скачай https://github.com/tronkko/dirent
  (файл `include/dirent.h`) и положи в `C:\umbra\src\`.

## Шаг 3. Подготовить папку с игрой

Игре нужны ассеты Barony. Работаем на **копии**, оригинал не трогаем:

```powershell
# путь Steam-версии может отличаться - проверь в Steam: ПКМ по Barony ->
# Управление -> Посмотреть локальные файлы
Copy-Item -Recurse "C:\Program Files (x86)\Steam\steamapps\common\Barony" C:\umbra-play

Copy-Item C:\umbra\build\Release\umbra.exe C:\umbra-play\
Copy-Item C:\umbra\lang\en.txt C:\umbra-play\lang\ -Force
```

## Шаг 4. Запуск

```powershell
cd C:\umbra-play
.\umbra.exe
```

Признаки того, что запустился именно наш форк:
- Заголовок окна — **Project Umbra**.
- Сейвы пишутся отдельно от Barony (оригинал в безопасности).
- В `log.txt` строка `Project Umbra version: ... (Based on Barony ...)`.

---

## Чек-лист плейтеста (наши механики)

Новая одиночная игра, любой класс:

| # | Что проверить | Ожидание |
|---|---|---|
| 1 | Спавн | Рядом появляется компаньон **с лампой** (Briggs/Rosalind/Mordecai — зависит от твоего класса) |
| 2 | Приказы | Взаимодействие с компаньоном открывает колесо приказов (следуй/жди/атакуй) |
| 3 | Темнота | Постоять в тёмном углу: реплика спутника → шёпоты страха (25/50/75/90) → **виньетка** по краям экрана |
| 4 | Страх 90+ | Периодический урон (не убивает, минимум 1 HP) + **тряска камеры** |
| 5 | Тень | Догнать страх до 100 (`/dread_rise 20` ускорит): спавн охотника → замани под свет: «The light sears the shadow!», Тень **шарахается от света** → катарсис |
| 6 | Костёр | Найти костёр (в подземельях встречаются): «The fire's warmth pushes back the dark», страх тает втрое быстрее, Тень изгоняется |
| 7 | Факел | Держать факел в руке ~90 сек: сообщение об износе; 4 ступени → гаснет и снимается сам |
| 8 | Крепления | Снять факел со стены → остаётся тёмное крепление; взаимодействие с запасным факелом в рюкзаке **зажигает его заново** |
| 9 | Магия | На страхе 75+ заклинания бьют заметно сильнее (до +30% на пике) |
| 10 | Доверие | Побыть рядом со спутником ~3 мин: реплика о доверии («I'm glad it's you down here...») |
| 11 | Скорбь | Если спутник погиб: «The dark feels heavier now», страх растёт быстрее |
| 12 | Звук | Музыка и эффекты работают (OpenAL) |

## Живая настройка баланса

В игре нажми **Enter** (строка сообщений) и вводи команды с `/`:

```
/dread_rise 2            скорость роста страха в темноте (деф. 3)
/dread_fall_bright 8     спад у яркого света (деф. 5)
/dread_fall_dim 2        спад в сумраке (деф. 1)
/dread_light_dark 40     порог "темно" 0-255 (деф. 32)
/dread_light_bright 90   порог "светло" (деф. 96)
/stalker_spawn_dread 60  страх, на котором приходит Тень (деф. 100)
/stalker_sear_damage 30  урон Тени от света в сек (деф. 20)
/stalker_cooldown 30     пауза между Тенями, сек (деф. 90)
/torch_stage_seconds 30  секунд на ступень износа факела (деф. 90)
/lantern_stage_seconds 60  то же для лампы (деф. 240)
```

Записывай, какие значения ощущаются правильно — вобьём их как дефолты.

## Если что-то пошло не так

- **Игра упала / не стартует** → пришли целиком `C:\umbra-play\log.txt`.
- **Механика ведёт себя странно** → скриншот + что делал + что ожидал.
- **Просто впечатления** — это тоже данные: где скучно, где страшно,
  где непонятно. Баланс ставился по интуиции, твои ощущения — истина.
