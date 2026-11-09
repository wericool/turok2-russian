# -*- coding: utf-8 -*-
"""Сводный словарь переводов: ключ loc_english.txt -> русский текст (обычная кириллица).

Ключи vo_*_merged (склейка реплик субтитров) build.py собирает автоматически.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translations_ui import TR as _ui        # меню, настройки, мультиплеер, достижения
from translations_vo import TR as _vo        # новые str_, галерея, субтитры (часть 1)
from translations_vo2 import TR as _vo2      # субтитры (часть 2)
from translations_desc import TR as _desc, EXTRA   # подсказки к настройкам; недостающие ключи игры

TR = {}
for d in (_ui, _vo, _vo2, _desc):
    TR.update(d)
