# Сторонние материалы

| Материал | Автор и права | Где используется |
|---|---|---|
| Исходный русификатор (перевод, растровые шрифты `bigfont`/`smallfont01`, адаптированный `zerothre.ttf`) | **Siberian Studio**, 2018 ([siberian-studio.ru](http://siberian-studio.ru)) | `siberian_2018/`; в моде как основа перевода и шрифты |
| Шрифт Zero Threes (`zerothre.ttf`) | Ray Larabie, Larabie Fonts (freeware); кириллица — Siberian Studio | шрифт меню |
| Noto Sans ExtraCondensed Medium | Google, SIL Open Font License 1.1 | в мод попадает из игры с переназначенным `cmap` (субтитры) |
| Roboto Mono | Google, Apache License 2.0 | в мод попадает из игры с переназначенным `cmap` (консоль, копирайт) |
| Английский текст, остальные ресурсы игры | © Penguin Random House LLC, Nightdive Studios | в репозитории **не хранятся**; `build.py` берёт их из установленной игры |

Шрифты Noto Sans и Roboto Mono в моде изменены только переназначением таблицы символов: глифы не менялись.

Код в `tools/` и `installer/` распространяется на условиях [LICENSE](LICENSE).
