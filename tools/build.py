# -*- coding: utf-8 -*-
"""Сборка русификатора Siberian.kpf для Turok 2: Seeds of Evil Remastered 3.0.x (KEX Engine 2025).

Запуск (нужны Python 3.9+ и Pillow):
    python tools/build.py                       # путь к игре ищется в библиотеках Steam
    python tools/build.py --game "D:\\...\\Turok 2 - Seeds of Evil"

Результат: dist/Siberian.kpf  (кладётся в <папка игры>\\mods\\).

Из игры берутся только файлы, которые нельзя распространять в исходниках:
английский localization/loc_english.txt и шрифты NotoSans / RobotoMono (их cmap переназначается).

Как движок рисует текст (выяснено в ходе работы, подробности в docs/TECHNICAL_RU.md):
  * строки перед отрисовкой переводятся в CP-1252; всё, чего в ней нет, становится '?';
    исключение — строки копирайта (RobotoMono), они идут как Unicode;
  * поэтому кириллица хранится как байты cp1251, прочитанные как CP-1252 ('А' -> 0xC0 -> 'À'),
    как в русификаторе Siberian Studio 2018 года, а шрифты рисуют на этих местах русские буквы.

Что кладётся в мод:
  localization/loc_english.txt            перевод в «кодировке Siberian»
  fonts/bigfont, fonts/smallfont01        растровые шрифты Siberian: PNG -> RGBA, в .kfont добавлен nosdf
  ui/zerothre.ttf                         шрифт меню Siberian как есть
  fonts/NotoSans-ExtraCondensedMedium.ttf из игры, cmap переназначен
  fonts/Vera.ttf, AtkinsonHyperLegible    субтитры; кириллицы в них нет -> подменены переназначенным NotoSans
  fonts/RobotoMono-*.ttf                  консоль и копирайт, cmap переназначен
"""
import argparse, io, os, re, sys, zipfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from translations import TR, EXTRA
from ttfremap import remap

GAME_DIR_NAME = 'Turok 2 - Seeds of Evil'
UNICODE_KEYS = {'m_copyright1', 'm_copyright2'}   # рисуются RobotoMono через Unicode


# ---------------------------------------------------------------- поиск игры
def steam_libraries():
    roots = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'),
                          (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for name in ('SteamPath', 'InstallPath'):
                        try:
                            roots.append(winreg.QueryValueEx(k, name)[0])
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    libs = []
    for r in roots:
        r = os.path.normpath(r)
        libs.append(r)
        vdf = os.path.join(r, 'steamapps', 'libraryfolders.vdf')
        if os.path.isfile(vdf):
            for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='ignore').read()):
                libs.append(os.path.normpath(p.replace('\\\\', '\\')))
    seen, out = set(), []
    for l in libs:
        if l.lower() not in seen:
            seen.add(l.lower()); out.append(l)
    return out


def find_game():
    for lib in steam_libraries():
        p = os.path.join(lib, 'steamapps', 'common', GAME_DIR_NAME)
        if os.path.isfile(os.path.join(p, 'game.kpf')):
            return p
    return None


# ---------------------------------------------------------------- кодировка
def to_game(s):
    """Обычная кириллица -> «кодировка Siberian» (байты cp1251 как символы CP-1252)."""
    out = []
    for b in s.replace('\n', '\\n').encode('cp1251'):
        try:
            out.append(bytes([b]).decode('cp1252'))
        except UnicodeDecodeError:
            out.append(chr(b))
    return ''.join(out)


def from_old(s):
    """Старый перевод: символы U+0080..U+00FF были байтами cp1251 -> обычная кириллица."""
    out = []
    for ch in s:
        o = ord(ch)
        if 128 <= o <= 255:
            try:
                out.append(bytes([o]).decode('cp1251')); continue
            except UnicodeDecodeError:
                pass
        out.append(ch)
    return ''.join(out)


# ---------------------------------------------------------------- перевод
KV = re.compile(r'^(\s*)([A-Za-z_]\w*)((?:\s*<[^>]*>)?)(\s*=\s*)(".*")(\s*//.*)?\s*$')


def str_old_index(k):
    """Строки str_NNN 3.0 -> номер позиционной строки старого (2018) формата."""
    if k <= 101: return k
    if 119 <= k <= 212: return k - 17
    if 215 <= k <= 246: return k - 19
    return None   # 102..118, 213, 214 — новые в 3.0, в старом переводе их нет


def build_loc(new_lines, old_lines):
    oq = [to_game(from_old(l)) for l in old_lines if l.startswith('"')]
    oldkeys = {}
    for l in old_lines:
        m = KV.match(l)
        if m and not l.startswith('str_'):
            oldkeys[(m.group(2), m.group(3).strip())] = to_game(from_old(m.group(5)))

    tr = dict(TR)
    # vo_*_merged = склейка частей vo_*_1, vo_*_2, ... через пробел
    for l in new_lines:
        m = KV.match(l)
        if m and m.group(2).startswith('vo_') and m.group(2).endswith('_merged'):
            pre = m.group(2)[:-len('_merged')]
            parts = sorted((k for k in tr if re.fullmatch(re.escape(pre) + r'_\d+', k)),
                           key=lambda k: int(k.rsplit('_', 1)[1]))
            if parts:
                tr[m.group(2)] = ' '.join(tr[p] for p in parts)

    out, stat, untr = [], {'old': 0, 'tr': 0, 'en': 0}, []
    for l in new_lines:
        m = KV.match(l)
        if not m:
            out.append(l); continue
        ind, key, tag, eq, val, tail = m.groups(); tail = tail or ''
        nv = None
        sm = re.fullmatch(r'str_(\d+)', key)
        if key in tr:
            txt = tr[key].replace('\n', '\\n') if key in UNICODE_KEYS else to_game(tr[key])
            nv = '"' + txt + '"'; stat['tr'] += 1
        elif sm:
            i = str_old_index(int(sm.group(1)))
            if i is not None and i < len(oq):
                nv = oq[i]; stat['old'] += 1
        elif (key, tag.strip()) in oldkeys:
            nv = oldkeys[(key, tag.strip())]; stat['old'] += 1
        if nv is None:
            stat['en'] += 1; untr.append(key); nv = val
        out.append(f'{ind}{key}{tag}{eq}{nv}{tail}')
    out.append('')
    out.append('// Keys referenced by achievements.json but missing in 3.0 loc_english.txt (added by translation)')
    for k, v in EXTRA.items():
        out.append(f'{k} = "{to_game(v)}"')
    return '\r\n'.join(out) + '\r\n', stat, untr     # UTF-8 без BOM, как в оригинале


# ---------------------------------------------------------------- шрифты
def kfont(path):
    t = open(path, 'rb').read().decode('latin-1')
    t = t[t.index('filter linear'):]          # убрать BOM и шапку-комментарий
    t = re.sub(r'//.*', '', t)                # комментарии с «мусорными» символами не нужны
    t = re.sub(r'[ \t]+\r?\n', '\n', t).replace('\r\n', '\n')
    t = t.replace('filter linear', 'filter linear\nnosdf', 1)   # атлас обычный, не SDF
    return t.replace('\n', '\r\n')


def png_rgba(path):
    im = Image.open(path).convert('L')
    rgba = Image.merge('RGBA', [Image.new('L', im.size, 255)] * 3 + [im])
    b = io.BytesIO(); rgba.save(b, 'PNG'); return b.getvalue()


# ---------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--game', help='папка игры (где лежит game.kpf); по умолчанию ищется в Steam')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist', 'Siberian.kpf'))
    a = ap.parse_args()
    game = a.game or find_game()
    if not game or not os.path.isfile(os.path.join(game, 'game.kpf')):
        sys.exit('Не найдена игра. Укажите папку: --game "путь к Turok 2 - Seeds of Evil"')
    print('Игра:', game)
    g = zipfile.ZipFile(os.path.join(game, 'game.kpf'))
    sib = os.path.join(ROOT, 'siberian_2018')

    new_lines = g.read('localization/loc_english.txt').decode('utf-8-sig').splitlines()
    old_lines = open(os.path.join(sib, 'localization', 'loc_english.txt'), 'rb').read().decode('utf-8-sig').splitlines()
    loc, stat, untr = build_loc(new_lines, old_lines)
    print('Строк: из перевода Siberian', stat['old'], '| новых переводов', stat['tr'], '| оставлено на английском', stat['en'])
    if untr:
        print('  на английском:', ', '.join(untr))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if os.path.exists(a.out):
        os.remove(a.out)
    with zipfile.ZipFile(a.out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('localization/loc_english.txt', loc.encode('utf-8'))
        for n in ('bigfont', 'smallfont01'):
            z.writestr(f'fonts/{n}.kfont', kfont(os.path.join(sib, 'fonts', f'{n}.kfont')).encode('utf-8'))
            z.writestr(f'fonts/{n}.png', png_rgba(os.path.join(sib, 'fonts', f'{n}.png')))
        # шрифт меню Siberian: у zerothre.ttf игры кириллица есть только в cmap, глифы пустые
        z.write(os.path.join(sib, 'ui', 'zerothre.ttf'), 'ui/zerothre.ttf')
        noto, _ = remap(g.read('fonts/NotoSans-ExtraCondensedMedium.ttf'))
        z.writestr('fonts/NotoSans-ExtraCondensedMedium.ttf', noto)
        # субтитры рисуются Vera / Atkinson — кириллицы в них нет, подменяем NotoSans
        z.writestr('fonts/Vera.ttf', noto)
        z.writestr('fonts/AtkinsonHyperLegible-Regular.otf', noto)
        for n in sorted(g.namelist()):
            if n.startswith('fonts/RobotoMono-') and n.endswith('.ttf'):
                z.writestr(n, remap(g.read(n))[0])
    print('Готово:', a.out, os.path.getsize(a.out), 'байт')


if __name__ == '__main__':
    main()
