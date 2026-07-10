# Project Umbra — сборка и запуск на Windows

> ⚠️ Черновик: путь составлен по CMakeLists и INSTALL.md апстрима, но на
> живой Windows-машине нами ещё не прогонялся. При первом тесте пройдём
> вместе и поправим этот документ по факту.

## Что понадобится

1. **Visual Studio 2022** (Community подойдёт) с workload
   «Разработка классических приложений на C++» (включает CMake).
2. **Git**.
3. **vcpkg** — менеджер C++-зависимостей от Microsoft.
4. **Купленная Barony в Steam** (установленная) — источник ассетов для
   dev-запуска.

## Шаг 1: vcpkg и зависимости

В PowerShell:

```powershell
git clone https://github.com/microsoft/vcpkg C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat

# зависимости нашего форка (OpenAL-стек, без FMOD)
C:\vcpkg\vcpkg install --triplet x64-windows `
    sdl2 sdl2-image sdl2-net sdl2-ttf `
    physfs rapidjson libpng zlib `
    openal-soft libvorbis libogg
```

Это долгий шаг (сборка библиотек), делается один раз.

## Шаг 2: клонировать и собрать Umbra

```powershell
git clone https://github.com/agent-carl/Barony umbra
cd umbra
git checkout claude/game-customization-graphics-t0ykbi

cmake -B build -S . `
    -DCMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake `
    -DCMAKE_BUILD_TYPE=Release `
    -DFMOD_ENABLED=OFF `
    -DOPENAL_ENABLED=ON `
    -DSTEAMWORKS_ENABLED=0 `
    -DEOS_ENABLED=0 `
    -DPLAYFAB_ENABLED=0

cmake --build build --config Release -j
```

Результат: `build\Release\umbra.exe` (и `editor.exe`).

Известные грабли, которые могут встретиться (чиним по факту):
- `GL/glu.h` не найден — на Windows GLU идёт с Windows SDK; если нет,
  ставится через vcpkg `opengl`/`freeglut`.
- `dirent.h` не найден — POSIX-заголовок; порт: https://github.com/tronkko/dirent
  (положить в include-путь). CMake апстрима про это знает для VS-проектов,
  для чистого CMake может понадобиться руками.

## Шаг 3: запуск с ассетами Barony

Игре нужны данные (модели/спрайты/звук) из твоей Steam-копии.
Обычный путь Steam-версии:
`C:\Program Files (x86)\Steam\steamapps\common\Barony`

Самый простой dev-способ — запуск из папки с ассетами:

```powershell
# скопировать бинарь к ассетам (НЕ в сам Steam-каталог! сделай копию)
Copy-Item -Recurse "C:\Program Files (x86)\Steam\steamapps\common\Barony" D:\umbra-data
Copy-Item build\Release\umbra.exe D:\umbra-data\
Copy-Item lang\en.txt D:\umbra-data\lang\ -Force
cd D:\umbra-data
.\umbra.exe
```

Копия каталога важна: наш форк не должен трогать установку Barony
(сейвы у нас и так разведены — Umbra пишет в свою папку).

## Шаг 4: что проверять (чек-лист первого запуска)

1. Окно называется **Project Umbra**, в логе — «Project Umbra version...
   (Based on Barony...)».
2. Новая одиночная игра → рядом спавнится **Альберт с лампой**, ему можно
   отдавать приказы (взаимодействие с ним).
3. Постоять в темноте: реплика Альберта про тьму → шёпоты страха
   (25/50/75/90) → **виньетка по краям экрана** темнеет.
4. Дать страху дойти до 100 → **Тень-охотник**; заманить под свет —
   «The light sears the shadow!» → катарсис.
5. Факел в руке **догорает** (~6 минут: сообщения об износе, потом гаснет).
6. Звук работает (OpenAL): музыка/эффекты.
7. Заклинания при страхе 75+ бьют заметно сильнее.

## Отчёт о проблемах

Лог игры: `%USERPROFILE%\.umbra\log.txt` (или рядом с exe — `log.txt`).
При падении/странностях — прислать его целиком.
