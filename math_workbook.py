# -*- coding: utf-8 -*-
import random
import tkinter as tk
import json
import os
import sys
import math
import re
import threading
import subprocess
import tempfile
import shutil
import urllib.request
from math import gcd
from datetime import datetime
from collections import deque

BG = "#eaf6ff"
CARD = "#ffffff"
PRIMARY = "#3b82c4"
PRIMARY_DARK = "#2c6595"
ACCENT = "#ffb703"
ACCENT_DARK = "#e29500"
GREEN = "#2ecc71"
GREEN_DARK = "#219150"
RED = "#e74c3c"
TEXT = "#26333a"
MUTED = "#6b7c85"
DISABLED = "#c9d3d8"
DISABLED_TEXT = "#8fa0a8"

# 도형 다이어그램에서 치수를 표시할 때 쓰는 색 (변/도형 종류가 아니라 "무엇을 재는 값인지"로 통일)
DIM_A = "#e0692a"   # 가로형 길이: 가로, 밑변, 윗변, 아랫변, 지름, 한 변, 한 대각선
DIM_B = "#1f9d63"   # 세로형 길이: 세로, 높이, 반지름, 다른 대각선
DIM_C = "#7c5cd6"   # 직육면체처럼 세 번째 치수가 더 필요할 때: 높이
OUTLINE_NEUTRAL = "#aeb9be"  # 치수로 표시되지 않는 나머지 변(그냥 도형의 모양)

FONT_NAME = "맑은 고딕"

APP_VERSION = "v1.1"

# 새 버전을 낼 때는 맨 위에 새 항목을 추가한다 (최신순으로 보여줌).
VERSION_HISTORY = [
    {
        "version": "v1.1",
        "date": "2026-08-03",
        "notes": [
            "시계 읽기 화면을 더 크고 보기 편하게 개선 (5분 단위 눈금 숫자 추가)",
            "일부 문제 문구·계산 오류 수정",
        ],
    },
    {
        "version": "v1.0",
        "date": "2026-08-02",
        "notes": [
            "사칙연산(덧셈·뺄셈·곱셈·나눗셈), 설정(숫자 연습), 시험, 오답노트, 기록 기능 출시",
            "도형(둘레·넓이·부피) 공식과 문제풀이, 원의 파이(π) 단위 지원",
            "분수·소수 사칙연산 추가",
            "문장제, 약수와 배수(최대공약수·최소공배수), 측정(단위 변환·시계 읽기) 카테고리 추가",
        ],
    },
]

# Digits the user has chosen to drill in 설정 (settings). Numbers containing
# any of these digits are drawn roughly BOOST_FACTOR times more often.
BOOSTED_DIGITS = set()
BOOST_FACTOR = 5


def _weighted_int(lo, hi):
    while True:
        n = random.randint(lo, hi)
        if not BOOSTED_DIGITS:
            return n
        if any(d in str(n) for d in BOOSTED_DIGITS):
            return n
        if random.random() < 1.0 / BOOST_FACTOR:
            return n


def _has_batchim(word):
    """True if the last syllable of `word` ends with a 받침 (final consonant)."""
    code = ord(word[-1]) - 0xAC00
    if 0 <= code <= 11171:
        return code % 28 != 0
    return False


def _josa(word, with_batchim, without_batchim):
    """Picks the correct particle form (예: 이/가, 을/를, 은/는) for `word`."""
    return with_batchim if _has_batchim(word) else without_batchim

ADD_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수 + 한 자리 수", "example": "예) 3 + 5"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 + 한 자리 (받아올림 없음)", "example": "예) 23 + 5"},
    {"level": 3, "title": "Lv.3", "desc": "두 자리 + 두 자리 (받아올림 없음)", "example": "예) 23 + 45"},
    {"level": 4, "title": "Lv.4", "desc": "두 자리 + 두 자리 (받아올림 있음)", "example": "예) 27 + 38"},
    {"level": 5, "title": "Lv.5", "desc": "두~세 자리 수 + 두~세 자리 수", "example": "예) 128 + 456"},
]

SUB_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수 - 한 자리 수", "example": "예) 8 - 3"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 - 한 자리 (받아내림 없음)", "example": "예) 28 - 5"},
    {"level": 3, "title": "Lv.3", "desc": "두 자리 - 두 자리 (받아내림 없음)", "example": "예) 58 - 23"},
    {"level": 4, "title": "Lv.4", "desc": "두 자리 - 두 자리 (받아내림 있음)", "example": "예) 42 - 17"},
    {"level": 5, "title": "Lv.5", "desc": "두~세 자리 수 - 두~세 자리 수", "example": "예) 456 - 128"},
]

MUL_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수 × 한 자리 수", "example": "예) 4 × 7"},
    {"level": 2, "title": "Lv.2", "desc": "한 자리 수 × 두 자리 수", "example": "예) 6 × 34"},
    {"level": 3, "title": "Lv.3", "desc": "두 자리 수 × 두 자리 수", "example": "예) 27 × 53"},
]

DIV_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수 ÷ 한 자리 수", "example": "예) 7 ÷ 3 = 7/3"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 수 ÷ 한 자리 수", "example": "예) 47 ÷ 6 = 47/6"},
    {"level": 3, "title": "Lv.3", "desc": "두 자리 수 ÷ 두 자리 수", "example": "예) 84 ÷ 23 = 84/23"},
]


def gen_addition(level):
    if level == 1:
        a, b = _weighted_int(1, 9), _weighted_int(1, 9)
    elif level == 2:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(1, 9)
            if a % 10 + b <= 9:
                break
    elif level == 3:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(10, 99)
            if a % 10 + b % 10 <= 9:
                break
    elif level == 4:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(10, 99)
            if a % 10 + b % 10 >= 10:
                break
    else:
        a, b = _weighted_int(10, 999), _weighted_int(10, 999)
    return a, b, a + b


def gen_subtraction(level):
    if level == 1:
        while True:
            a, b = _weighted_int(1, 9), _weighted_int(1, 9)
            if a >= b:
                break
    elif level == 2:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(1, 9)
            if a % 10 >= b:
                break
    elif level == 3:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(10, 99)
            if a >= b and a % 10 >= b % 10:
                break
    elif level == 4:
        while True:
            a, b = _weighted_int(10, 99), _weighted_int(10, 99)
            if a >= b and a % 10 < b % 10:
                break
    else:
        while True:
            a, b = _weighted_int(10, 999), _weighted_int(10, 999)
            if a >= b:
                break
    return a, b, a - b


def gen_multiplication(level):
    if level == 1:
        a, b = _weighted_int(1, 9), _weighted_int(1, 9)
    elif level == 2:
        one, two = _weighted_int(1, 9), _weighted_int(10, 99)
        a, b = (one, two) if random.random() < 0.5 else (two, one)
    else:
        a, b = _weighted_int(10, 99), _weighted_int(10, 99)
    return a, b, a * b


def gen_division(level):
    """Returns (a, b, num, den) where a/b reduced to lowest terms is num/den.
    a and b are unconstrained, so most problems won't divide evenly and the
    answer is a proper/improper fraction; den == 1 on the rare exact division."""
    if level == 1:
        a, b = _weighted_int(1, 9), _weighted_int(1, 9)
    elif level == 2:
        a, b = _weighted_int(10, 99), _weighted_int(1, 9)
    else:
        a, b = _weighted_int(10, 99), _weighted_int(10, 99)
    g = gcd(a, b)
    return a, b, a // g, b // g


# ---------------------------------------------------------------------------
# 분수 덧셈/뺄셈 (진분수만 다룸 -- 대분수는 범위 밖)
# gen 함수는 (n1, d1, n2, d2, 정답분자, 정답분모) 6-tuple을 돌려준다.
# ---------------------------------------------------------------------------
FRAC_ADD_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "분모가 같은 진분수의 덧셈", "example": "예) 1/5 + 2/5"},
    {"level": 2, "title": "Lv.2", "desc": "분모가 다른 진분수의 덧셈", "example": "예) 1/3 + 1/4"},
]
FRAC_SUB_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "분모가 같은 진분수의 뺄셈", "example": "예) 4/5 - 2/5"},
    {"level": 2, "title": "Lv.2", "desc": "분모가 다른 진분수의 뺄셈", "example": "예) 3/4 - 1/3"},
]


def gen_frac_add(level):
    if level == 1:
        d = _weighted_int(2, 12)
        n1, n2 = _weighted_int(1, d - 1), _weighted_int(1, d - 1)
        d1 = d2 = d
    else:
        d1 = _weighted_int(2, 10)
        d2 = _weighted_int(2, 10)
        while d2 == d1:
            d2 = _weighted_int(2, 10)
        n1, n2 = _weighted_int(1, d1 - 1), _weighted_int(1, d2 - 1)
    num, den = n1 * d2 + n2 * d1, d1 * d2
    g = gcd(num, den)
    return n1, d1, n2, d2, num // g, den // g


def gen_frac_sub(level):
    if level == 1:
        d = _weighted_int(3, 12)  # d>=3 so a numerator pair with n1>n2>=1 exists
        n1 = _weighted_int(2, d - 1)
        n2 = _weighted_int(1, n1 - 1)
        d1 = d2 = d
    else:
        d1 = _weighted_int(2, 10)
        d2 = _weighted_int(2, 10)
        while d2 == d1:
            d2 = _weighted_int(2, 10)
        while True:
            n1, n2 = _weighted_int(1, d1 - 1), _weighted_int(1, d2 - 1)
            if n1 * d2 > n2 * d1:  # n1/d1 > n2/d2 이어야 결과가 양수
                break
    num, den = n1 * d2 - n2 * d1, d1 * d2
    g = gcd(num, den)
    return n1, d1, n2, d2, num // g, den // g


FRAC_MUL_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "진분수 × 자연수", "example": "예) 2/5 × 3"},
    {"level": 2, "title": "Lv.2", "desc": "진분수 × 진분수", "example": "예) 2/3 × 3/4"},
]
FRAC_DIV_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "진분수 ÷ 자연수", "example": "예) 2/3 ÷ 4"},
    {"level": 2, "title": "Lv.2", "desc": "진분수 ÷ 진분수", "example": "예) 2/3 ÷ 4/5"},
]


def gen_frac_mul(level):
    if level == 1:
        d1 = _weighted_int(2, 10)
        n1 = _weighted_int(1, d1 - 1)
        n2, d2 = _weighted_int(2, 9), 1  # 자연수를 분모 1인 "분수"로 취급
    else:
        d1 = _weighted_int(2, 10)
        n1 = _weighted_int(1, d1 - 1)
        d2 = _weighted_int(2, 10)
        n2 = _weighted_int(1, d2 - 1)
    num, den = n1 * n2, d1 * d2
    g = gcd(num, den)
    return n1, d1, n2, d2, num // g, den // g


def gen_frac_div(level):
    if level == 1:
        d1 = _weighted_int(2, 10)
        n1 = _weighted_int(1, d1 - 1)
        n2, d2 = _weighted_int(2, 9), 1  # 진분수 ÷ 자연수
    else:
        d1 = _weighted_int(2, 10)
        n1 = _weighted_int(1, d1 - 1)
        d2 = _weighted_int(2, 10)
        n2 = _weighted_int(1, d2 - 1)
    # n1/d1 ÷ n2/d2 = n1/d1 × d2/n2
    num, den = n1 * d2, d1 * n2
    g = gcd(num, den)
    return n1, d1, n2, d2, num // g, den // g


FRAC_LABELS = {"frac_add": "분수 덧셈", "frac_sub": "분수 뺄셈", "frac_mul": "분수 곱셈", "frac_div": "분수 나눗셈"}
FRAC_SYMBOL = {"frac_add": "+", "frac_sub": "−", "frac_mul": "×", "frac_div": "÷"}
FRAC_GEN = {"frac_add": gen_frac_add, "frac_sub": gen_frac_sub, "frac_mul": gen_frac_mul, "frac_div": gen_frac_div}
FRAC_LEVELS_MAP = {"frac_add": FRAC_ADD_LEVELS, "frac_sub": FRAC_SUB_LEVELS,
                    "frac_mul": FRAC_MUL_LEVELS, "frac_div": FRAC_DIV_LEVELS}


# ---------------------------------------------------------------------------
# 소수 사칙연산 -- 기존 PracticePage의 (a, b, answer) 형태를 그대로 쓰되
# 소수로 채점한다 (오차 허용 비교).
# ---------------------------------------------------------------------------
DEC_ADD_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "소수 첫째 자리 덧셈", "example": "예) 2.3 + 1.5"},
    {"level": 2, "title": "Lv.2", "desc": "소수 둘째 자리까지 덧셈", "example": "예) 3.45 + 1.2"},
]
DEC_SUB_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "소수 첫째 자리 뺄셈", "example": "예) 4.8 - 1.5"},
    {"level": 2, "title": "Lv.2", "desc": "소수 둘째 자리까지 뺄셈", "example": "예) 5.45 - 1.2"},
]
DEC_MUL_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "소수 × 자연수", "example": "예) 2.5 × 3"},
    {"level": 2, "title": "Lv.2", "desc": "소수 × 소수", "example": "예) 1.5 × 2.4"},
]
DEC_DIV_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "소수 ÷ 자연수 (나누어떨어지는 경우)", "example": "예) 4.8 ÷ 4"},
]


def gen_dec_add(level):
    places = 1 if level == 1 else 2
    scale = 10 ** places
    a = _weighted_int(1, 9 * scale) / scale
    b = _weighted_int(1, 9 * scale) / scale
    return round(a, places), round(b, places), round(a + b, places)


def gen_dec_sub(level):
    places = 1 if level == 1 else 2
    scale = 10 ** places
    while True:
        ai, bi = _weighted_int(1, 9 * scale), _weighted_int(1, 9 * scale)
        if ai >= bi:
            break
    a, b = ai / scale, bi / scale
    return round(a, places), round(b, places), round(a - b, places)


def gen_dec_mul(level):
    if level == 1:
        a = round(_weighted_int(1, 99) / 10, 1)
        b = _weighted_int(2, 9)
        return a, b, round(a * b, 2)
    a = round(_weighted_int(1, 99) / 10, 1)
    b = round(_weighted_int(1, 99) / 10, 1)
    return a, b, round(a * b, 2)


def gen_dec_div(level):
    b = _weighted_int(2, 9)
    ans = round(_weighted_int(1, 50) / 10, 1)
    a = round(ans * b, 2)
    return a, b, ans


DEC_LABELS = {"dec_add": "소수 덧셈", "dec_sub": "소수 뺄셈", "dec_mul": "소수 곱셈", "dec_div": "소수 나눗셈"}
DEC_SYMBOL = {"dec_add": "+", "dec_sub": "−", "dec_mul": "×", "dec_div": "÷"}
DEC_GEN = {"dec_add": gen_dec_add, "dec_sub": gen_dec_sub, "dec_mul": gen_dec_mul, "dec_div": gen_dec_div}
DEC_LEVELS_MAP = {"dec_add": DEC_ADD_LEVELS, "dec_sub": DEC_SUB_LEVELS,
                   "dec_mul": DEC_MUL_LEVELS, "dec_div": DEC_DIV_LEVELS}


# ---------------------------------------------------------------------------
# 문장제: 덧셈/뺄셈/곱셈/나눗셈을 자연스러운 한국어 문장으로 묻는다.
# gen 함수는 (문제 문장, 정답) 튜플을 돌려준다 (PracticePage의 "text_int" 모드).
# ---------------------------------------------------------------------------
WORD_ITEMS = [
    ("사과", "개"), ("귤", "개"), ("배", "개"), ("연필", "자루"), ("공책", "권"),
    ("구슬", "개"), ("붕어빵", "개"), ("풍선", "개"), ("색종이", "장"), ("스티커", "장"),
    ("축구공", "개"), ("사탕", "개"), ("초콜릿", "개"), ("책", "권"), ("장미", "송이"),
]
WORD_NAMES = ["민준", "서연", "지훈", "하윤", "도윤", "예은", "시우", "수아", "준서", "다은"]

WORD_ADD_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수로 더하기", "example": "예) 사탕 3개와 5개"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 수로 더하기", "example": "예) 사탕 23개와 15개"},
    {"level": 3, "title": "Lv.3", "desc": "큰 수로 더하기", "example": "예) 사탕 120개와 85개"},
]
WORD_SUB_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수로 빼기", "example": "예) 사탕 8개 중 3개"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 수로 빼기", "example": "예) 사탕 45개 중 23개"},
    {"level": 3, "title": "Lv.3", "desc": "큰 수로 빼기", "example": "예) 사탕 250개 중 120개"},
]
WORD_MUL_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "한 자리 수끼리 곱하기", "example": "예) 한 상자에 4개씩 3상자"},
    {"level": 2, "title": "Lv.2", "desc": "한 자리 × 두 자리", "example": "예) 한 상자에 6개씩 15상자"},
    {"level": 3, "title": "Lv.3", "desc": "두 자리끼리 곱하기", "example": "예) 한 상자에 12개씩 18상자"},
]
WORD_DIV_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "작은 수로 똑같이 나누기", "example": "예) 18개를 3명에게"},
    {"level": 2, "title": "Lv.2", "desc": "두 자리 수로 나누기", "example": "예) 180개를 6명에게"},
    {"level": 3, "title": "Lv.3", "desc": "여러 묶음으로 나누기", "example": "예) 400개를 16상자에"},
]


def gen_word_add(level):
    lo, hi = {1: (2, 9), 2: (10, 50)}.get(level, (50, 300))
    a, b = _weighted_int(lo, hi), _weighted_int(lo, hi)
    item, counter = random.choice(WORD_ITEMS)
    name = random.choice(WORD_NAMES)
    variant = random.randint(0, 2)
    if variant == 0:
        text = (f"{name}{_josa(name, '은', '는')} {item}{_josa(item, '을', '를')} {a}{counter} 가지고 있었는데, "
                f"{b}{counter}{_josa(counter, '을', '를')} 더 받았습니다. "
                f"{name}{_josa(name, '이', '가')} 지금 가진 {item}{_josa(item, '은', '는')} 모두 몇 {counter}일까요?")
    elif variant == 1:
        text = (f"바구니에 {item}{_josa(item, '이', '가')} {a}{counter} 있었는데 "
                f"{b}{counter}{_josa(counter, '을', '를')} 더 담았습니다. "
                f"바구니에 있는 {item}{_josa(item, '은', '는')} 모두 몇 {counter}일까요?")
    else:
        text = (f"{name}{_josa(name, '은', '는')} 어제 {item} {a}{counter}, 오늘 {item} {b}{counter}"
                f"{_josa(counter, '을', '를')} 모았습니다. "
                f"{name}{_josa(name, '이', '가')} 모은 {item}{_josa(item, '은', '는')} 모두 몇 {counter}일까요?")
    return text, a + b


def gen_word_sub(level):
    lo, hi = {1: (2, 9), 2: (10, 50)}.get(level, (50, 300))
    while True:
        a, b = _weighted_int(lo, hi), _weighted_int(lo, hi)
        if a >= b:
            break
    item, counter = random.choice(WORD_ITEMS)
    name = random.choice(WORD_NAMES)
    variant = random.randint(0, 2)
    if variant == 0:
        text = (f"{name}{_josa(name, '은', '는')} {item} {a}{counter}{_josa(counter, '을', '를')} 가지고 있었습니다. "
                f"그중 {b}{counter}{_josa(counter, '을', '를')} 친구에게 주었습니다. "
                f"{name}{_josa(name, '이', '가')} 남은 {item}{_josa(item, '은', '는')} 몇 {counter}일까요?")
    elif variant == 1:
        text = (f"가게에 {item}{_josa(item, '이', '가')} {a}{counter} 있었는데 {b}{counter}{_josa(counter, '이', '가')} 팔렸습니다. "
                f"가게에 남은 {item}{_josa(item, '은', '는')} 몇 {counter}일까요?")
    else:
        text = (f"{item} {a}{counter} 중에서 {b}{counter}{_josa(counter, '을', '를')} 사용했습니다. "
                f"남은 {item}{_josa(item, '은', '는')} 몇 {counter}일까요?")
    return text, a - b


def gen_word_mul(level):
    a_lo, a_hi, b_lo, b_hi = {1: (2, 9, 2, 9), 2: (2, 9, 10, 30)}.get(level, (10, 30, 10, 30))
    a, b = _weighted_int(a_lo, a_hi), _weighted_int(b_lo, b_hi)
    item, counter = random.choice(WORD_ITEMS)
    group = random.choice(["상자", "봉지", "바구니", "묶음"])
    name = random.choice(WORD_NAMES)
    if random.random() < 0.5:
        text = (f"한 {group}에 {item}{_josa(item, '이', '가')} {a}{counter}씩 들어 있습니다. "
                f"{b}{group}에는 {item}{_josa(item, '이', '가')} 모두 몇 {counter} 들어 있을까요?")
    else:
        text = (f"{name}{_josa(name, '은', '는')} {item}{_josa(item, '을', '를')} 한 {group}에 {a}{counter}씩 담아서 "
                f"{b}{group}{_josa(group, '을', '를')} 만들었습니다. "
                f"{name}{_josa(name, '이', '가')} 담은 {item}{_josa(item, '은', '는')} 모두 몇 {counter}일까요?")
    return text, a * b


def gen_word_div(level):
    n_lo, n_hi, q_lo, q_hi = {1: (2, 9, 1, 9), 2: (2, 9, 10, 30)}.get(level, (2, 20, 10, 50))
    n, q = _weighted_int(n_lo, n_hi), _weighted_int(q_lo, q_hi)
    total = n * q
    item, counter = random.choice(WORD_ITEMS)
    if random.random() < 0.5:
        text = (f"{item} {total}{counter}{_josa(counter, '을', '를')} {n}명에게 똑같이 나누어 주려고 합니다. "
                f"한 명은 {item}{_josa(item, '을', '를')} 몇 {counter}씩 받을 수 있을까요?")
    else:
        text = (f"{item} {total}{counter}{_josa(counter, '을', '를')} {n}상자에 똑같이 나누어 담으려고 합니다. "
                f"한 상자에는 {item}{_josa(item, '을', '를')} 몇 {counter}씩 담을 수 있을까요?")
    return text, q


WORD_LABELS = {"word_add": "덧셈 문장제", "word_sub": "뺄셈 문장제", "word_mul": "곱셈 문장제", "word_div": "나눗셈 문장제"}
WORD_GEN = {"word_add": gen_word_add, "word_sub": gen_word_sub, "word_mul": gen_word_mul, "word_div": gen_word_div}
WORD_LEVELS_MAP = {"word_add": WORD_ADD_LEVELS, "word_sub": WORD_SUB_LEVELS,
                    "word_mul": WORD_MUL_LEVELS, "word_div": WORD_DIV_LEVELS}


# ---------------------------------------------------------------------------
# 약수와 배수: 최대공약수(gcd) / 최소공배수(lcm) 구하기 ("text_int" 모드)
# ---------------------------------------------------------------------------
GCD_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "30 이하의 두 수", "example": "예) 12와 18의 최대공약수"},
    {"level": 2, "title": "Lv.2", "desc": "100 이하의 두 수", "example": "예) 48과 72의 최대공약수"},
]
LCM_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "12 이하의 두 수", "example": "예) 4와 6의 최소공배수"},
    {"level": 2, "title": "Lv.2", "desc": "24 이하의 두 수", "example": "예) 8과 18의 최소공배수"},
]


def _num_josa(n, with_batchim, without_batchim):
    """Particle for a number read aloud in Sino-Korean (e.g. 24='이십사' -> no
    batchim -> 와; 26='이십육' -> batchim -> 과). Numbers ending in 0 are read
    ending in a batchim syllable (십/백/...), so they take with_batchim too."""
    last = n % 10
    return with_batchim if last in (0, 1, 3, 6, 7, 8) else without_batchim


def _num_josa_ro(n):
    """으로/로 particle for a number read aloud in Sino-Korean. Unlike 과/와
    or 은/는, ㄹ-batchim syllables (1='일', 7='칠', 8='팔') take 로 just like
    no-batchim syllables -- only 0/3/6 ('영'/'삼'/'육') take 으로."""
    last = n % 10
    return "으로" if last in (0, 3, 6) else "로"


def gen_gcd(level):
    """Builds a, b as multiples of a shared factor g (a=g*m1, b=g*m2) so the
    answer is almost always a meaningful common factor -- picking a, b fully
    independently made the answer 1 (coprime) more than half the time, which
    made the exercise trivial/boring rather than testing GCD-finding."""
    cap, g_lo, g_hi = (30, 2, 9) if level == 1 else (100, 2, 20)
    while True:
        g = _weighted_int(g_lo, g_hi)
        max_m = cap // g
        if max_m < 2:
            continue
        m1, m2 = _weighted_int(1, max_m), _weighted_int(1, max_m)
        if m1 != m2:
            break
    a, b = g * m1, g * m2
    text = f"{a}{_num_josa(a, '과', '와')} {b}의 최대공약수를 구하세요."
    return text, gcd(a, b)


def gen_lcm(level):
    lo, hi = (2, 12) if level == 1 else (4, 24)
    while True:
        a, b = _weighted_int(lo, hi), _weighted_int(lo, hi)
        if a == b:
            continue
        ans = a * b // gcd(a, b)
        if ans <= 300:
            break
    text = f"{a}{_num_josa(a, '과', '와')} {b}의 최소공배수를 구하세요."
    return text, ans


NUM_LABELS = {"gcd": "최대공약수", "lcm": "최소공배수"}
NUM_GEN = {"gcd": gen_gcd, "lcm": gen_lcm}
NUM_LEVELS_MAP = {"gcd": GCD_LEVELS, "lcm": LCM_LEVELS}


# ---------------------------------------------------------------------------
# 측정: 길이/무게/들이 단위 변환("text_decimal" 모드)과 시계 읽기("clock" 모드)
# ---------------------------------------------------------------------------
UNIT_LENGTH_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "mm ↔ cm", "example": "예) 5cm는 몇 mm?"},
    {"level": 2, "title": "Lv.2", "desc": "cm ↔ m", "example": "예) 230cm는 몇 m?"},
    {"level": 3, "title": "Lv.3", "desc": "m ↔ km", "example": "예) 2500m는 몇 km?"},
]
UNIT_WEIGHT_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "g ↔ kg (자연수)", "example": "예) 3kg는 몇 g?"},
    {"level": 2, "title": "Lv.2", "desc": "g ↔ kg (소수)", "example": "예) 2300g는 몇 kg?"},
]
UNIT_VOLUME_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "mL ↔ L (자연수)", "example": "예) 2L는 몇 mL?"},
    {"level": 2, "title": "Lv.2", "desc": "mL ↔ L (소수)", "example": "예) 1500mL는 몇 L?"},
]
CLOCK_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "정각과 30분", "example": "예) 3시, 3시 30분"},
    {"level": 2, "title": "Lv.2", "desc": "5분 단위", "example": "예) 3시 25분, 7시 40분"},
    {"level": 3, "title": "Lv.3", "desc": "1분 단위", "example": "예) 3시 47분, 9시 12분"},
]


def gen_unit_length(level):
    if level == 1:
        if random.random() < 0.5:
            cm = _weighted_int(1, 30)
            return f"{cm}cm는 몇 mm일까요?", cm * 10
        mm = _weighted_int(1, 30) * 10
        return f"{mm}mm는 몇 cm일까요?", mm // 10
    elif level == 2:
        if random.random() < 0.5:
            m = _weighted_int(1, 20)
            return f"{m}m는 몇 cm일까요?", m * 100
        cm = _weighted_int(1, 50) * 10
        return f"{cm}cm는 몇 m일까요?", round(cm / 100, 2)
    else:
        if random.random() < 0.5:
            km = _weighted_int(1, 10)
            return f"{km}km는 몇 m일까요?", km * 1000
        m = _weighted_int(1, 20) * 100
        return f"{m}m는 몇 km일까요?", round(m / 1000, 2)


def gen_unit_weight(level):
    if level == 1:
        if random.random() < 0.5:
            kg = _weighted_int(1, 20)
            return f"{kg}kg는 몇 g일까요?", kg * 1000
        g = _weighted_int(1, 20) * 1000
        return f"{g}g는 몇 kg일까요?", g // 1000
    if random.random() < 0.5:
        g = _weighted_int(1, 99) * 100
        return f"{g}g는 몇 kg일까요?", round(g / 1000, 2)
    kg = round(_weighted_int(1, 99) / 10, 1)
    return f"{kg}kg는 몇 g일까요?", round(kg * 1000)


def gen_unit_volume(level):
    if level == 1:
        if random.random() < 0.5:
            l = _weighted_int(1, 20)
            return f"{l}L는 몇 mL일까요?", l * 1000
        ml = _weighted_int(1, 20) * 1000
        return f"{ml}mL는 몇 L일까요?", ml // 1000
    if random.random() < 0.5:
        ml = _weighted_int(1, 99) * 100
        return f"{ml}mL는 몇 L일까요?", round(ml / 1000, 2)
    l = round(_weighted_int(1, 99) / 10, 1)
    return f"{l}L는 몇 mL일까요?", round(l * 1000)


def gen_clock(level):
    hour = random.randint(1, 12)
    if level == 1:
        minute = random.choice([0, 30])
    elif level == 2:
        minute = random.choice(range(0, 60, 5))
    else:
        minute = random.randint(0, 59)
    return hour, minute


MEASURE_LABELS = {"unit_length": "길이 단위 변환", "unit_weight": "무게 단위 변환",
                   "unit_volume": "들이 단위 변환", "clock_read": "시계 읽기"}
MEASURE_GEN = {"unit_length": gen_unit_length, "unit_weight": gen_unit_weight,
               "unit_volume": gen_unit_volume, "clock_read": gen_clock}
MEASURE_LEVELS_MAP = {"unit_length": UNIT_LENGTH_LEVELS, "unit_weight": UNIT_WEIGHT_LEVELS,
                       "unit_volume": UNIT_VOLUME_LEVELS, "clock_read": CLOCK_LEVELS}


# ---------------------------------------------------------------------------
# 학년별 메뉴에서 새로 필요해진 13개 단원 (수/규칙/곱셈구구/세 자리 수/시간/원/각/
# 각도/평균/약수/배수/비와 비율/비례식). 전부 "text_int"나 "text_decimal" 모드라
# PracticePage/TestPage 등 기존 화면을 그대로 재사용한다 (새 화면 불필요).
# ---------------------------------------------------------------------------
NUMBER_SENSE_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "1~20 사이의 수", "example": "예) 7 다음 수는?"},
    {"level": 2, "title": "Lv.2", "desc": "1~100 사이의 수", "example": "예) 63보다 1 작은 수는?"},
]
PATTERN_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "1~3씩 커지는 규칙", "example": "예) 2, 4, 6, 8, ?"},
    {"level": 2, "title": "Lv.2", "desc": "2~9씩 커지는 규칙", "example": "예) 5, 12, 19, 26, ?"},
    {"level": 3, "title": "Lv.3", "desc": "곱해지는 규칙", "example": "예) 2, 4, 8, 16, ?"},
]
# 구구단은 전통적인 학습 방식대로 2단~9단을 각각 하나의 레벨로 골라 연습한다.
TIMES_TABLE_LEVELS = [
    {"level": n - 1, "title": f"{n}단", "desc": f"{n}단 연습", "example": f"예) {n} × 3, {n} × 7"}
    for n in range(2, 10)
]
PLACE_VALUE_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "자릿값 구하기", "example": "예) 352에서 5가 나타내는 값"},
    {"level": 2, "title": "Lv.2", "desc": "가장 큰/작은 수 만들기", "example": "예) 3,5,2로 만들 수 있는 가장 큰 수"},
]
ELAPSED_TIME_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "같은 시 안에서 경과 시간", "example": "예) 3시 10분 ~ 3시 45분"},
    {"level": 2, "title": "Lv.2", "desc": "시가 바뀌는 경과 시간", "example": "예) 9시 40분 ~ 10시 15분"},
]
CIRCLE_RELATION_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "1~20cm", "example": "예) 반지름이 5cm면 지름은?"},
    {"level": 2, "title": "Lv.2", "desc": "1~50cm", "example": "예) 지름이 34cm면 반지름은?"},
]
ANGLE_BASIC_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "직각과 각의 기초", "example": "예) 직각은 몇 도?"},
    {"level": 2, "title": "Lv.2", "desc": "두 각의 합", "example": "예) 40도와 50도를 더하면?"},
]
ANGLE_CALC_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "삼각형 세 각의 합(180도)", "example": "예) 두 각이 50도, 60도면 나머지는?"},
    {"level": 2, "title": "Lv.2", "desc": "사각형 네 각의 합(360도)", "example": "예) 세 각이 80,90,100도면 나머지는?"},
]
AVERAGE_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "세 수의 평균", "example": "예) 4, 6, 8의 평균"},
    {"level": 2, "title": "Lv.2", "desc": "네 수의 평균", "example": "예) 3, 5, 7, 9의 평균"},
]
DIVISOR_COUNT_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "50 이하의 수", "example": "예) 12의 약수는 모두 몇 개?"},
    {"level": 2, "title": "Lv.2", "desc": "100 이하의 수", "example": "예) 48의 약수는 모두 몇 개?"},
]
MULTIPLE_FIND_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "작은 수의 배수", "example": "예) 4의 5번째 배수는?"},
    {"level": 2, "title": "Lv.2", "desc": "큰 수의 배수", "example": "예) 13의 8번째 배수는?"},
]
RATIO_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "비율을 소수로", "example": "예) 8은 20의 몇 배(비율)?"},
    {"level": 2, "title": "Lv.2", "desc": "비율을 백분율(%)로", "example": "예) 20은 50의 몇 %?"},
]
PROPORTION_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "작은 수의 비례식", "example": "예) 2:3 = 8:x"},
    {"level": 2, "title": "Lv.2", "desc": "큰 수의 비례식", "example": "예) 6:7 = x:35"},
]


def gen_number_sense(level):
    hi = 20 if level == 1 else 100
    n = _weighted_int(2, hi - 1)
    variant = random.randint(0, 2)
    if variant == 0:
        return f"{n} 다음 수는 무엇일까요?", n + 1
    if variant == 1:
        return f"{n}보다 1 작은 수는 무엇일까요?", n - 1
    m = _weighted_int(1, hi)
    while m == n:
        m = _weighted_int(1, hi)
    bigger = max(n, m)
    return f"{n}{_num_josa(n, '과', '와')} {m} 중에서 더 큰 수는 무엇일까요?", bigger


def gen_pattern(level):
    if level == 1:
        step = _weighted_int(1, 3)
        start = _weighted_int(1, 15)
        terms = [start + step * i for i in range(4)]
        answer = start + step * 4
        explain = f"규칙: 숫자가 {step}씩 커지는 규칙이에요. {terms[-1]} 다음은 {terms[-1]}+{step}={answer}예요."
    elif level == 2:
        step = _weighted_int(2, 9)
        start = _weighted_int(1, 30)
        terms = [start + step * i for i in range(4)]
        answer = start + step * 4
        explain = f"규칙: 숫자가 {step}씩 커지는 규칙이에요. {terms[-1]} 다음은 {terms[-1]}+{step}={answer}예요."
    else:
        ratio = random.choice([2, 3])
        start = _weighted_int(1, 5)
        terms = [start * (ratio ** i) for i in range(4)]
        answer = start * (ratio ** 4)
        explain = f"규칙: 숫자가 {ratio}배씩 커지는 규칙이에요. {terms[-1]} 다음은 {terms[-1]}×{ratio}={answer}예요."
    seq_text = ", ".join(str(t) for t in terms)
    return f"규칙에 맞게 다음에 올 수를 구하세요: {seq_text}, ?", answer, {"explain": explain}


def gen_times_table(level):
    a = level + 1  # level 1 -> 2단, level 2 -> 3단, ..., level 8 -> 9단
    b = _weighted_int(1, 9)
    return f"{a} × {b}", a * b


def gen_place_value(level):
    if level == 1:
        h, t, o = _weighted_int(1, 9), _weighted_int(0, 9), _weighted_int(0, 9)
        n = h * 100 + t * 10 + o
        digit, place, mult = random.choice([(h, "백의", 100), (t, "십의", 10), (o, "일의", 1)])
        value = digit * mult
        return f"{n}에서 {place} 자리 숫자가 나타내는 값은 얼마일까요?", value
    d1, d2, d3 = random.sample(range(0, 10), 3)  # distinct digits -> at most one is 0
    digits = [d1, d2, d3]
    nonzero_desc = sorted([d for d in digits if d != 0], reverse=True)
    josa = _num_josa_ro(d3)
    if random.random() < 0.5:
        # 가장 큰 수: 0이 아닌 가장 큰 숫자를 앞자리로, 나머지(0 포함)는 내림차순으로 뒤에
        leading = nonzero_desc[0]
        rest = sorted(digits, reverse=True)
        rest.remove(leading)
        answer_digits = [leading] + rest
        text = f"숫자 카드 {d1}, {d2}, {d3}{josa} 만들 수 있는 가장 큰 세 자리 수는 얼마일까요?"
    else:
        # 가장 작은 수: 0이 아닌 가장 작은 숫자를 앞자리로(0은 맨 앞에 올 수 없음), 나머지는 오름차순
        leading = nonzero_desc[-1]
        rest = sorted(digits)
        rest.remove(leading)
        answer_digits = [leading] + rest
        text = f"숫자 카드 {d1}, {d2}, {d3}{josa} 만들 수 있는 가장 작은 세 자리 수는 얼마일까요?"
    answer = int("".join(str(d) for d in answer_digits))
    return text, answer


ELAPSED_ACTIVITIES = ["놀이", "수업", "축구 경기", "독서", "청소", "그림 그리기 대회"]


def gen_elapsed_time(level):
    h = random.randint(1, 11)  # never 12, so h % 12 == h below always holds
    activity = random.choice(ELAPSED_ACTIVITIES)
    if level == 1:
        duration = _weighted_int(5, 50)
        max_m1 = 60 - duration - 1
        m1 = _weighted_int(0, max_m1) if max_m1 >= 0 else 0
        end_h, end_m = h, m1 + duration
    else:
        duration = _weighted_int(20, 90)
        m1 = _weighted_int(0, 40)
        total = m1 + duration
        end_h0 = (h + total // 60) % 12
        end_h = 12 if end_h0 == 0 else end_h0
        end_m = total % 60
    text = (f"{h}시 {m1}분에 시작한 {activity}{_josa(activity, '이', '가')} {end_h}시 {end_m}분에 끝났습니다. "
            f"{activity}{_josa(activity, '은', '는')} 몇 분 동안 진행되었을까요?")
    return text, duration


def gen_circle_relation(level):
    hi = 20 if level == 1 else 50
    if random.random() < 0.5:
        r = _weighted_int(1, hi)
        return (f"원의 반지름이 {r}cm이면 지름은 몇 cm일까요?", r * 2,
                {"draw": ("shape_circle", {"반지름": r})})
    d = _weighted_int(1, hi) * 2
    return (f"원의 지름이 {d}cm이면 반지름은 몇 cm일까요?", d // 2,
            {"draw": ("shape_circle", {"지름": d})})


def gen_angle_basic(level):
    if level == 1:
        variant = random.randint(0, 1)
        if variant == 0:
            return "직각은 몇 도인가요?", 90, {"draw": ("angle", [90])}
        a = _weighted_int(10, 80)
        return (f"직각(90도)에서 {a}도를 빼면 몇 도일까요?", 90 - a,
                {"draw": ("angle", [90, a])})
    a, b = _weighted_int(10, 90), _weighted_int(10, 90)
    if random.random() < 0.5:
        return f"{a}도와 {b}도를 더하면 몇 도일까요?", a + b, {"draw": ("angle", [a, b])}
    a, b = max(a, b), min(a, b)
    return f"{a}도에서 {b}도를 빼면 몇 도일까요?", a - b, {"draw": ("angle", [a, b])}


def gen_angle_calc(level):
    if level == 1:
        a = _weighted_int(20, 90)
        b = _weighted_int(20, 180 - a - 10)
        c = 180 - a - b
        return f"삼각형의 세 각 중 두 각이 {a}도, {b}도입니다. 나머지 한 각은 몇 도일까요?", c
    a = _weighted_int(50, 150)
    b = _weighted_int(50, 150)
    c = _weighted_int(20, max(21, 360 - a - b - 10))
    d = 360 - a - b - c
    while d < 10:
        a = _weighted_int(50, 150)
        b = _weighted_int(50, 150)
        c = _weighted_int(20, max(21, 360 - a - b - 10))
        d = 360 - a - b - c
    return f"사각형의 네 각 중 세 각이 {a}도, {b}도, {c}도입니다. 나머지 한 각은 몇 도일까요?", d


def gen_average(level):
    count = 3 if level == 1 else 4
    avg = _weighted_int(3, 30)
    total = avg * count
    nums = []
    remaining_total = total
    remaining_count = count
    for i in range(count - 1):
        max_val = remaining_total - (remaining_count - 1) * 1
        max_val = max(1, min(max_val, avg * 2 if avg * 2 > 0 else 1))
        v = random.randint(1, max(1, max_val))
        nums.append(v)
        remaining_total -= v
        remaining_count -= 1
    nums.append(remaining_total)
    if nums[-1] <= 0:
        nums = [avg] * count  # fallback: flat sequence, still a valid (boring) average
    random.shuffle(nums)
    nums_text = ", ".join(str(n) for n in nums)
    return f"다음 수들의 평균을 구하세요: {nums_text}", sum(nums) // count


def gen_divisor_count(level):
    lo, hi = (6, 50) if level == 1 else (20, 100)
    n = _weighted_int(lo, hi)
    count = sum(1 for d in range(1, n + 1) if n % d == 0)
    return f"{n}의 약수는 모두 몇 개일까요?", count


def gen_multiple_find(level):
    lo, hi, k_lo, k_hi = (2, 12, 2, 9) if level == 1 else (13, 30, 2, 12)
    n, k = _weighted_int(lo, hi), _weighted_int(k_lo, k_hi)
    return f"{n}의 {k}번째 배수는 얼마일까요?", n * k


def gen_ratio(level):
    if level == 1:
        base = _weighted_int(2, 20)
        mult = round(_weighted_int(2, 30) / 10, 1)
        compare = round(base * mult)
        if compare <= 0:
            compare = base
        actual_ratio = round(compare / base, 2)
        return f"{compare}{_num_josa(compare, '은', '는')} {base}의 몇 배(비율)일까요? (소수로 답하세요)", actual_ratio
    # base must be a multiple of 20 so that base*pct/100 always lands on an
    # exact integer for every percentage below (their required divisors --
    # 10, 5, 4, 2 -- all divide 20), otherwise int-dividing compare back
    # down would silently produce a "정답" that doesn't reverse to pct.
    base = _weighted_int(1, 10) * 20
    pct_choices = [10, 20, 25, 40, 50, 60, 75, 80, 90]
    pct = random.choice(pct_choices)
    compare = base * pct // 100
    return f"{compare}{_num_josa(compare, '은', '는')} {base}의 몇 %일까요?", pct


def gen_proportion(level):
    hi = 12 if level == 1 else 30
    while True:
        a, b = _weighted_int(2, hi), _weighted_int(2, hi)
        if math.gcd(a, b) == 1 and a != b:
            break
    k = _weighted_int(2, 9)
    unknown_is_c = random.random() < 0.5
    if unknown_is_c:
        c, x = a * k, b * k
        return f"{a}:{b} = {c}:x 일 때, x는 얼마일까요?", x
    x, d = a * k, b * k
    return f"{a}:{b} = x:{d} 일 때, x는 얼마일까요?", x


# ---------------------------------------------------------------------------
# 모양 (초1) -- "choice" 모드: 그려진 도형을 보고 이름을 골라 맞히는 4지선다형.
# 다른 단원과 달리 (문제문구, 선택지 목록, 정답) 3-tuple을 돌려준다.
# ---------------------------------------------------------------------------
SHAPE_NAME_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "원 · 삼각형 · 사각형", "example": "예) 이 도형의 이름은?"},
    {"level": 2, "title": "Lv.2", "desc": "오각형 · 육각형 포함", "example": "예) 이 도형의 이름은?"},
]
SHAPE_NAME_POOL_1 = ["원", "삼각형", "사각형"]
SHAPE_NAME_POOL_2 = ["원", "삼각형", "사각형", "오각형", "육각형"]


def gen_shape_name(level):
    pool = SHAPE_NAME_POOL_1 if level == 1 else SHAPE_NAME_POOL_2
    correct = random.choice(pool)
    n_choices = 3 if level == 1 else 4
    distractors = [s for s in pool if s != correct]
    random.shuffle(distractors)
    choices = [correct] + distractors[:n_choices - 1]
    random.shuffle(choices)
    return "이 도형의 이름은 무엇일까요?", choices, correct


# ---------------------------------------------------------------------------
# 그래프 (초3/초6) -- 막대그래프를 보고 답하는 수치형 문제 ("text_int" 재사용).
# ---------------------------------------------------------------------------
GRAPH_READ_LEVELS = [
    {"level": 1, "title": "Lv.1", "desc": "항목 3개, 작은 수", "example": "예) 가장 많은 과일은 몇 개?"},
    {"level": 2, "title": "Lv.2", "desc": "항목 4~5개, 큰 수", "example": "예) 사과와 배의 차이는?"},
]
GRAPH_CATEGORIES = ["사과", "배", "귤", "포도", "키위", "수박", "딸기"]


def gen_graph_read(level):
    n_cats = 3 if level == 1 else random.choice([4, 5])
    step = _weighted_int(1, 3) if level == 1 else _weighted_int(2, 5)
    cats = random.sample(GRAPH_CATEGORIES, n_cats)
    mults = [random.randint(1, 4) for _ in cats]
    while len(set(mults)) == 1:  # avoid every bar being identical (nothing to compare)
        mults = [random.randint(1, 4) for _ in cats]
    values = [m * step for m in mults]

    variant = random.choice(["max", "min", "specific", "diff", "sum"])
    prefix = "과일 개수를 나타낸 그래프입니다."
    if variant == "max":
        text, answer = f"{prefix} 가장 많은 과일은 몇 개일까요?", max(values)
    elif variant == "min":
        text, answer = f"{prefix} 가장 적은 과일은 몇 개일까요?", min(values)
    elif variant == "specific":
        idx = random.randrange(len(cats))
        cat = cats[idx]
        text = f"{prefix} {cat}{_josa(cat, '은', '는')} 몇 개일까요?"
        answer = values[idx]
    elif variant == "diff":
        i, j = random.sample(range(len(cats)), 2)
        text = f"{prefix} {cats[i]}{_josa(cats[i], '과', '와')} {cats[j]}의 개수 차이는 몇 개일까요?"
        answer = abs(values[i] - values[j])
    else:
        text, answer = f"{prefix} 과일은 모두 몇 개일까요?", sum(values)

    return text, answer, {"draw": ("bargraph", (cats, values, step))}


GRADE_UNIT_LABELS = {
    "number_sense": "수", "pattern": "규칙", "times_table": "구구단",
    "place_value": "세 자리 수", "elapsed_time": "시간", "circle_relation": "원",
    "angle_basic": "각", "angle_calc": "각도", "average": "평균",
    "divisor_count": "약수", "multiple_find": "배수", "ratio": "비와 비율",
    "proportion": "비례식", "shape_name": "모양", "graph_read": "그래프",
}
GRADE_UNIT_GEN = {
    "number_sense": gen_number_sense, "pattern": gen_pattern, "times_table": gen_times_table,
    "place_value": gen_place_value, "elapsed_time": gen_elapsed_time, "circle_relation": gen_circle_relation,
    "angle_basic": gen_angle_basic, "angle_calc": gen_angle_calc, "average": gen_average,
    "divisor_count": gen_divisor_count, "multiple_find": gen_multiple_find, "ratio": gen_ratio,
    "proportion": gen_proportion, "shape_name": gen_shape_name, "graph_read": gen_graph_read,
}
GRADE_UNIT_LEVELS_MAP = {
    "number_sense": NUMBER_SENSE_LEVELS, "pattern": PATTERN_LEVELS, "times_table": TIMES_TABLE_LEVELS,
    "place_value": PLACE_VALUE_LEVELS, "elapsed_time": ELAPSED_TIME_LEVELS,
    "circle_relation": CIRCLE_RELATION_LEVELS, "angle_basic": ANGLE_BASIC_LEVELS,
    "angle_calc": ANGLE_CALC_LEVELS, "average": AVERAGE_LEVELS, "divisor_count": DIVISOR_COUNT_LEVELS,
    "multiple_find": MULTIPLE_FIND_LEVELS, "ratio": RATIO_LEVELS, "proportion": PROPORTION_LEVELS,
    "shape_name": SHAPE_NAME_LEVELS, "graph_read": GRAPH_READ_LEVELS,
}
# ratio는 Lv1이 소수(0.4배 등), Lv2가 정수(퍼센트)를 돌려주는데, "text_decimal" 모드는
# 정수 답도 그대로 받아들이므로(0.005 오차 허용 비교) 이 op 하나만 text_decimal로 통일한다.
GRADE_UNIT_DECIMAL_OPS = {"ratio"}
# shape_name은 숫자 답이 아니라 4지선다("choice" 모드)라 아래 자동 등록 루프에서
# 빼고 별도로 지정한다.
GRADE_UNIT_CHOICE_OPS = {"shape_name"}
# 이 연산들은 gen 함수가 3번째 원소로 {"draw": (kind, data)}를 돌려주고,
# PracticePage가 그 op일 때만 캔버스를 만들어 문제마다 그림을 그려준다.
DIAGRAM_OPS = {"circle_relation", "angle_basic", "graph_read"}

# 공식이 실제로 있는 학년별 신규 단원만 문제 화면에 공식을 함께 보여준다
# (구구단·세 자리 수·시간·수·규칙·약수·배수처럼 "공식"이랄 게 없는 단원은 제외).
FORMULA_TEXT = {
    "circle_relation": "지름 = 반지름 × 2   /   반지름 = 지름 ÷ 2",
    "angle_basic": "직각 = 90도   /   일직선 = 180도",
    "angle_calc": "삼각형 세 각의 합 = 180도   /   사각형 네 각의 합 = 360도",
    "average": "평균 = (모든 수의 합) ÷ (수의 개수)",
    "ratio": "비율 = 비교하는 양 ÷ 기준량",
    "proportion": "가:나 = 다:라 이면, 가×라 = 나×다",
}

# LevelSelectPage 하단 안내 문구. 기본값("레벨이 올라갈수록 자릿수가 늘어나요")이
# 맞지 않는 단원만 여기서 따로 지정한다.
LEVEL_CAPTION_DEFAULT = "레벨이 올라갈수록 자릿수가 늘어나요"
LEVEL_CAPTION_OVERRIDES = {
    "times_table": "레벨이 올라갈수록 큰 단을 연습해요",
    "shape_name": "여러 가지 도형의 이름을 맞혀보세요",
    "clock_read": "레벨이 올라갈수록 시각을 더 세밀하게 읽어요",
}


OP_LABELS = {"add": "덧셈", "sub": "뺄셈", "mul": "곱셈", "div": "나눗셈"}
OP_SYMBOL = {"add": "+", "sub": "−", "mul": "×", "div": "÷"}
OP_GEN = {"add": gen_addition, "sub": gen_subtraction, "mul": gen_multiplication, "div": gen_division}
OP_LEVELS_MAP = {"add": ADD_LEVELS, "sub": SUB_LEVELS, "mul": MUL_LEVELS, "div": DIV_LEVELS}

# 분수/소수/문장제/약수와 배수/측정/학년별 신규 13개 단원도 같은 화면들(레벨선택/문제풀이)을
# 공유하므로 공통 맵에 합쳐 둔다.
OP_LABELS.update(FRAC_LABELS)
OP_LABELS.update(DEC_LABELS)
OP_LABELS.update(WORD_LABELS)
OP_LABELS.update(NUM_LABELS)
OP_LABELS.update(MEASURE_LABELS)
OP_LABELS.update(GRADE_UNIT_LABELS)
OP_SYMBOL.update(FRAC_SYMBOL)
OP_SYMBOL.update(DEC_SYMBOL)
OP_GEN.update(FRAC_GEN)
OP_GEN.update(DEC_GEN)
OP_GEN.update(WORD_GEN)
OP_GEN.update(NUM_GEN)
OP_GEN.update(MEASURE_GEN)
OP_GEN.update(GRADE_UNIT_GEN)
OP_LEVELS_MAP.update(FRAC_LEVELS_MAP)
OP_LEVELS_MAP.update(DEC_LEVELS_MAP)
OP_LEVELS_MAP.update(WORD_LEVELS_MAP)
OP_LEVELS_MAP.update(NUM_LEVELS_MAP)
OP_LEVELS_MAP.update(MEASURE_LEVELS_MAP)
OP_LEVELS_MAP.update(GRADE_UNIT_LEVELS_MAP)

# 각 연산이 답을 어떻게 입력/채점하는지: 정수 / 소수(오차허용) / 분수(분자÷분모) / 분수쌍(a/b op c/d) /
# 문장제·약수배수(정수 서술형) / 단위변환(소수 서술형) / 시계(시·분 두 칸)
OP_ANSWER_MODE = {
    "add": "int", "sub": "int", "mul": "int", "div": "div_fraction",
    "dec_add": "decimal", "dec_sub": "decimal", "dec_mul": "decimal", "dec_div": "decimal",
    "frac_add": "frac_pair", "frac_sub": "frac_pair", "frac_mul": "frac_pair", "frac_div": "frac_pair",
    "word_add": "text_int", "word_sub": "text_int", "word_mul": "text_int", "word_div": "text_int",
    "gcd": "text_int", "lcm": "text_int",
    "unit_length": "text_decimal", "unit_weight": "text_decimal", "unit_volume": "text_decimal",
    "clock_read": "clock",
}
for _gu_op in GRADE_UNIT_LABELS:
    if _gu_op in GRADE_UNIT_CHOICE_OPS:
        OP_ANSWER_MODE[_gu_op] = "choice"
    elif _gu_op in GRADE_UNIT_DECIMAL_OPS:
        OP_ANSWER_MODE[_gu_op] = "text_decimal"
    else:
        OP_ANSWER_MODE[_gu_op] = "text_int"

# LevelSelectPage/PracticePage는 여러 카테고리가 공유하므로,
# 뒤로가기가 어느 상위 화면으로 갈지는 카테고리로 구분한다.
OP_CATEGORY = {
    "add": "arith", "sub": "arith", "mul": "arith", "div": "arith",
    "frac_add": "fracdec", "frac_sub": "fracdec", "frac_mul": "fracdec", "frac_div": "fracdec",
    "dec_add": "fracdec", "dec_sub": "fracdec", "dec_mul": "fracdec", "dec_div": "fracdec",
    "word_add": "word", "word_sub": "word", "word_mul": "word", "word_div": "word",
    "gcd": "numtheory", "lcm": "numtheory",
    "unit_length": "measure", "unit_weight": "measure", "unit_volume": "measure", "clock_read": "measure",
}
for _gu_op in GRADE_UNIT_LABELS:
    OP_CATEGORY[_gu_op] = "gradenew"
CATEGORY_BACK = {
    "arith": ("← 사칙연산", "show_op_select"),
    "fracdec": ("← 분수·소수", "show_fracdec_select"),
    "word": ("← 문장제", "show_word_select"),
    "numtheory": ("← 약수와 배수", "show_numtheory_select"),
    "measure": ("← 측정", "show_measure_select"),
    "shape": ("← 도형", "show_shape_home"),
    "gradenew": ("← 처음으로", "show_main_menu"),
}
CATEGORY_NAME = {cat: label[2:] for cat, (label, _cmd) in CATEGORY_BACK.items()}  # "← X" -> "X"


def _ro_josa(word):
    return "으로" if _has_batchim(word) else "로"


# 시험(TestSetupPage)에서 카테고리별로 고를 수 있는 연산 목록. 도형은 구조가
# 완전히 달라(치수 dict 기반) 별도의 ShapeTestSetupPage로 처리한다.
TEST_OPS_BY_CATEGORY = {
    "arith": ["add", "sub", "mul", "div"],
    "fracdec": ["frac_add", "frac_sub", "frac_mul", "frac_div", "dec_add", "dec_sub", "dec_mul", "dec_div"],
    "word": ["word_add", "word_sub", "word_mul", "word_div"],
    "numtheory": ["gcd", "lcm"],
    "measure": ["unit_length", "unit_weight", "unit_volume", "clock_read"],
}


# ---------------------------------------------------------------------------
# 기록: 완료한 시험 결과를 exe(또는 스크립트)와 같은 폴더의 json 파일에 저장한다.
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


HISTORY_PATH = os.path.join(_app_dir(), "기록.json")


def load_history():
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_history_entry(entry):
    entries = load_history()
    entries.append(entry)
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 디스크에 못 써도 앱이 죽어서는 안 됨


def clear_history():
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump({"entries": []}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 시작 시 뜨는 버전 안내 팝업의 "오늘 하루 그만보기" 상태 저장.
# ---------------------------------------------------------------------------
NOTICE_PATH = os.path.join(_app_dir(), "공지설정.json")


def load_notice_dismiss_date():
    try:
        with open(NOTICE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("dismiss_date")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_notice_dismiss_date(date_str):
    try:
        with open(NOTICE_PATH, "w", encoding="utf-8") as f:
            json.dump({"dismiss_date": date_str}, f, ensure_ascii=False)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# 자동 업데이트: GitHub Release에서 최신 버전을 확인하고, 있으면 새 exe를 받아
# 지금 실행 중인 exe를 교체한다. 새 버전을 배포하려면 GitHub 저장소에
# 태그를 "v1.1"처럼 붙여서 Release를 만들고, 빌드한 exe를 EXE_ASSET_NAME과
# 정확히 같은 파일명으로 첨부하면 된다. EXE_ASSET_NAME은 일부러 영문으로
# 뒀다 -- GitHub 웹 업로드(특히 드래그 앤 드롭)가 한글 파일명을 "default.exe"로
# 깨뜨리는 경우가 있어서다. 로컬에 설치된 실제 파일명(초등수학문제집.exe)엔
# 영향 없음 -- download_and_restart_with_update()가 항상 지금 실행 중인
# exe의 경로(sys.executable)에 덮어쓰므로, 여긴 그저 Release에서 "어떤
# 첨부파일을 받을지" 찾는 이름일 뿐이다.
# ---------------------------------------------------------------------------
GITHUB_REPO = "JungSung-Kim/Elementary-Mathematics"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
EXE_ASSET_NAME = "MathWorkbook.exe"


def _parse_version(v):
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums) if nums else (0,)


def fetch_latest_release_info():
    """Hits the GitHub API for this repo's latest release. Returns
    (tag_name, download_url) or None on ANY failure -- offline, no releases
    published yet, rate-limited, malformed response, ... An update check
    must never crash or block the app, so every failure mode just means
    'no update found this time'."""
    try:
        req = urllib.request.Request(
            GITHUB_API_LATEST,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "math-workbook-app"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = data.get("tag_name", "")
        asset_url = None
        for asset in data.get("assets", []):
            if asset.get("name") == EXE_ASSET_NAME:
                asset_url = asset.get("browser_download_url")
                break
        if not tag or not asset_url:
            return None
        return tag, asset_url
    except Exception:
        return None


def download_and_restart_with_update(download_url):
    """Downloads the new exe, then hands off to a small detached batch
    script that waits for this process to exit, overwrites the current exe
    with the new one, relaunches it, and deletes itself -- Windows won't
    let a running exe overwrite its own file directly."""
    exe_path = sys.executable
    tmp_new = os.path.join(tempfile.gettempdir(), "초등수학문제집_new.exe")

    req = urllib.request.Request(download_url, headers={"User-Agent": "math-workbook-app"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_new, "wb") as f:
        shutil.copyfileobj(resp, f)

    bat_path = os.path.join(tempfile.gettempdir(), "초등수학문제집_update.bat")
    bat_content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        f'copy /y "{tmp_new}" "{exe_path}"\r\n'
        f'start "" "{exe_path}"\r\n'
        'del "%~f0"\r\n'
    )
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )


# ---------------------------------------------------------------------------
# 도형: 초등 교육과정 범위의 둘레·넓이·부피 공식과 문제 생성
# (원기둥/원뿔/구의 부피, 겉넓이 등은 중학교 과정이라 제외)
# ---------------------------------------------------------------------------
SHAPE_DEFS = []
SHAPE_ORDER = ["정사각형", "직사각형", "평행사변형", "삼각형", "마름모",
               "사다리꼴", "원", "직육면체", "정육면체"]
SHAPE_ICONS = {
    "정사각형": "■", "직사각형": "▭", "평행사변형": "▱", "삼각형": "▲",
    "마름모": "◆", "사다리꼴": "⏢", "원": "●", "직육면체": "▦", "정육면체": "▩",
}


def _add_shape(key, shape_label, quantity_label, unit, formula_text, gen_fn, decimal=False):
    SHAPE_DEFS.append({
        "key": key, "shape_label": shape_label, "quantity_label": quantity_label,
        "unit": unit, "formula_text": formula_text, "gen": gen_fn, "decimal": decimal,
    })


def _gen_square_perimeter():
    s = _weighted_int(1, 30)
    return {"한 변": s}, s * 4


def _gen_square_area():
    s = _weighted_int(1, 30)
    return {"한 변": s}, s * s


def _gen_rect_perimeter():
    w, h = _weighted_int(1, 30), _weighted_int(1, 30)
    return {"가로": w, "세로": h}, (w + h) * 2


def _gen_rect_area():
    w, h = _weighted_int(1, 30), _weighted_int(1, 30)
    return {"가로": w, "세로": h}, w * h


def _gen_parallelogram_area():
    b, h = _weighted_int(1, 30), _weighted_int(1, 30)
    return {"밑변": b, "높이": h}, b * h


def _gen_triangle_area():
    while True:
        b, h = _weighted_int(1, 30), _weighted_int(1, 30)
        if (b * h) % 2 == 0:
            break
    return {"밑변": b, "높이": h}, b * h // 2


def _gen_rhombus_perimeter():
    s = _weighted_int(1, 30)
    return {"한 변": s}, s * 4


def _gen_rhombus_area():
    while True:
        d1, d2 = _weighted_int(1, 30), _weighted_int(1, 30)
        if (d1 * d2) % 2 == 0:
            break
    return {"한 대각선": d1, "다른 대각선": d2}, d1 * d2 // 2


def _gen_trapezoid_area():
    while True:
        a, b, h = _weighted_int(1, 20), _weighted_int(1, 20), _weighted_int(1, 20)
        if ((a + b) * h) % 2 == 0:
            break
    return {"윗변": a, "아랫변": b, "높이": h}, (a + b) * h // 2


def _gen_circle_circumference():
    d = _weighted_int(1, 30)
    return {"지름": d}, round(d * 3.14, 2)


def _gen_circle_area():
    r = _weighted_int(1, 20)
    return {"반지름": r}, round(r * r * 3.14, 2)


def _gen_cuboid_volume():
    a, b, c = _weighted_int(1, 15), _weighted_int(1, 15), _weighted_int(1, 15)
    return {"가로": a, "세로": b, "높이": c}, a * b * c


def _gen_cube_volume():
    s = _weighted_int(1, 15)
    return {"한 모서리": s}, s ** 3


_add_shape("square_perimeter", "정사각형", "둘레", "cm", "둘레 = 한 변 × 4", _gen_square_perimeter)
_add_shape("square_area", "정사각형", "넓이", "cm²", "넓이 = 한 변 × 한 변", _gen_square_area)
_add_shape("rect_perimeter", "직사각형", "둘레", "cm", "둘레 = (가로 + 세로) × 2", _gen_rect_perimeter)
_add_shape("rect_area", "직사각형", "넓이", "cm²", "넓이 = 가로 × 세로", _gen_rect_area)
_add_shape("parallelogram_area", "평행사변형", "넓이", "cm²", "넓이 = 밑변 × 높이", _gen_parallelogram_area)
_add_shape("triangle_area", "삼각형", "넓이", "cm²", "넓이 = 밑변 × 높이 ÷ 2", _gen_triangle_area)
_add_shape("rhombus_perimeter", "마름모", "둘레", "cm", "둘레 = 한 변 × 4", _gen_rhombus_perimeter)
_add_shape("rhombus_area", "마름모", "넓이", "cm²", "넓이 = 한 대각선 × 다른 대각선 ÷ 2", _gen_rhombus_area)
_add_shape("trapezoid_area", "사다리꼴", "넓이", "cm²", "넓이 = (윗변 + 아랫변) × 높이 ÷ 2", _gen_trapezoid_area)
_add_shape("circle_circumference", "원", "둘레(원주)", "cm", "원주 = 지름 × 3.14", _gen_circle_circumference, decimal=True)
_add_shape("circle_area", "원", "넓이", "cm²", "넓이 = 반지름 × 반지름 × 3.14", _gen_circle_area, decimal=True)
_add_shape("cuboid_volume", "직육면체", "부피", "cm³", "부피 = 가로 × 세로 × 높이", _gen_cuboid_volume)
_add_shape("cube_volume", "정육면체", "부피", "cm³", "부피 = 한 모서리 × 한 모서리 × 한 모서리", _gen_cube_volume)

SHAPES_BY_LABEL = {}
for _sd in SHAPE_DEFS:
    SHAPES_BY_LABEL.setdefault(_sd["shape_label"], []).append(_sd)
SHAPE_DEFS_BY_KEY = {sd["key"]: sd for sd in SHAPE_DEFS}

TEST_QUESTION_COUNTS = [10, 20, 30, 50]
TEST_TIME_LIMITS = [3, 5, 10, 15]  # minutes
COUNT_MIN, COUNT_MAX = 1, 100
MINUTES_MIN, MINUTES_MAX = 1, 60


class RoundButton(tk.Button):
    """A simple flat, colorful button styled for a kids' app."""

    def __init__(self, master, text, command, bg=PRIMARY, fg="white",
                 active_bg=None, size=18, bold=True, width=None, pady=14, **kw):
        active_bg = active_bg or bg
        super().__init__(
            master, text=text, command=command, bg=bg, fg=fg,
            activebackground=active_bg, activeforeground=fg,
            font=(FONT_NAME, size, "bold" if bold else "normal"),
            relief="flat", bd=0, cursor="hand2", width=width, pady=pady,
            **kw,
        )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"초등 수학 문제집 {APP_VERSION}")
        self.geometry("820x800")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        # When set, (label, callback): overrides a shared page's default
        # "뒤로가기" (e.g. LevelSelectPage's CATEGORY_BACK, ShapePracticePage's
        # go_back) so that content entered from a 학년 page returns to that
        # grade's unit list (or the 학년 그룹 화면that dispatched it) instead
        # of the old operation-category screen. Set right before navigating
        # into a shared page from a grade context; cleared on any "index"
        # page so it never leaks into an unrelated navigation later.
        self.nav_return = None
        # Separate from nav_return: only ShapeSelectPage checks this, so that
        # 초5 "도형" (browse every shape) still lets ShapeQuantitySelectPage/
        # ShapePracticePage chain back through their own normal parent (not
        # jump straight to the grade page), while ShapeSelectPage itself
        # still knows to return to the grade it was opened from.
        self.shape_browse_return = None
        # Which grade (1-6) the current page was entered from, if any --
        # purely for display (a small "초등 N학년" badge on shared pages).
        self.entry_grade = None

        self.show_main_menu()

    def reset_nav_context(self):
        self.nav_return = None
        self.shape_browse_return = None
        self.entry_grade = None

    def reset_nav_return_only(self):
        """For ShapeSelectPage/ShapeQuantitySelectPage: clears the (unrelated)
        grade->single-unit nav_return, but keeps shape_browse_return and
        entry_grade alive so 초N '도형 전체보기' keeps its own grade context
        as the user browses through these pages."""
        self.nav_return = None

    def maybe_show_version_notice(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if load_notice_dismiss_date() == today:
            return
        VersionNoticeDialog(self, VERSION_HISTORY[0])

    def maybe_check_for_update(self):
        threading.Thread(target=self._check_for_update_worker, daemon=True).start()

    def _check_for_update_worker(self):
        info = fetch_latest_release_info()
        if info is None:
            return
        tag, download_url = info
        if _parse_version(tag) > _parse_version(APP_VERSION):
            self.after(0, lambda: UpdateAvailableDialog(self, tag, download_url))

    def clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def set_enter_handler(self, handler):
        """Route the Enter key to `handler` no matter which widget has focus.
        Pass None to disable (used on non-practice pages)."""
        self.unbind("<Return>")
        self.unbind("<KP_Enter>")
        if handler is not None:
            self.bind("<Return>", lambda e: handler())
            self.bind("<KP_Enter>", lambda e: handler())

    def show_main_menu(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        MainMenuPage(self.container, self)

    def show_category_index(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        CategoryIndexPage(self.container, self)

    def show_grade_select(self, grade):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        GradeSelectPage(self.container, self, grade)

    def show_grade_group(self, grade, label, kind, items):
        self.clear()
        self.set_enter_handler(None)
        GradeGroupPage(self.container, self, grade, label, kind, items)

    def show_op_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        OpSelectPage(self.container, self)

    def show_level_select(self, op):
        self.clear()
        self.set_enter_handler(None)
        LevelSelectPage(self.container, self, op)

    def show_practice(self, op, level):
        self.clear()
        PracticePage(self.container, self, op, level)

    def show_settings(self, category="arith"):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        SettingsPage(self.container, self, category)

    def show_test_setup(self, category="arith"):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        TestSetupPage(self.container, self, category)

    def show_test(self, op, level, count, minutes):
        self.clear()
        TestPage(self.container, self, op, level, count, minutes)

    def show_test_result(self, op, level, questions, user_answers, elapsed_seconds, total_seconds):
        self.clear()
        self.set_enter_handler(None)
        TestResultPage(self.container, self, op, level, questions, user_answers,
                         elapsed_seconds, total_seconds)

    def show_shape_home(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        ShapeHomePage(self.container, self)

    def show_shape_formulas(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        ShapeFormulaPage(self.container, self)

    def show_shape_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_return_only()
        ShapeSelectPage(self.container, self)

    def show_shape_quantity_select(self, shape_label):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_return_only()
        ShapeQuantitySelectPage(self.container, self, shape_label)

    def show_shape_practice(self, key):
        self.clear()
        ShapePracticePage(self.container, self, key)

    def show_shape_test_setup(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        ShapeTestSetupPage(self.container, self)

    def show_shape_test(self, key, count, minutes):
        self.clear()
        ShapeTestPage(self.container, self, key, count, minutes)

    def show_shape_test_result(self, key, questions, user_answers, elapsed_seconds, total_seconds):
        self.clear()
        self.set_enter_handler(None)
        ShapeTestResultPage(self.container, self, key, questions, user_answers,
                              elapsed_seconds, total_seconds)

    def show_fracdec_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        FracDecSelectPage(self.container, self)

    def show_word_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        WordSelectPage(self.container, self)

    def show_numtheory_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        NumTheorySelectPage(self.container, self)

    def show_measure_select(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        MeasureSelectPage(self.container, self)

    def show_history(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        HistoryPage(self.container, self)

    def show_version_history(self):
        self.clear()
        self.set_enter_handler(None)
        self.reset_nav_context()
        VersionHistoryPage(self.container, self)

    def show_wrong_answer_review(self, op, questions):
        self.clear()
        WrongAnswerReviewPage(self.container, self, op, questions)

    def show_review_done(self, op, total, correct):
        self.clear()
        self.set_enter_handler(None)
        ReviewDonePage(self.container, self, op, total, correct)


class VersionNoticeDialog(tk.Toplevel):
    """Startup popup showing the latest version's changelog. '확인' just
    closes it (shows again next launch); '오늘 하루 그만보기' also remembers
    today's date so it stays quiet for the rest of the day."""

    def __init__(self, app, entry):
        super().__init__(app)
        self.app = app
        self.title("업데이트 안내")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(app)
        self.protocol("WM_DELETE_WINDOW", self.close)

        tk.Label(self, text=entry["version"], bg=CARD, fg=PRIMARY,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(28, 2))
        tk.Label(self, text=f"{entry['date']} 업데이트 내용", bg=CARD, fg=MUTED,
                  font=(FONT_NAME, 11)).pack(pady=(0, 16))

        notes_frame = tk.Frame(self, bg=CARD)
        notes_frame.pack(padx=30, pady=(0, 20))
        for note in entry["notes"]:
            tk.Label(notes_frame, text=f"·  {note}", bg=CARD, fg=TEXT, font=(FONT_NAME, 11),
                      anchor="w", justify="left", wraplength=340).pack(fill="x", pady=3)

        btn_row = tk.Frame(self, bg=CARD)
        btn_row.pack(pady=(0, 26))
        RoundButton(btn_row, "오늘 하루 그만보기", self.dismiss_today, bg=DISABLED, fg=TEXT,
                     size=11, bold=False, width=13, pady=8).pack(side="left", padx=6)
        RoundButton(btn_row, "확인", self.close, bg=PRIMARY, size=12, width=8, pady=8).pack(side="left", padx=6)

        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        px = app.winfo_x() + (app.winfo_width() - w) // 2
        py = app.winfo_y() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")

        self.grab_set()
        self.focus_set()

    def close(self):
        self.grab_release()
        self.destroy()

    def dismiss_today(self):
        save_notice_dismiss_date(datetime.now().strftime("%Y-%m-%d"))
        self.close()


class UpdateAvailableDialog(tk.Toplevel):
    """Shown when a background check finds a newer GitHub Release than the
    version currently running. '지금 업데이트' downloads the new exe on a
    background thread (so the UI stays responsive) and hands off to
    download_and_restart_with_update() to swap the file and relaunch."""

    def __init__(self, app, tag, download_url):
        super().__init__(app)
        self.app = app
        self.tag = tag
        self.download_url = download_url
        self.title("업데이트 안내")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(app)
        self.protocol("WM_DELETE_WINDOW", self.close)

        tk.Label(self, text="새 버전이 있어요!", bg=CARD, fg=TEXT,
                  font=(FONT_NAME, 18, "bold")).pack(pady=(28, 6))
        tk.Label(self, text=f"현재 {APP_VERSION}  →  최신 {tag}", bg=CARD, fg=MUTED,
                  font=(FONT_NAME, 12)).pack(pady=(0, 18))

        self.status_label = tk.Label(self, text=" ", bg=CARD, fg=PRIMARY, font=(FONT_NAME, 11))
        self.status_label.pack(pady=(0, 8))

        btn_row = tk.Frame(self, bg=CARD)
        btn_row.pack(pady=(4, 26))
        self.later_btn = RoundButton(btn_row, "나중에", self.close, bg=DISABLED, fg=TEXT,
                                       size=11, bold=False, width=10, pady=8)
        self.later_btn.pack(side="left", padx=6)
        self.update_btn = RoundButton(btn_row, "지금 업데이트", self.on_update_click, bg=PRIMARY,
                                        size=12, width=12, pady=8)
        self.update_btn.pack(side="left", padx=6)

        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        px = app.winfo_x() + (app.winfo_width() - w) // 2
        py = app.winfo_y() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")

        self.grab_set()
        self.focus_set()

    def close(self):
        self.grab_release()
        self.destroy()

    def on_update_click(self):
        if not getattr(sys, "frozen", False):
            self.status_label.config(text="개발 모드에서는 자동 업데이트를 할 수 없어요", fg=RED)
            return
        self.update_btn.config(state="disabled")
        self.later_btn.config(state="disabled")
        self.status_label.config(text="새 버전을 받는 중이에요...", fg=PRIMARY)
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        try:
            download_and_restart_with_update(self.download_url)
            self.app.after(0, self.app.destroy)
        except Exception:
            self.app.after(0, self._on_download_failed)

    def _on_download_failed(self):
        self.status_label.config(text="업데이트를 받지 못했어요. 나중에 다시 시도해주세요", fg=RED)
        self.update_btn.config(state="normal")
        self.later_btn.config(state="normal")


class MainMenuPage(tk.Frame):
    GRADE_ROW1 = [
        {"symbol": "1", "label": "초등 1학년", "desc": "수 · 덧셈 · 뺄셈 · 시계 · 규칙 · 모양", "grade": 1},
        {"symbol": "2", "label": "초등 2학년", "desc": "구구단 · 세 자리 수 · 시간 · 길이", "grade": 2},
        {"symbol": "3", "label": "초등 3학년", "desc": "나눗셈 · 분수 · 소수 · 원 · 각 · 그래프", "grade": 3},
        {"symbol": "4", "label": "초등 4학년", "desc": "각도 · 삼각형 · 사각형 · 평균 · 규칙", "grade": 4},
    ]
    GRADE_ROW2 = [
        {"symbol": "5", "label": "초등 5학년", "desc": "약수 · 배수 · 분수 · 소수 · 비와 비율 · 도형", "grade": 5},
        {"symbol": "6", "label": "초등 6학년", "desc": "분수·소수 나눗셈 · 비례식 · 원의 넓이 등", "grade": 6},
        {"symbol": "📊", "label": "기록", "desc": "지금까지 본 시험 기록 보기", "cmd": "show_history"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        tk.Label(self, text="초등 수학 문제집", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 28, "bold")).pack(pady=(30, 4))
        tk.Label(self, text="학년을 골라보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 13)).pack(pady=(0, 18))

        for row_i, cards in enumerate([self.GRADE_ROW1, self.GRADE_ROW2]):
            row = tk.Frame(self, bg=BG)
            row.pack(pady=8)
            for i, cat in enumerate(cards):
                card = tk.Frame(row, bg=CARD, width=178, height=175,
                                  highlightbackground="#dbe7ee", highlightthickness=1)
                card.grid(row=0, column=i, padx=8)
                card.pack_propagate(False)

                tk.Label(card, text=cat["symbol"], bg=CARD, fg=PRIMARY,
                          font=(FONT_NAME, 19, "bold")).pack(pady=(18, 2))
                tk.Label(card, text=cat["label"], bg=CARD, fg=TEXT, font=(FONT_NAME, 15, "bold")).pack()
                tk.Label(card, text=cat["desc"], bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                          wraplength=150, justify="center").pack(pady=(4, 0))
                if "grade" in cat:
                    cmd = lambda g=cat["grade"]: self.app.show_grade_select(g)
                else:
                    cmd = getattr(self.app, cat["cmd"])
                RoundButton(card, "시작하기", cmd, bg=PRIMARY, size=11,
                             width=9, pady=6).pack(pady=(12, 0))

        link_row = tk.Frame(self, bg=BG)
        link_row.pack(pady=(14, 0))
        RoundButton(link_row, f"{APP_VERSION} · 버전 이력 보기", self.app.show_version_history,
                     bg=BG, fg=MUTED, size=10, bold=False, pady=2).pack(side="left", padx=8)
        RoundButton(link_row, "연산별로 보기", self.app.show_category_index,
                     bg=BG, fg=MUTED, size=10, bold=False, pady=2).pack(side="left", padx=8)


class CategoryIndexPage(tk.Frame):
    """학년별 메뉴가 기본이 된 뒤에도, 예전처럼 연산 종류별로 바로 찾아 들어가고
    싶을 때 쓰는 보조 화면 (문장제·약수와 배수처럼 지금 학년 목록엔 없는 기능도
    전부 여기서는 접근 가능하게 남겨둔다)."""

    CATEGORIES_ROW1 = [
        {"symbol": "＋－×÷", "label": "사칙연산", "desc": "덧셈 · 뺄셈 · 곱셈 · 나눗셈", "cmd": "show_op_select"},
        {"symbol": "▲■●", "label": "도형", "desc": "둘레 · 넓이 · 부피", "cmd": "show_shape_home"},
        {"symbol": "½ 1.2", "label": "분수·소수", "desc": "분수 사칙연산 · 소수 사칙연산", "cmd": "show_fracdec_select"},
    ]
    CATEGORIES_ROW2 = [
        {"symbol": "✎", "label": "문장제", "desc": "문장을 읽고 식 세워 풀기", "cmd": "show_word_select"},
        {"symbol": "5|30", "label": "약수와 배수", "desc": "최대공약수 · 최소공배수", "cmd": "show_numtheory_select"},
        {"symbol": "📏🕐", "label": "측정", "desc": "단위 변환 · 시계 읽기", "cmd": "show_measure_select"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="연산별로 보기", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="학년 대신 연산 종류로 찾아볼 수도 있어요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 13)).pack(pady=(0, 18))

        for cats in [self.CATEGORIES_ROW1, self.CATEGORIES_ROW2]:
            row = tk.Frame(self, bg=BG)
            row.pack(pady=8)
            for i, cat in enumerate(cats):
                card = tk.Frame(row, bg=CARD, width=178, height=175,
                                  highlightbackground="#dbe7ee", highlightthickness=1)
                card.grid(row=0, column=i, padx=8)
                card.pack_propagate(False)
                tk.Label(card, text=cat["symbol"], bg=CARD, fg=PRIMARY,
                          font=(FONT_NAME, 19, "bold")).pack(pady=(18, 2))
                tk.Label(card, text=cat["label"], bg=CARD, fg=TEXT, font=(FONT_NAME, 15, "bold")).pack()
                tk.Label(card, text=cat["desc"], bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                          wraplength=150, justify="center").pack(pady=(4, 0))
                RoundButton(card, "시작하기", getattr(self.app, cat["cmd"]), bg=PRIMARY, size=11,
                             width=9, pady=6).pack(pady=(12, 0))


GRADE_CURRICULUM = {
    1: [
        {"label": "수", "kind": "op", "op": "number_sense"},
        {"label": "덧셈", "kind": "op", "op": "add"},
        {"label": "뺄셈", "kind": "op", "op": "sub"},
        {"label": "시계", "kind": "op", "op": "clock_read"},
        {"label": "규칙", "kind": "op", "op": "pattern"},
        {"label": "모양", "kind": "op", "op": "shape_name"},
    ],
    2: [
        {"label": "구구단", "kind": "op", "op": "times_table"},
        {"label": "세 자리 수", "kind": "op", "op": "place_value"},
        {"label": "시간", "kind": "op", "op": "elapsed_time"},
        {"label": "길이", "kind": "op", "op": "unit_length"},
    ],
    3: [
        {"label": "나눗셈", "kind": "op", "op": "div"},
        {"label": "분수", "kind": "op_group", "ops": ["frac_add", "frac_sub"]},
        {"label": "소수", "kind": "op_group", "ops": ["dec_add", "dec_sub"]},
        {"label": "원", "kind": "op", "op": "circle_relation"},
        {"label": "각", "kind": "op", "op": "angle_basic"},
        {"label": "그래프", "kind": "op", "op": "graph_read"},
    ],
    4: [
        {"label": "각도", "kind": "op", "op": "angle_calc"},
        {"label": "삼각형", "kind": "shape", "key": "triangle_area"},
        {"label": "사각형", "kind": "shape_group",
         "keys": ["square_area", "rect_area", "parallelogram_area", "rhombus_area", "trapezoid_area"]},
        {"label": "평균", "kind": "op", "op": "average"},
        {"label": "규칙", "kind": "op", "op": "pattern"},
    ],
    5: [
        {"label": "약수", "kind": "op", "op": "divisor_count"},
        {"label": "배수", "kind": "op", "op": "multiple_find"},
        {"label": "분수", "kind": "op_group", "ops": ["frac_add", "frac_sub", "frac_mul", "frac_div"]},
        {"label": "소수", "kind": "op_group", "ops": ["dec_add", "dec_sub", "dec_mul", "dec_div"]},
        {"label": "비와 비율", "kind": "op", "op": "ratio"},
        {"label": "도형", "kind": "shape_browse"},
    ],
    6: [
        {"label": "분수 나눗셈", "kind": "op", "op": "frac_div"},
        {"label": "소수 나눗셈", "kind": "op", "op": "dec_div"},
        {"label": "비례식", "kind": "op", "op": "proportion"},
        {"label": "원의 넓이", "kind": "shape", "key": "circle_area"},
        {"label": "공간도형", "kind": "shape_group", "keys": ["cuboid_volume", "cube_volume"]},
        {"label": "그래프", "kind": "op", "op": "graph_read"},
    ],
}


class GradeSelectPage(tk.Frame):
    def __init__(self, master, app, grade):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.grade = grade

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"초등학교 {grade}학년", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 28, "bold")).pack(pady=(16, 4))
        tk.Label(self, text="배우고 싶은 단원을 골라보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 13)).pack(pady=(0, 20))

        grid = tk.Frame(self, bg=BG)
        grid.pack()
        units = GRADE_CURRICULUM[grade]
        for i, unit in enumerate(units):
            card = tk.Frame(grid, bg=CARD, width=178, height=150,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            card.pack_propagate(False)
            tk.Label(card, text=unit["label"], bg=CARD, fg=TEXT,
                      font=(FONT_NAME, 15, "bold")).pack(pady=(28, 0))
            if unit["kind"] == "deferred":
                tk.Label(card, text="준비 중이에요", bg=CARD, fg=MUTED, font=(FONT_NAME, 10)).pack(pady=(6, 0))
                RoundButton(card, "준비 중", lambda: None, bg=DISABLED, fg=DISABLED_TEXT,
                             size=11, width=8, pady=6).pack(pady=(14, 0))
            else:
                RoundButton(card, "풀기", self._make_command(unit), bg=ACCENT, fg=TEXT,
                             size=11, width=8, pady=6).pack(pady=(20, 0))

    def _enter(self, target_fn, *args):
        """Marks 'this grade's own list' as where the target page's back
        button should return to, then navigates -- so 덧셈/뺄셈/시계 등을
        학년 화면에서 들어가면 뒤로가기가 사칙연산/측정 같은 옛 카테고리가
        아니라 항상 이 학년 목록으로 돌아온다."""
        grade = self.grade
        self.app.nav_return = ("← 목록으로", lambda: self.app.show_grade_select(grade))
        self.app.entry_grade = grade
        target_fn(*args)

    def _enter_shape_browse(self):
        """도형 전체 보기는 ShapeSelectPage 이하 화면들이 자기들끼리 이미
        잘 오가므로 nav_return은 건드리지 않고, ShapeSelectPage 자신의
        뒤로가기만 학년으로 돌아가도록 별도 플래그를 쓴다."""
        grade = self.grade
        self.app.shape_browse_return = ("← 목록으로", lambda: self.app.show_grade_select(grade))
        self.app.entry_grade = grade
        self.app.show_shape_select()

    def _make_command(self, unit):
        kind = unit["kind"]
        if kind == "op":
            return lambda op=unit["op"]: self._enter(self.app.show_level_select, op)
        if kind == "op_group":
            return lambda: self.app.show_grade_group(self.grade, unit["label"], "op", unit["ops"])
        if kind == "shape":
            return lambda key=unit["key"]: self._enter(self.app.show_shape_practice, key)
        if kind == "shape_group":
            return lambda: self.app.show_grade_group(self.grade, unit["label"], "shape", unit["keys"])
        if kind == "shape_browse":
            return self._enter_shape_browse
        return lambda: None


class GradeGroupPage(tk.Frame):
    """N학년의 한 단원이 여러 기존 연산(예: 분수 덧셈+뺄셈)이나 여러 도형으로
    이루어져 있을 때, 그 항목들만 모아 보여주는 중간 화면. 뒤로가기는 항상 그
    학년 페이지로 돌아간다 (어느 학년에서 들어왔는지 이미 알고 있으므로)."""

    def __init__(self, master, app, grade, label, kind, items):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.grade, self.label, self.kind, self.items = grade, label, kind, items

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 목록으로", lambda: self.app.show_grade_select(grade), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=label, bg=BG, fg=TEXT,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(18, 2))
        tk.Label(self, text=f"초등 {grade}학년", bg=BG, fg=MUTED, font=(FONT_NAME, 11)).pack(pady=(0, 22))

        row = tk.Frame(self, bg=BG)
        row.pack()
        for i, item in enumerate(items):
            card_label = OP_LABELS[item] if kind == "op" else SHAPE_DEFS_BY_KEY[item]["quantity_label"]
            sub_label = "" if kind == "op" else SHAPE_DEFS_BY_KEY[item]["shape_label"]
            card = tk.Frame(row, bg=CARD, width=170, height=160,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            card.pack_propagate(False)
            if sub_label:
                tk.Label(card, text=sub_label, bg=CARD, fg=MUTED, font=(FONT_NAME, 10)).pack(pady=(20, 0))
            tk.Label(card, text=card_label, bg=CARD, fg=TEXT, font=(FONT_NAME, 15, "bold"),
                      wraplength=150, justify="center").pack(pady=(6 if sub_label else 26, 0))
            if kind == "op":
                cmd = lambda op=item: self._enter(self.app.show_level_select, op)
            else:
                cmd = lambda key=item: self._enter(self.app.show_shape_practice, key)
            RoundButton(card, "풀기", cmd, bg=ACCENT, fg=TEXT, size=11, width=8, pady=6).pack(pady=(14, 0))

    def _enter(self, target_fn, *args):
        # 자기 자신(이 그룹 화면)으로 돌아오도록 지정 -- 학년 화면으로 건너뛰지 않는다.
        grade, label, kind, items = self.grade, self.label, self.kind, self.items
        self.app.nav_return = ("← 목록으로", lambda: self.app.show_grade_group(grade, label, kind, items))
        self.app.entry_grade = grade
        target_fn(*args)


class OpSelectPage(tk.Frame):
    OPS = [
        {"op": "add", "symbol": "➕", "label": "덧셈"},
        {"op": "sub", "symbol": "➖", "label": "뺄셈"},
        {"op": "mul", "symbol": "✖", "label": "곱셈"},
        {"op": "div", "symbol": "➗", "label": "나눗셈"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="사칙연산", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 30, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="풀고 싶은 연산을 골라보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 14)).pack(pady=(0, 36))

        row = tk.Frame(self, bg=BG)
        row.pack()
        for i, spec in enumerate(self.OPS):
            c = self.make_card(row, spec["symbol"], spec["label"],
                                 lambda o=spec["op"]: self.app.show_level_select(o))
            c.grid(row=0, column=i, padx=12)

        row2 = tk.Frame(self, bg=BG)
        row2.pack(pady=(18, 0))
        settings_card = self.make_card(row2, "⚙", "설정", self.app.show_settings,
                                         subtitle="자주 틀리는 숫자 연습", color=PRIMARY_DARK)
        settings_card.grid(row=0, column=0, padx=12)
        test_card = self.make_card(row2, "⏱", "시험", self.app.show_test_setup,
                                     subtitle="제한시간 안에 풀어보기", color=ACCENT_DARK)
        test_card.grid(row=0, column=1, padx=12)

    def make_card(self, master, symbol, label, command, subtitle=None, color=PRIMARY):
        card = tk.Frame(master, bg=CARD, width=170, height=200,
                          highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack_propagate(False)
        tk.Label(card, text=symbol, bg=CARD, fg=color, font=(FONT_NAME, 32, "bold")).pack(pady=(22, 4))
        tk.Label(card, text=label, bg=CARD, fg=TEXT, font=(FONT_NAME, 16, "bold")).pack()
        if subtitle:
            tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                      wraplength=140, justify="center").pack(pady=(3, 0))
        RoundButton(card, "시작하기", command, bg=color, size=11, width=8, pady=7).pack(pady=(14, 0))
        return card


class FracDecSelectPage(tk.Frame):
    FRAC_OPS = [
        {"op": "frac_add", "symbol": "+", "label": "분수 덧셈"},
        {"op": "frac_sub", "symbol": "−", "label": "분수 뺄셈"},
        {"op": "frac_mul", "symbol": "×", "label": "분수 곱셈"},
        {"op": "frac_div", "symbol": "÷", "label": "분수 나눗셈"},
    ]
    DEC_OPS = [
        {"op": "dec_add", "symbol": "+", "label": "소수 덧셈"},
        {"op": "dec_sub", "symbol": "−", "label": "소수 뺄셈"},
        {"op": "dec_mul", "symbol": "×", "label": "소수 곱셈"},
        {"op": "dec_div", "symbol": "÷", "label": "소수 나눗셈"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="분수 · 소수", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 28, "bold")).pack(pady=(16, 4))
        tk.Label(self, text="풀고 싶은 연산을 골라보세요 (설정의 숫자 연습은 여기도 똑같이 적용돼요)",
                  bg=BG, fg=MUTED, font=(FONT_NAME, 12)).pack(pady=(0, 22))

        tk.Label(self, text="분수", bg=BG, fg=TEXT, font=(FONT_NAME, 13, "bold")).pack(anchor="center")
        row1 = tk.Frame(self, bg=BG)
        row1.pack(pady=(6, 18))
        for i, spec in enumerate(self.FRAC_OPS):
            c = self._make_card(row1, spec["symbol"], spec["label"],
                                  lambda o=spec["op"]: self.app.show_level_select(o))
            c.grid(row=0, column=i, padx=12)

        tk.Label(self, text="소수", bg=BG, fg=TEXT, font=(FONT_NAME, 13, "bold")).pack(anchor="center")
        row2 = tk.Frame(self, bg=BG)
        row2.pack(pady=(6, 18))
        for i, spec in enumerate(self.DEC_OPS):
            c = self._make_card(row2, spec["symbol"], spec["label"],
                                  lambda o=spec["op"]: self.app.show_level_select(o))
            c.grid(row=0, column=i, padx=12)

        row3 = tk.Frame(self, bg=BG)
        row3.pack(pady=(4, 16))
        settings_card = self._make_card(row3, "⚙", "설정", lambda: self.app.show_settings("fracdec"),
                                          subtitle="자주 틀리는 숫자 연습", color=PRIMARY_DARK)
        settings_card.grid(row=0, column=0, padx=12)
        test_card = self._make_card(row3, "⏱", "시험", lambda: self.app.show_test_setup("fracdec"),
                                      subtitle="제한시간 안에 풀어보기", color=ACCENT_DARK)
        test_card.grid(row=0, column=1, padx=12)

    def _make_card(self, master, symbol, label, command, subtitle=None, color=PRIMARY):
        card = tk.Frame(master, bg=CARD, width=170, height=150,
                          highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack_propagate(False)
        tk.Label(card, text=symbol, bg=CARD, fg=(color if subtitle else PRIMARY),
                  font=(FONT_NAME, 26, "bold")).pack(pady=(16, 4))
        tk.Label(card, text=label, bg=CARD, fg=TEXT, font=(FONT_NAME, 13, "bold")).pack()
        if subtitle:
            tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                      wraplength=140, justify="center").pack(pady=(2, 0))
        btn_bg, btn_fg = (color, "white") if subtitle else (ACCENT, TEXT)
        RoundButton(card, "시작하기" if subtitle else "풀기", command, bg=btn_bg, fg=btn_fg,
                     size=11, width=8, pady=6).pack(pady=(8, 0))
        return card


class WordSelectPage(tk.Frame):
    WORD_OPS = [
        {"op": "word_add", "symbol": "➕", "label": "덧셈 문장제"},
        {"op": "word_sub", "symbol": "➖", "label": "뺄셈 문장제"},
        {"op": "word_mul", "symbol": "✖", "label": "곱셈 문장제"},
        {"op": "word_div", "symbol": "➗", "label": "나눗셈 문장제"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="문장제", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 30, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="문장을 읽고 어떤 연산인지 생각해서 풀어보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 14)).pack(pady=(0, 36))

        row = tk.Frame(self, bg=BG)
        row.pack()
        for i, spec in enumerate(self.WORD_OPS):
            card = tk.Frame(row, bg=CARD, width=170, height=170,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=spec["symbol"], bg=CARD, fg=PRIMARY, font=(FONT_NAME, 30, "bold")).pack(pady=(22, 4))
            tk.Label(card, text=spec["label"], bg=CARD, fg=TEXT, font=(FONT_NAME, 14, "bold")).pack()
            RoundButton(card, "풀기", lambda o=spec["op"]: self.app.show_level_select(o),
                         bg=ACCENT, fg=TEXT, size=11, width=8, pady=7).pack(pady=(16, 0))

        row2 = tk.Frame(self, bg=BG)
        row2.pack(pady=(18, 0))
        for i, (symbol, label, cmd, subtitle, color) in enumerate([
            ("⚙", "설정", lambda: self.app.show_settings("word"), "자주 틀리는 숫자 연습", PRIMARY_DARK),
            ("⏱", "시험", lambda: self.app.show_test_setup("word"), "제한시간 안에 풀어보기", ACCENT_DARK),
        ]):
            card = tk.Frame(row2, bg=CARD, width=170, height=170,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=symbol, bg=CARD, fg=color, font=(FONT_NAME, 26, "bold")).pack(pady=(22, 4))
            tk.Label(card, text=label, bg=CARD, fg=TEXT, font=(FONT_NAME, 14, "bold")).pack()
            tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                      wraplength=140, justify="center").pack(pady=(3, 0))
            RoundButton(card, "시작하기", cmd, bg=color, size=11, width=8, pady=7).pack(pady=(12, 0))


class NumTheorySelectPage(tk.Frame):
    NUM_OPS = [
        {"op": "gcd", "symbol": "GCD", "label": "최대공약수", "desc": "두 수를 나누는 가장 큰 수"},
        {"op": "lcm", "symbol": "LCM", "label": "최소공배수", "desc": "두 수의 배수 중 가장 작은 수"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="약수와 배수", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 30, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="두 수의 최대공약수와 최소공배수를 구해보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 14)).pack(pady=(0, 36))

        row = tk.Frame(self, bg=BG)
        row.pack()
        for i, spec in enumerate(self.NUM_OPS):
            card = tk.Frame(row, bg=CARD, width=210, height=190,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=12)
            card.pack_propagate(False)
            tk.Label(card, text=spec["symbol"], bg=CARD, fg=PRIMARY, font=(FONT_NAME, 22, "bold")).pack(pady=(24, 4))
            tk.Label(card, text=spec["label"], bg=CARD, fg=TEXT, font=(FONT_NAME, 16, "bold")).pack()
            tk.Label(card, text=spec["desc"], bg=CARD, fg=MUTED, font=(FONT_NAME, 10),
                      wraplength=170, justify="center").pack(pady=(4, 0))
            RoundButton(card, "풀기", lambda o=spec["op"]: self.app.show_level_select(o),
                         bg=ACCENT, fg=TEXT, size=11, width=8, pady=7).pack(pady=(14, 0))

        row2 = tk.Frame(self, bg=BG)
        row2.pack(pady=(18, 0))
        for i, (symbol, label, cmd, subtitle, color) in enumerate([
            ("⚙", "설정", lambda: self.app.show_settings("numtheory"), "자주 틀리는 숫자 연습", PRIMARY_DARK),
            ("⏱", "시험", lambda: self.app.show_test_setup("numtheory"), "제한시간 안에 풀어보기", ACCENT_DARK),
        ]):
            card = tk.Frame(row2, bg=CARD, width=170, height=170,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=symbol, bg=CARD, fg=color, font=(FONT_NAME, 26, "bold")).pack(pady=(22, 4))
            tk.Label(card, text=label, bg=CARD, fg=TEXT, font=(FONT_NAME, 14, "bold")).pack()
            tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                      wraplength=140, justify="center").pack(pady=(3, 0))
            RoundButton(card, "시작하기", cmd, bg=color, size=11, width=8, pady=7).pack(pady=(12, 0))


class MeasureSelectPage(tk.Frame):
    MEASURE_OPS = [
        {"op": "unit_length", "symbol": "📏", "label": "길이 단위 변환"},
        {"op": "unit_weight", "symbol": "⚖", "label": "무게 단위 변환"},
        {"op": "unit_volume", "symbol": "🥤", "label": "들이 단위 변환"},
        {"op": "clock_read", "symbol": "🕐", "label": "시계 읽기"},
    ]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="측정", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 30, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="단위 변환과 시계 읽기를 연습해보세요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 14)).pack(pady=(0, 36))

        row = tk.Frame(self, bg=BG)
        row.pack()
        for i, spec in enumerate(self.MEASURE_OPS):
            card = tk.Frame(row, bg=CARD, width=170, height=170,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=spec["symbol"], bg=CARD, fg=PRIMARY, font=(FONT_NAME, 26, "bold")).pack(pady=(22, 4))
            tk.Label(card, text=spec["label"], bg=CARD, fg=TEXT, font=(FONT_NAME, 13, "bold"),
                      wraplength=140, justify="center").pack()
            RoundButton(card, "풀기", lambda o=spec["op"]: self.app.show_level_select(o),
                         bg=ACCENT, fg=TEXT, size=11, width=8, pady=7).pack(pady=(16, 0))

        row2 = tk.Frame(self, bg=BG)
        row2.pack(pady=(18, 0))
        for i, (symbol, label, cmd, subtitle, color) in enumerate([
            ("⚙", "설정", lambda: self.app.show_settings("measure"), "자주 틀리는 숫자 연습", PRIMARY_DARK),
            ("⏱", "시험", lambda: self.app.show_test_setup("measure"), "제한시간 안에 풀어보기", ACCENT_DARK),
        ]):
            card = tk.Frame(row2, bg=CARD, width=170, height=170,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)
            tk.Label(card, text=symbol, bg=CARD, fg=color, font=(FONT_NAME, 26, "bold")).pack(pady=(22, 4))
            tk.Label(card, text=label, bg=CARD, fg=TEXT, font=(FONT_NAME, 14, "bold")).pack()
            tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=(FONT_NAME, 9),
                      wraplength=140, justify="center").pack(pady=(3, 0))
            RoundButton(card, "시작하기", cmd, bg=color, size=11, width=8, pady=7).pack(pady=(12, 0))


class SettingsPage(tk.Frame):
    def __init__(self, master, app, category="arith"):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        back_label, back_cmd = CATEGORY_BACK[category]
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, back_label, getattr(self.app, back_cmd), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="설정", bg=BG, fg=TEXT, font=(FONT_NAME, 28, "bold")).pack(pady=(24, 8))
        tk.Label(self, text="자주 틀리는 숫자를 선택하면, 그 숫자가 들어간 문제가 더 자주 나와요",
                  bg=BG, fg=MUTED, font=(FONT_NAME, 13)).pack()
        tk.Label(self, text="(예: 1을 선택하면 1, 10~19, 21, 31, 41 처럼 1이 들어간 숫자가 더 자주 출제돼요)",
                  bg=BG, fg=MUTED, font=(FONT_NAME, 11)).pack(pady=(2, 30))

        grid = tk.Frame(self, bg=BG)
        grid.pack()
        self.buttons = {}
        for d in range(10):
            btn = tk.Button(grid, text=str(d), font=(FONT_NAME, 20, "bold"),
                              width=3, height=1, relief="flat", bd=0, cursor="hand2",
                              highlightbackground="#dbe7ee", highlightthickness=1,
                              command=lambda dd=d: self.toggle(dd))
            btn.grid(row=d // 5, column=d % 5, padx=10, pady=10)
            self.buttons[d] = btn

        self.status_label = tk.Label(self, text="", bg=BG, fg=PRIMARY, font=(FONT_NAME, 13, "bold"))
        self.status_label.pack(pady=(24, 0))

        RoundButton(self, "전체 초기화", self.reset, bg=DISABLED, fg=TEXT, size=12,
                     width=12, pady=8).pack(pady=(18, 0))

        self.refresh()

    def toggle(self, d):
        key = str(d)
        if key in BOOSTED_DIGITS:
            BOOSTED_DIGITS.discard(key)
        else:
            BOOSTED_DIGITS.add(key)
        self.refresh()

    def reset(self):
        BOOSTED_DIGITS.clear()
        self.refresh()

    def refresh(self):
        for d, btn in self.buttons.items():
            if str(d) in BOOSTED_DIGITS:
                btn.config(bg=ACCENT, fg=TEXT, activebackground=ACCENT_DARK)
            else:
                btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")
        if BOOSTED_DIGITS:
            nums = ", ".join(sorted(BOOSTED_DIGITS))
            self.status_label.config(text=f"선택된 숫자: {nums}  (이 숫자가 더 자주 나와요)")
        else:
            self.status_label.config(text="선택된 숫자 없음 — 모든 숫자가 균등한 확률로 나와요")


class LevelSelectPage(tk.Frame):
    def __init__(self, master, app, op):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.op = op

        if self.app.nav_return:
            # NOT consumed here: PracticePage sends the user back to this
            # same LevelSelectPage repeatedly within one grade-entered
            # session, and each of those return visits needs the same
            # "돌아가면 학년 목록" back-target, not just the first one.
            # It's reset instead by every "index" page (show_main_menu,
            # show_op_select, ...) so it can't leak into an unrelated
            # later visit that didn't come from a grade page.
            back_label, back_action = self.app.nav_return
        else:
            back_label, back_cmd = CATEGORY_BACK[OP_CATEGORY[op]]
            back_action = getattr(self.app, back_cmd)
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, back_label, back_action, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"{OP_LABELS[op]} 난이도 선택", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(18, 4))
        if self.app.entry_grade:
            tk.Label(self, text=f"초등 {self.app.entry_grade}학년", bg=BG, fg=MUTED,
                      font=(FONT_NAME, 11)).pack()
        if op in FORMULA_TEXT:
            tk.Label(self, text=f"공식: {FORMULA_TEXT[op]}", bg=BG, fg=PRIMARY_DARK,
                      font=(FONT_NAME, 11, "bold")).pack(pady=(4, 0))
        tk.Label(self, text=LEVEL_CAPTION_OVERRIDES.get(op, LEVEL_CAPTION_DEFAULT), bg=BG, fg=MUTED,
                  font=(FONT_NAME, 12)).pack(pady=(0, 26))

        # 구구단(2~9단)처럼 레벨이 많은 연산도 창 밖으로 넘치지 않게 스크롤 처리한다.
        scroll = ScrollableFrame(self, bg=BG, height=560)
        scroll.pack(fill="both", expand=True, padx=60, pady=(0, 10))

        for lv in OP_LEVELS_MAP[op]:
            self.make_row(scroll.inner, lv)

    def make_row(self, master, lv):
        row = tk.Frame(master, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        row.pack(fill="x", pady=6)

        badge = tk.Frame(row, bg=PRIMARY, width=64, height=64)
        badge.pack(side="left", padx=16, pady=12)
        badge.pack_propagate(False)
        tk.Label(badge, text=lv["title"], bg=PRIMARY, fg="white",
                  font=(FONT_NAME, 13, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        text_col = tk.Frame(row, bg=CARD)
        text_col.pack(side="left", fill="both", expand=True, pady=12)
        tk.Label(text_col, text=lv["desc"], bg=CARD, fg=TEXT,
                  font=(FONT_NAME, 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(text_col, text=lv["example"], bg=CARD, fg=MUTED,
                  font=(FONT_NAME, 11), anchor="w").pack(fill="x")

        RoundButton(row, "풀기", lambda l=lv["level"]: self.app.show_practice(self.op, l),
                     bg=ACCENT, fg=TEXT, size=12, width=6, pady=8).pack(side="right", padx=16)


def _fmt_num(x):
    """Formats an int or float for display without ugly float artifacts."""
    return f"{x:g}" if isinstance(x, float) else str(x)


class PracticePage(tk.Frame):
    def __init__(self, master, app, op, level):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.op = op
        self.level = level
        self.mode = OP_ANSWER_MODE[op]
        self.uses_fraction_input = self.mode in ("div_fraction", "frac_pair")
        self.uses_clock_input = self.mode == "clock"
        self.uses_text_problem = self.mode in ("text_int", "text_decimal")
        self.uses_diagram = op in DIAGRAM_OPS
        self.uses_choice_input = self.mode == "choice"

        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.state = "answering"  # answering -> checked -> answering ...
        self.a = self.b = self.answer = None
        self.n1 = self.d1 = self.n2 = self.d2 = None
        self.correct_num = self.correct_den = None
        self.hour = self.minute = None
        self.explain = None
        self.choices = self.correct_choice = None
        self.choice_buttons = []
        self.recent = deque(maxlen=DEDUP_WINDOW)

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 목록으로", lambda: self.app.show_level_select(self.op), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(top, text=f"{OP_LABELS[op]} Lv.{level}", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 16, "bold")).pack(side="left", padx=(18, 0))
        if self.app.entry_grade:
            tk.Label(top, text=f"초등 {self.app.entry_grade}학년", bg=BG, fg=MUTED,
                      font=(FONT_NAME, 11)).pack(side="left", padx=(10, 0))

        self.score_label = tk.Label(top, text="", bg=BG, fg=MUTED, font=(FONT_NAME, 13))
        self.score_label.pack(side="right")

        if op in FORMULA_TEXT:
            formula_row = tk.Frame(self, bg=BG)
            formula_row.pack(fill="x", padx=24, pady=(6, 0))
            tk.Label(formula_row, text=f"공식: {FORMULA_TEXT[op]}", bg=BG, fg=PRIMARY_DARK,
                      font=(FONT_NAME, 11, "bold")).pack(side="left")

        card = tk.Frame(self, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack(padx=60, pady=(30, 20), fill="both", expand=True)

        if self.uses_clock_input:
            self.canvas = tk.Canvas(card, width=300, height=300, bg=CARD, highlightthickness=0)
            self.canvas.pack(pady=(16, 6))
        elif self.uses_diagram:
            self.canvas = tk.Canvas(card, width=240, height=170, bg=CARD, highlightthickness=0)
            self.canvas.pack(pady=(20, 4))
        elif self.uses_choice_input:
            self.canvas = tk.Canvas(card, width=200, height=170, bg=CARD, highlightthickness=0)
            self.canvas.pack(pady=(20, 4))

        prob_size = {"text_int": 17, "text_decimal": 17, "clock": 15, "frac_pair": 40, "choice": 17}.get(self.mode, 46)
        self.problem_label = tk.Label(card, text="", bg=CARD, fg=TEXT, wraplength=560, justify="center",
                                        font=(FONT_NAME, prob_size,
                                              "bold" if not (self.uses_text_problem or self.uses_choice_input) else "normal"))
        self.problem_label.pack(pady=(16 if (self.uses_clock_input or self.uses_diagram or self.uses_choice_input) else 60, 16))

        input_row = tk.Frame(card, bg=CARD)
        input_row.pack(pady=6)

        vcmd = (self.register(self._validate_num), "%P")

        if self.uses_clock_input:
            self.hour_var = tk.StringVar()
            self.minute_var = tk.StringVar()
            self.hour_entry = tk.Entry(input_row, textvariable=self.hour_var, font=(FONT_NAME, 24),
                                         width=3, justify="center", relief="solid", bd=2,
                                         validate="key", validatecommand=vcmd)
            self.hour_entry.pack(side="left", ipady=4)
            tk.Label(input_row, text="시", bg=CARD, fg=TEXT, font=(FONT_NAME, 18)).pack(side="left", padx=(6, 14))
            self.minute_entry = tk.Entry(input_row, textvariable=self.minute_var, font=(FONT_NAME, 24),
                                           width=3, justify="center", relief="solid", bd=2,
                                           validate="key", validatecommand=vcmd)
            self.minute_entry.pack(side="left", ipady=4)
            tk.Label(input_row, text="분", bg=CARD, fg=TEXT, font=(FONT_NAME, 18)).pack(side="left", padx=(6, 0))
            self.entry = self.hour_entry
        elif self.uses_fraction_input:
            frac_col = tk.Frame(input_row, bg=CARD)
            frac_col.pack()
            self.num_var = tk.StringVar()
            self.den_var = tk.StringVar()
            self.num_entry = tk.Entry(frac_col, textvariable=self.num_var, font=(FONT_NAME, 22),
                                        width=6, justify="center", relief="solid", bd=2,
                                        validate="key", validatecommand=vcmd)
            self.num_entry.pack(pady=(0, 5))
            tk.Frame(frac_col, bg=TEXT, height=2, width=110).pack()
            self.den_entry = tk.Entry(frac_col, textvariable=self.den_var, font=(FONT_NAME, 22),
                                        width=6, justify="center", relief="solid", bd=2,
                                        validate="key", validatecommand=vcmd)
            self.den_entry.pack(pady=(5, 0))
            self.entry = self.num_entry
            if self.mode == "div_fraction":
                tk.Label(card, text="나누어떨어지지 않으면 분수로 답하세요 (분모를 비우면 자연수로 채점돼요)",
                          bg=CARD, fg=MUTED, font=(FONT_NAME, 10)).pack(pady=(10, 0))
            else:
                tk.Label(card, text="분수로 답하세요 (분모를 비우면 자연수로 채점돼요)",
                          bg=CARD, fg=MUTED, font=(FONT_NAME, 10)).pack(pady=(10, 0))
        elif self.uses_choice_input:
            self.choice_row = tk.Frame(input_row, bg=CARD)
            self.choice_row.pack()
        else:
            self.answer_var = tk.StringVar()
            self.entry = tk.Entry(input_row, textvariable=self.answer_var, font=(FONT_NAME, 28),
                                    width=8, justify="center", relief="solid", bd=2,
                                    validate="key", validatecommand=vcmd)
            self.entry.pack(side="left", ipady=6)

        self.feedback_label = tk.Label(card, text=" ", bg=CARD, font=(FONT_NAME, 16, "bold"),
                                         wraplength=560, justify="center")
        self.feedback_label.pack(pady=(18, 0))

        self.main_btn = RoundButton(card, "확인", self.on_main_button, bg=ACCENT, fg=TEXT,
                                      size=16, width=12, pady=12)
        self.main_btn.pack(pady=(22, 30))

        self.app.set_enter_handler(self.on_main_button)
        self.next_problem()

    def _validate_num(self, proposed):
        if proposed == "":
            return True
        if self.mode in ("decimal", "text_decimal"):
            core = proposed.lstrip("-")
            return core.count(".") <= 1 and core.replace(".", "").isdigit()
        return proposed.lstrip("-").isdigit()

    def update_score(self):
        self.score_label.config(
            text=f"맞음 {self.correct_count}   틀림 {self.wrong_count}   연속정답 {self.streak}"
        )

    def next_problem(self):
        gen = lambda lvl: gen_raw_with_dedup(OP_GEN[self.op], self.mode, lvl, self.recent)
        sym = OP_SYMBOL.get(self.op, "")

        if self.mode == "div_fraction":
            self.a, self.b, self.correct_num, self.correct_den = gen(self.level)
            problem_text = f"{self.a}  {sym}  {self.b}  =  ?"
        elif self.mode == "frac_pair":
            self.n1, self.d1, self.n2, self.d2, self.correct_num, self.correct_den = gen(self.level)
            op1 = str(self.n1) if self.d1 == 1 else f"{self.n1}/{self.d1}"
            op2 = str(self.n2) if self.d2 == 1 else f"{self.n2}/{self.d2}"
            problem_text = f"{op1}   {sym}   {op2}   =   ?"
        elif self.mode in ("text_int", "text_decimal"):
            result = gen(self.level)
            problem_text, self.answer = result[0], result[1]
            extra = result[2] if len(result) > 2 else {}
            self.explain = extra.get("explain")
            if self.uses_diagram:
                draw_kind, draw_data = extra["draw"]
                if draw_kind == "shape_circle":
                    draw_shape_diagram(self.canvas, "원", draw_data)
                elif draw_kind == "angle":
                    draw_angle_diagram(self.canvas, draw_data)
                elif draw_kind == "bargraph":
                    cats, values, gstep = draw_data
                    draw_bar_graph(self.canvas, cats, values, gstep)
        elif self.mode == "clock":
            self.hour, self.minute = gen(self.level)
            draw_clock_diagram(self.canvas, self.hour, self.minute)
            problem_text = "지금 시각은 몇 시 몇 분일까요?"
        elif self.mode == "choice":
            problem_text, self.choices, self.correct_choice = gen(self.level)
            draw_named_shape(self.canvas, self.correct_choice)
        else:
            self.a, self.b, self.answer = gen(self.level)
            problem_text = f"{_fmt_num(self.a)}  {sym}  {_fmt_num(self.b)}  =  ?"

        if self.uses_clock_input:
            self.hour_var.set("")
            self.minute_var.set("")
            self.hour_entry.config(state="normal", disabledbackground=CARD)
            self.minute_entry.config(state="normal", disabledbackground=CARD)
            self.hour_entry.focus_set()
        elif self.uses_fraction_input:
            self.num_var.set("")
            self.den_var.set("")
            self.num_entry.config(state="normal", disabledbackground=CARD)
            self.den_entry.config(state="normal", disabledbackground=CARD)
            self.num_entry.focus_set()
        elif self.uses_choice_input:
            for b in self.choice_buttons:
                b.destroy()
            self.choice_buttons = []
            for choice_text in self.choices:
                b = RoundButton(self.choice_row, choice_text, lambda c=choice_text: self.on_choice_click(c),
                                  bg=CARD, fg=TEXT, size=13, width=8, pady=10,
                                  highlightbackground="#dbe7ee", highlightthickness=1)
                b.pack(side="left", padx=6)
                self.choice_buttons.append(b)
        else:
            self.answer_var.set("")
            self.entry.config(state="normal", disabledbackground=CARD)
            self.entry.focus_set()

        self.problem_label.config(text=problem_text)
        self.feedback_label.config(text=" ", fg=TEXT)
        if self.uses_choice_input:
            self.main_btn.pack_forget()
        else:
            self.main_btn.config(text="확인", bg=ACCENT, fg=TEXT)
        self.update_score()
        self.state = "answering"

    def on_main_button(self):
        if self.state == "answering":
            self.check_answer()
        else:
            self.next_problem()

    def check_answer(self):
        if self.uses_choice_input:
            return  # 선택지를 클릭하는 것 자체가 제출이라 확인/Enter로는 채점하지 않는다
        if self.uses_clock_input:
            h_raw = self.hour_var.get().strip()
            m_raw = self.minute_var.get().strip()
            if h_raw == "" or m_raw == "":
                return
            is_correct = int(h_raw) == self.hour and int(m_raw) == self.minute
            correct_text = f"{self.hour}시 {self.minute}분"
        elif self.uses_fraction_input:
            num_raw = self.num_var.get().strip()
            den_raw = self.den_var.get().strip()
            if num_raw == "" or num_raw == "-":
                return
            user_num = int(num_raw)
            user_den = int(den_raw) if den_raw not in ("", "-") else 1
            is_correct = user_den != 0 and user_num * self.correct_den == self.correct_num * user_den
            correct_text = (str(self.correct_num) if self.correct_den == 1
                             else f"{self.correct_num}/{self.correct_den}")
        elif self.mode in ("decimal", "text_decimal"):
            raw = self.answer_var.get().strip()
            if raw in ("", "-", "."):
                return
            try:
                user_val = float(raw)
            except ValueError:
                return
            is_correct = abs(user_val - self.answer) < 0.005
            correct_text = _fmt_num(self.answer)
        else:
            raw = self.answer_var.get().strip()
            if raw == "" or raw == "-":
                return
            user_val = int(raw)
            is_correct = user_val == self.answer
            correct_text = str(self.answer)

        if self.uses_clock_input:
            self.hour_entry.config(state="disabled")
            self.minute_entry.config(state="disabled")
        elif self.uses_fraction_input:
            self.num_entry.config(state="disabled")
            self.den_entry.config(state="disabled")
        else:
            self.entry.config(state="disabled")
        self._apply_result(is_correct, correct_text)
        self.focus_set()
        self.main_btn.focus_set()

    def on_choice_click(self, chosen):
        if self.state != "answering":
            return
        is_correct = chosen == self.correct_choice
        for b in self.choice_buttons:
            if b.cget("text") == self.correct_choice:
                b.config(bg=GREEN, fg="white")
            elif b.cget("text") == chosen:
                b.config(bg=RED, fg="white")
            b.config(state="disabled")
        self.main_btn.pack(pady=(22, 30))
        self._apply_result(is_correct, self.correct_choice)
        self.focus_set()
        self.main_btn.focus_set()

    def _apply_result(self, is_correct, correct_text):
        if is_correct:
            self.correct_count += 1
            self.streak += 1
            msg = "정답이에요! 참 잘했어요"
            if self.explain:
                msg += f"\n{self.explain}"
            self.feedback_label.config(text=msg, fg=GREEN_DARK)
        else:
            self.wrong_count += 1
            self.streak = 0
            msg = f"오답이에요. 정답은 {correct_text}예요"
            if self.explain:
                msg += f"\n{self.explain}"
            self.feedback_label.config(text=msg, fg=RED)

        self.main_btn.config(text="다음 문제 →", bg=PRIMARY, fg="white")
        self.update_score()
        self.state = "checked"


# ---------------------------------------------------------------------------
# 시험(TestPage)과 오답노트(WrongAnswerReviewPage)가 함께 쓰는 모드-공통 헬퍼.
# PracticePage는 이미 검증된 코드라 건드리지 않고, 같은 모드별 규칙(정수/소수/
# 분수쌍/서술형/시계)을 여기서 독립적으로 재구현해 두 화면이 공유한다.
# ---------------------------------------------------------------------------
def _wrap_question(op, mode, raw):
    """Pure formatting: turns a raw OP_GEN(level) tuple into the mode-tagged
    display dict. Kept separate from generation so gen_question_dict_dedup
    can retry the random draw without re-deriving the formatting rules."""
    sym = OP_SYMBOL.get(op, "")
    if mode == "div_fraction":
        a, b, num, den = raw
        return {"mode": mode, "prob_text": f"{a}  {sym}  {b}  =  ?", "num": num, "den": den}
    if mode == "frac_pair":
        n1, d1, n2, d2, num, den = raw
        op1 = str(n1) if d1 == 1 else f"{n1}/{d1}"
        op2 = str(n2) if d2 == 1 else f"{n2}/{d2}"
        return {"mode": mode, "prob_text": f"{op1}   {sym}   {op2}   =   ?", "num": num, "den": den}
    if mode in ("text_int", "text_decimal"):
        # some generators (e.g. gen_pattern) return a 3rd "extra" dict (used
        # only by PracticePage, for things like an answer explanation) --
        # TestPage/WrongAnswerReviewPage just ignore it here.
        text, answer = raw[0], raw[1]
        return {"mode": mode, "prob_text": text, "answer": answer}
    if mode == "clock":
        hour, minute = raw
        return {"mode": mode, "prob_text": "지금 시각은 몇 시 몇 분일까요?", "hour": hour, "minute": minute}
    a, b, answer = raw  # "int" or "decimal"
    return {"mode": mode, "prob_text": f"{_fmt_num(a)}  {sym}  {_fmt_num(b)}  =  ?", "answer": answer}


def gen_question_dict(op, level):
    """Generates one question as a mode-tagged dict that both display code
    and grading code can handle uniformly, regardless of which of the 7
    answer modes `op` uses."""
    mode = OP_ANSWER_MODE[op]
    raw = OP_GEN[op](level)
    return _wrap_question(op, mode, raw)


def _raw_signature(mode, raw):
    """The subset of a raw OP_GEN() tuple that defines a question's numeric
    identity for dedup purposes (i.e. excluding the computed answer, which
    isn't itself 'the numbers' -- word_add's a+b=12 and a+b=12 from a
    different a,b pair are different questions)."""
    if mode in ("div_fraction",):
        return raw[:2]
    if mode == "frac_pair":
        return raw[:4]
    if mode == "clock":
        return raw
    if mode in ("text_int", "text_decimal"):
        return (raw[0],)  # the rendered sentence itself (its numbers included)
    return raw[:2]  # "int" / "decimal": (a, b)


DEDUP_WINDOW = 10


def gen_raw_with_dedup(gen_fn, mode, level, recent, max_tries=30):
    """Calls gen_fn(level) until its number-signature hasn't shown up in the
    last DEDUP_WINDOW draws recorded in `recent` (a deque), so a student
    doesn't see the exact same numbers again too soon. Falls back to
    whatever was last generated if max_tries is exhausted -- some very
    narrow ranges (e.g. Lv.1 클록 with few hour/minute combos) may not have
    10 distinct options, and a rare repeat beats hanging or crashing."""
    raw = None
    for _ in range(max_tries):
        raw = gen_fn(level)
        sig = _raw_signature(mode, raw)
        if sig not in recent:
            recent.append(sig)
            return raw
    recent.append(_raw_signature(mode, raw))
    return raw


def gen_question_dict_dedup(op, level, recent):
    mode = OP_ANSWER_MODE[op]
    raw = gen_raw_with_dedup(OP_GEN[op], mode, level, recent)
    return _wrap_question(op, mode, raw)


def gen_shape_with_dedup(gen_fn, recent, max_tries=30):
    """Same idea as gen_raw_with_dedup, for 도형 generators -- these take no
    level and return (dims, answer) instead of an OP_GEN-style tuple, so the
    signature is just the dimension values themselves."""
    result = None
    for _ in range(max_tries):
        result = gen_fn()
        sig = tuple(result[0].values())
        if sig not in recent:
            recent.append(sig)
            return result
    recent.append(tuple(result[0].values()))
    return result


def grade_question(q, user_answer):
    """Returns (is_correct, correct_answer_text) for a question dict from
    gen_question_dict and a user_answer read via read_mode_input (or None
    for 'left blank')."""
    mode = q["mode"]
    if user_answer is None:
        ok = False
    elif mode in ("div_fraction", "frac_pair"):
        user_num, user_den = user_answer
        ok = user_den != 0 and user_num * q["den"] == q["num"] * user_den
    elif mode == "clock":
        ok = user_answer == (q["hour"], q["minute"])
    elif mode in ("decimal", "text_decimal"):
        ok = abs(user_answer - q["answer"]) < 0.005
    else:
        ok = user_answer == q["answer"]

    if mode in ("div_fraction", "frac_pair"):
        correct_text = str(q["num"]) if q["den"] == 1 else f"{q['num']}/{q['den']}"
    elif mode == "clock":
        correct_text = f"{q['hour']}시 {q['minute']}분"
    elif mode in ("decimal", "text_decimal"):
        correct_text = _fmt_num(q["answer"])
    else:
        correct_text = str(q["answer"])
    return ok, correct_text


def format_user_answer(mode, ua):
    if ua is None:
        return "안 씀"
    if mode in ("div_fraction", "frac_pair"):
        num, den = ua
        return str(num) if den == 1 else f"{num}/{den}"
    if mode == "clock":
        h, m = ua
        return f"{h}시 {m}분"
    if mode in ("decimal", "text_decimal"):
        return _fmt_num(ua)
    return str(ua)


def validate_mode_num(mode, proposed):
    if proposed == "":
        return True
    if mode in ("decimal", "text_decimal"):
        core = proposed.lstrip("-")
        return core.count(".") <= 1 and core.replace(".", "").isdigit()
    return proposed.lstrip("-").isdigit()


def build_question_display(parent, mode):
    """Builds the question canvas (clock only) + label, sized/fonted to fit
    the mode. Returns (canvas_or_None, label)."""
    canvas = None
    if mode == "clock":
        canvas = tk.Canvas(parent, width=300, height=300, bg=CARD, highlightthickness=0)
        canvas.pack(pady=(6, 4))
    size = {"text_int": 16, "text_decimal": 16, "clock": 15, "frac_pair": 34}.get(mode, 38)
    weight = "normal" if mode in ("text_int", "text_decimal") else "bold"
    label = tk.Label(parent, text="", bg=CARD, fg=TEXT, wraplength=560, justify="center",
                       font=(FONT_NAME, size, weight))
    label.pack(pady=(6, 10))
    return canvas, label


def build_mode_input(parent, mode, register_cmd):
    """Builds the answer-input widgets for `mode` and returns a dict of
    references (`entries`, `focus`, plus mode-specific StringVars) that
    clear_mode_input/disable_mode_input/read_mode_input operate on."""
    widgets = {"mode": mode}
    if mode == "clock":
        row = tk.Frame(parent, bg=CARD)
        row.pack(pady=6)
        hour_var, minute_var = tk.StringVar(), tk.StringVar()
        hour_entry = tk.Entry(row, textvariable=hour_var, font=(FONT_NAME, 24), width=3,
                                justify="center", relief="solid", bd=2,
                                validate="key", validatecommand=register_cmd)
        hour_entry.pack(side="left", ipady=4)
        tk.Label(row, text="시", bg=CARD, fg=TEXT, font=(FONT_NAME, 18)).pack(side="left", padx=(6, 14))
        minute_entry = tk.Entry(row, textvariable=minute_var, font=(FONT_NAME, 24), width=3,
                                  justify="center", relief="solid", bd=2,
                                  validate="key", validatecommand=register_cmd)
        minute_entry.pack(side="left", ipady=4)
        tk.Label(row, text="분", bg=CARD, fg=TEXT, font=(FONT_NAME, 18)).pack(side="left", padx=(6, 0))
        widgets.update(hour_var=hour_var, minute_var=minute_var,
                        entries=[hour_entry, minute_entry], focus=hour_entry)
    elif mode in ("div_fraction", "frac_pair"):
        frac_col = tk.Frame(parent, bg=CARD)
        frac_col.pack()
        num_var, den_var = tk.StringVar(), tk.StringVar()
        num_entry = tk.Entry(frac_col, textvariable=num_var, font=(FONT_NAME, 22), width=6,
                               justify="center", relief="solid", bd=2,
                               validate="key", validatecommand=register_cmd)
        num_entry.pack(pady=(0, 5))
        tk.Frame(frac_col, bg=TEXT, height=2, width=110).pack()
        den_entry = tk.Entry(frac_col, textvariable=den_var, font=(FONT_NAME, 22), width=6,
                               justify="center", relief="solid", bd=2,
                               validate="key", validatecommand=register_cmd)
        den_entry.pack(pady=(5, 0))
        widgets.update(num_var=num_var, den_var=den_var,
                        entries=[num_entry, den_entry], focus=num_entry)
    else:
        answer_var = tk.StringVar()
        entry = tk.Entry(parent, textvariable=answer_var, font=(FONT_NAME, 28), width=8,
                           justify="center", relief="solid", bd=2,
                           validate="key", validatecommand=register_cmd)
        entry.pack(ipady=6)
        widgets.update(answer_var=answer_var, entries=[entry], focus=entry)
    return widgets


def clear_mode_input(widgets):
    mode = widgets["mode"]
    if mode == "clock":
        widgets["hour_var"].set("")
        widgets["minute_var"].set("")
    elif mode in ("div_fraction", "frac_pair"):
        widgets["num_var"].set("")
        widgets["den_var"].set("")
    else:
        widgets["answer_var"].set("")
    for e in widgets["entries"]:
        e.config(state="normal", disabledbackground=CARD)
    widgets["focus"].focus_set()


def disable_mode_input(widgets):
    for e in widgets["entries"]:
        e.config(state="disabled")


def read_mode_input(widgets):
    """Returns a user-answer value shaped for grade_question(), or None if
    left blank/incomplete."""
    mode = widgets["mode"]
    if mode == "clock":
        h, m = widgets["hour_var"].get().strip(), widgets["minute_var"].get().strip()
        if h == "" or m == "":
            return None
        return (int(h), int(m))
    if mode in ("div_fraction", "frac_pair"):
        num_raw = widgets["num_var"].get().strip()
        den_raw = widgets["den_var"].get().strip()
        if num_raw in ("", "-"):
            return None
        user_num = int(num_raw)
        user_den = int(den_raw) if den_raw not in ("", "-") else 1
        return (user_num, user_den)
    raw = widgets["answer_var"].get().strip()
    if raw in ("", "-", "."):
        return None
    if mode in ("decimal", "text_decimal"):
        try:
            return float(raw)
        except ValueError:
            return None
    return int(raw)


class ScrollableFrame(tk.Frame):
    """A vertically scrollable area. Put widgets inside `.inner`."""

    def __init__(self, master, bg=BG, height=220):
        super().__init__(master, bg=bg)
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0, height=height)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg)

        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # scope the mousewheel binding to only while the cursor is over this
        # canvas, so it doesn't leak into other pages/windows
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))


class TestSetupPage(tk.Frame):
    def __init__(self, master, app, category="arith"):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.category = category
        self.ops = TEST_OPS_BY_CATEGORY[category]

        self.selected_op = self.ops[0]
        self.selected_level = 1
        self.selected_count = TEST_QUESTION_COUNTS[0]
        self.selected_minutes = TEST_TIME_LIMITS[1]

        back_label, back_cmd = CATEGORY_BACK[category]
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, back_label, getattr(self.app, back_cmd), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"{CATEGORY_NAME[category]} 시험 설정", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(12, 20))

        self.section("어떤 문제로 볼까요?")
        self.build_chip_row(self, [(op, OP_LABELS[op]) for op in self.ops],
                              lambda: self.selected_op, self.pick_op, max_cols=4)

        self.section("난이도는요?")
        self.level_container = tk.Frame(self, bg=BG)
        self.level_container.pack(pady=(6, 0))
        self.rebuild_level_row()

        self.section("몇 문제 풀까요?")
        self.build_number_row(self, TEST_QUESTION_COUNTS, "문제",
                                lambda: self.selected_count, self.pick_count,
                                COUNT_MIN, COUNT_MAX)

        self.section("제한시간은요?")
        self.build_number_row(self, TEST_TIME_LIMITS, "분",
                                lambda: self.selected_minutes, self.pick_minutes,
                                MINUTES_MIN, MINUTES_MAX)

        RoundButton(self, "시험 시작", self.start_test, bg=ACCENT, fg=TEXT,
                     size=15, width=14, pady=11).pack(pady=(28, 0))

    def section(self, text):
        tk.Label(self, text=text, bg=BG, fg=TEXT, font=(FONT_NAME, 13, "bold")).pack(pady=(14, 0))

    def build_chip_row(self, parent, items, selected_getter, on_pick, max_cols=6):
        row = tk.Frame(parent, bg=BG)
        row.pack(pady=(6, 0))
        buttons = {}

        def refresh():
            cur = selected_getter()
            for v, btn in buttons.items():
                if v == cur:
                    btn.config(bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK)
                else:
                    btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")

        for i, (value, label) in enumerate(items):
            b = tk.Button(row, text=label, font=(FONT_NAME, 12, "bold"),
                            relief="flat", bd=0, cursor="hand2", padx=14, pady=7,
                            highlightbackground="#dbe7ee", highlightthickness=1,
                            command=lambda v=value: (on_pick(v), refresh()))
            b.grid(row=i // max_cols, column=i % max_cols, padx=5, pady=4)
            buttons[value] = b
        refresh()
        return buttons, refresh

    def build_number_row(self, parent, presets, unit, getter, setter, lo, hi):
        """A chip row of preset values plus a free-typed custom entry, kept in
        sync both ways: picking a chip updates the entry, and typing a value
        (clamped to [lo, hi]) un-highlights the chips unless it matches one."""
        row = tk.Frame(parent, bg=BG)
        row.pack(pady=(6, 0))
        buttons = {}
        var = tk.StringVar(value=str(getter()))
        guard = {"on": False}

        def style(cur):
            for v, btn in buttons.items():
                if v == cur:
                    btn.config(bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK)
                else:
                    btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")

        def pick_preset(v):
            setter(v)
            guard["on"] = True
            var.set(str(v))
            guard["on"] = False
            style(v)

        for value in presets:
            b = tk.Button(row, text=f"{value}{unit}", font=(FONT_NAME, 12, "bold"),
                            relief="flat", bd=0, cursor="hand2", padx=14, pady=7,
                            highlightbackground="#dbe7ee", highlightthickness=1,
                            command=lambda v=value: pick_preset(v))
            b.pack(side="left", padx=5)
            buttons[value] = b

        def on_change(*_):
            if guard["on"]:
                return
            raw = var.get().strip()
            if raw.isdigit() and raw != "0":
                n = max(lo, min(hi, int(raw)))
                setter(n)
                style(n)
            else:
                style(-1)

        tk.Label(row, text="직접입력", bg=BG, fg=MUTED, font=(FONT_NAME, 11)).pack(side="left", padx=(14, 4))
        vcmd = (self.register(lambda p: p == "" or p.isdigit()), "%P")
        entry = tk.Entry(row, textvariable=var, font=(FONT_NAME, 12), width=5, justify="center",
                           relief="solid", bd=1, validate="key", validatecommand=vcmd)
        entry.pack(side="left")
        tk.Label(row, text=f"{unit} ({lo}~{hi})", bg=BG, fg=MUTED, font=(FONT_NAME, 10)).pack(side="left", padx=(4, 0))

        var.trace_add("write", on_change)
        style(getter())
        return buttons

    def pick_op(self, op):
        self.selected_op = op
        self.selected_level = 1
        self.rebuild_level_row()

    def pick_count(self, n):
        self.selected_count = max(COUNT_MIN, min(COUNT_MAX, n))

    def pick_minutes(self, m):
        self.selected_minutes = max(MINUTES_MIN, min(MINUTES_MAX, m))

    def pick_level(self, lv):
        self.selected_level = lv

    def rebuild_level_row(self):
        for w in self.level_container.winfo_children():
            w.destroy()
        items = [(lv["level"], lv["title"]) for lv in OP_LEVELS_MAP[self.selected_op]]
        self.build_chip_row(self.level_container, items, lambda: self.selected_level, self.pick_level)

    def start_test(self):
        self.app.show_test(self.selected_op, self.selected_level,
                             self.selected_count, self.selected_minutes)


class TestPage(tk.Frame):
    def __init__(self, master, app, op, level, count, minutes):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.op = op
        self.level = level
        self.count = count
        self.minutes = minutes
        self.mode = OP_ANSWER_MODE[op]

        recent = deque(maxlen=DEDUP_WINDOW)
        self.questions = [gen_question_dict_dedup(op, level, recent) for _ in range(count)]

        self.user_answers = [None] * count
        self.index = 0
        self.remaining = minutes * 60
        self.finished = False
        self._timer_job = None

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(16, 0))
        RoundButton(top, "✕ 중단하기", self.confirm_quit, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")
        tk.Label(top, text=f"{OP_LABELS[op]} 시험", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 15, "bold")).pack(side="left", padx=(16, 0))
        self.timer_label = tk.Label(top, text="", bg=BG, fg=PRIMARY, font=(FONT_NAME, 15, "bold"))
        self.timer_label.pack(side="right")

        self.progress_label = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT_NAME, 12))
        self.progress_label.pack(pady=(8, 0))

        card = tk.Frame(self, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack(padx=60, pady=(16, 20), fill="both", expand=True)

        self.canvas, self.problem_label = build_question_display(card, self.mode)

        vcmd = (self.register(self._validate_num), "%P")
        self.widgets = build_mode_input(card, self.mode, vcmd)

        self.main_btn = RoundButton(card, "다음 →", self.submit_current, bg=ACCENT, fg=TEXT,
                                      size=15, width=12, pady=11)
        self.main_btn.pack(pady=(28, 30))

        self.app.set_enter_handler(self.submit_current)
        self.show_question()
        self._tick()

    def _validate_num(self, proposed):
        return validate_mode_num(self.mode, proposed)

    def show_question(self):
        q = self.questions[self.index]
        self.problem_label.config(text=q["prob_text"])
        if self.mode == "clock":
            draw_clock_diagram(self.canvas, q["hour"], q["minute"])
        self.progress_label.config(text=f"{self.index + 1} / {self.count} 문제")
        clear_mode_input(self.widgets)
        is_last = self.index == self.count - 1
        self.main_btn.config(text="제출하기" if is_last else "다음 →")

    def _read_current_answer(self):
        return read_mode_input(self.widgets)

    def submit_current(self):
        if self.finished:
            return
        self.user_answers[self.index] = self._read_current_answer()
        if self.index < self.count - 1:
            self.index += 1
            self.show_question()
        else:
            self.finish(quit_early=False)

    def _tick(self):
        if self.finished:
            return
        mm, ss = divmod(max(self.remaining, 0), 60)
        self.timer_label.config(text=f"남은 시간 {mm:02d}:{ss:02d}",
                                  fg=RED if self.remaining <= 30 else PRIMARY)
        if self.remaining <= 0:
            self.finish(quit_early=False)
            return
        self.remaining -= 1
        self._timer_job = self.after(1000, self._tick)

    def confirm_quit(self):
        self.finish(quit_early=True)

    def finish(self, quit_early):
        if self.finished:
            return
        self.finished = True
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        if not quit_early and self.user_answers[self.index] is None:
            self.user_answers[self.index] = self._read_current_answer()
        elapsed = self.minutes * 60 - max(self.remaining, 0)
        self.app.show_test_result(self.op, self.level, self.questions, self.user_answers,
                                    elapsed, self.minutes * 60)


class TestResultPage(tk.Frame):
    def __init__(self, master, app, op, level, questions, user_answers, elapsed_seconds, total_seconds):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.op = op
        self.level = level
        self.questions = questions

        graded = []
        correct_n = 0
        for q, ua in zip(questions, user_answers):
            ok, ans_text = grade_question(q, ua)
            ua_text = format_user_answer(q["mode"], ua)
            if ok:
                correct_n += 1
            graded.append({"prob": q["prob_text"], "user": ua_text, "answer": ans_text, "ok": ok})

        total = len(questions)
        accuracy = round(correct_n / total * 100) if total else 0
        mm, ss = divmod(elapsed_seconds, 60)
        self.wrong_indices = [i for i, g in enumerate(graded) if not g["ok"]]

        save_history_entry({
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "op": op, "op_label": OP_LABELS[op], "level": level,
            "correct": correct_n, "total": total, "accuracy": accuracy,
            "elapsed_seconds": elapsed_seconds,
        })

        back_label, back_cmd = CATEGORY_BACK[OP_CATEGORY[op]]
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(16, 0))
        RoundButton(top, back_label, getattr(self.app, back_cmd), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"{OP_LABELS[op]} 시험 결과", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 24, "bold")).pack(pady=(10, 16))

        stat_row = tk.Frame(self, bg=BG)
        stat_row.pack()
        for label, value, color in [
            ("맞은 개수", f"{correct_n}/{total}", GREEN_DARK),
            ("정답률", f"{accuracy}%", PRIMARY),
            ("걸린 시간", f"{mm:02d}:{ss:02d}", TEXT),
        ]:
            box = tk.Frame(stat_row, bg=CARD, width=160, height=92,
                             highlightbackground="#dbe7ee", highlightthickness=1)
            box.pack_propagate(False)
            box.pack(side="left", padx=8)
            tk.Label(box, text=value, bg=CARD, fg=color, font=(FONT_NAME, 22, "bold")).pack(pady=(18, 0))
            tk.Label(box, text=label, bg=CARD, fg=MUTED, font=(FONT_NAME, 11)).pack()

        scroll = ScrollableFrame(self, bg=BG, height=260)
        scroll.pack(fill="both", expand=True, padx=40, pady=(18, 6))
        for i, g in enumerate(graded, start=1):
            row_bg = CARD if g["ok"] else "#fdeceb"
            row = tk.Frame(scroll.inner, bg=row_bg, highlightbackground="#dbe7ee", highlightthickness=1)
            row.pack(fill="x", pady=3, padx=2)
            mark_color = GREEN_DARK if g["ok"] else RED
            tk.Label(row, text=("○" if g["ok"] else "✕"), bg=row_bg, fg=mark_color,
                      font=(FONT_NAME, 13, "bold"), width=2).pack(side="left", padx=(10, 4), pady=8)
            tk.Label(row, text=f"{i}. {g['prob']} → {g['answer']}", bg=row_bg, fg=TEXT,
                      font=(FONT_NAME, 12), anchor="w", justify="left",
                      wraplength=460).pack(side="left", padx=4, pady=8)
            if not g["ok"]:
                tk.Label(row, text=f"내 답: {g['user']}", bg=row_bg, fg=RED,
                          font=(FONT_NAME, 11), anchor="e").pack(side="right", padx=10)

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=(12, 16))
        retry_minutes = max(1, round(total_seconds / 60))
        if self.wrong_indices:
            wrong_questions = [questions[i] for i in self.wrong_indices]
            RoundButton(btn_row, f"틀린 문제 다시 풀기 ({len(wrong_questions)})",
                         lambda: self.app.show_wrong_answer_review(op, wrong_questions),
                         bg=ACCENT, fg=TEXT, size=12, width=20, pady=9).pack(side="left", padx=6)
        RoundButton(btn_row, "같은 설정으로 다시", lambda: self.app.show_test(op, level, total, retry_minutes),
                     bg=PRIMARY, size=12, width=15, pady=9).pack(side="left", padx=6)
        RoundButton(btn_row, "시험 설정으로", lambda: self.app.show_test_setup(OP_CATEGORY[op]),
                     bg=DISABLED, fg=TEXT, size=12, width=12, pady=9).pack(side="left", padx=6)


def _tick_line(canvas, x1, y1, x2, y2, color, width=3, dash=None):
    """A colored line with small perpendicular tick marks at both ends, like a
    dimension line in a technical drawing -- makes clear exactly which span
    is being measured, not just a floating number near the shape."""
    canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash)
    dx, dy = x2 - x1, y2 - y1
    length = (dx ** 2 + dy ** 2) ** 0.5 or 1
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    t = 6
    for (ex, ey) in [(x1, y1), (x2, y2)]:
        canvas.create_line(ex - px * t, ey - py * t, ex + px * t, ey + py * t, fill=color, width=width)


def draw_shape_diagram(canvas, shape_label, dims):
    """Draws a labeled outline of `shape_label` on a 240x170 canvas. Every
    dimension in `dims` gets its own colored, ticked line drawn directly on
    (or against) the edge it measures, with a matching-colored label -- so
    which side is which is visible at a glance, not just written in text.
    Color meaning is consistent across every shape: DIM_A(orange) = a
    horizontal/base-type length, DIM_B(green) = a vertical/height-type
    length, DIM_C(purple) = a third length only needed for 직육면체."""
    canvas.delete("all")
    cx, cy = 120, 78
    font = (FONT_NAME, 11, "bold")

    def label(x, y, text, color=TEXT, anchor="center"):
        canvas.create_text(x, y, text=text, fill=color, font=font, anchor=anchor)

    if shape_label == "정사각형":
        s = 100
        x0, y0, x1, y1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
        canvas.create_rectangle(x0, y0, x1, y1, outline=OUTLINE_NEUTRAL, width=2)
        _tick_line(canvas, x0, y0, x1, y0, DIM_A)
        label(cx, y0 - 16, f"한 변 {dims.get('한 변')}cm", DIM_A)

    elif shape_label == "직사각형":
        w, h = 130, 80
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        canvas.create_rectangle(x0, y0, x1, y1, outline=OUTLINE_NEUTRAL, width=2)
        _tick_line(canvas, x0, y0, x1, y0, DIM_A)
        label(cx, y0 - 16, f"가로 {dims.get('가로')}cm", DIM_A)
        _tick_line(canvas, x1, y0, x1, y1, DIM_B)
        label(x1 + 34, cy, f"세로\n{dims.get('세로')}cm", DIM_B)

    elif shape_label == "평행사변형":
        skew, w, h = 30, 110, 70
        x0, y0 = cx - w / 2, cy + h / 2
        pts = [x0, y0, x0 + w, y0, x0 + w + skew, y0 - h, x0 + skew, y0 - h]
        canvas.create_polygon(pts, outline=OUTLINE_NEUTRAL, fill="", width=2)
        _tick_line(canvas, x0, y0, x0 + w, y0, DIM_A)
        label(cx, y0 + 18, f"밑변 {dims.get('밑변')}cm", DIM_A)
        _tick_line(canvas, x0 + skew, y0 - h, x0 + skew, y0, DIM_B, width=2, dash=(4, 2))
        label(x0 + skew - 30, cy, f"높이\n{dims.get('높이')}cm", DIM_B)

    elif shape_label == "삼각형":
        w, h = 120, 90
        x0, y0 = cx - w / 2, cy + h / 2
        apex_x = x0 + w * 0.4
        pts = [x0, y0, x0 + w, y0, apex_x, y0 - h]
        canvas.create_polygon(pts, outline=OUTLINE_NEUTRAL, fill="", width=2)
        _tick_line(canvas, x0, y0, x0 + w, y0, DIM_A)
        label(cx, y0 + 18, f"밑변 {dims.get('밑변')}cm", DIM_A)
        _tick_line(canvas, apex_x, y0 - h, apex_x, y0, DIM_B, width=2, dash=(4, 2))
        label(apex_x - 34, cy, f"높이\n{dims.get('높이')}cm", DIM_B)

    elif shape_label == "마름모":
        if "한 변" in dims:
            s = 72
            pts = [cx, cy - s, cx + s, cy, cx, cy + s, cx - s, cy]
            canvas.create_polygon(pts, outline=OUTLINE_NEUTRAL, fill="", width=2)
            _tick_line(canvas, cx, cy - s, cx + s, cy, DIM_A)
            label(cx + 50, cy - 46, f"한 변 {dims.get('한 변')}cm", DIM_A)
        else:
            w, h = 130, 90
            pts = [cx, cy - h / 2, cx + w / 2, cy, cx, cy + h / 2, cx - w / 2, cy]
            canvas.create_polygon(pts, outline=OUTLINE_NEUTRAL, fill="", width=2)
            _tick_line(canvas, cx - w / 2, cy, cx + w / 2, cy, DIM_A, width=2, dash=(4, 2))
            _tick_line(canvas, cx, cy - h / 2, cx, cy + h / 2, DIM_B, width=2, dash=(4, 2))
            label(cx, cy + h / 2 + 18, f"한 대각선 {dims.get('한 대각선')}cm", DIM_A)
            label(cx + w / 2 + 36, cy, f"다른 대각선\n{dims.get('다른 대각선')}cm", DIM_B)

    elif shape_label == "사다리꼴":
        top_w, bot_w, h = 70, 130, 80
        x0t, x0b = cx - top_w / 2, cx - bot_w / 2
        y0, y1 = cy - h / 2, cy + h / 2
        pts = [x0t, y0, x0t + top_w, y0, x0b + bot_w, y1, x0b, y1]
        canvas.create_polygon(pts, outline=OUTLINE_NEUTRAL, fill="", width=2)
        _tick_line(canvas, x0t, y0, x0t + top_w, y0, DIM_A)
        label(cx, y0 - 16, f"윗변 {dims.get('윗변')}cm", DIM_A)
        _tick_line(canvas, x0b, y1, x0b + bot_w, y1, DIM_A)
        label(cx, y1 + 18, f"아랫변 {dims.get('아랫변')}cm", DIM_A)
        _tick_line(canvas, x0t, y0, x0t, y1, DIM_B, width=2, dash=(4, 2))
        label(x0t - 30, cy, f"높이\n{dims.get('높이')}cm", DIM_B)

    elif shape_label == "원":
        r = 60
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=OUTLINE_NEUTRAL, width=2)
        has_d, has_r = "지름" in dims, "반지름" in dims
        if has_d:
            _tick_line(canvas, cx - r, cy, cx + r, cy, DIM_A, width=2, dash=(4, 2))
            label(cx, cy + r + 16, f"지름 {dims.get('지름')}cm", DIM_A)
        if has_r:
            _tick_line(canvas, cx, cy, cx, cy - r, DIM_B, width=2, dash=(4, 2))  # drawn upward so it never overlaps the diameter line
            label(cx + 34, cy - r / 2, f"반지름\n{dims.get('반지름')}cm", DIM_B)
        if has_d and has_r:
            label(cx, cy + r + 36, "반지름 = 지름 ÷ 2", MUTED)

    elif shape_label == "직육면체":
        w, h, ox, oy = 100, 60, 30, -18
        x0, y0 = cx - w / 2 - 10, cy + h / 2
        canvas.create_rectangle(x0, y0 - h, x0 + w, y0, outline=OUTLINE_NEUTRAL, width=2)
        for (ax, ay) in [(x0, y0 - h), (x0 + w, y0 - h), (x0 + w, y0)]:
            canvas.create_line(ax, ay, ax + ox, ay + oy, fill=OUTLINE_NEUTRAL, width=2)
        canvas.create_line(x0 + ox, y0 - h + oy, x0 + w + ox, y0 - h + oy, fill=OUTLINE_NEUTRAL, width=2)
        canvas.create_line(x0 + w + ox, y0 - h + oy, x0 + w + ox, y0 + oy, fill=OUTLINE_NEUTRAL, width=2)
        _tick_line(canvas, x0, y0, x0 + w, y0, DIM_A)
        label(cx - 10, y0 + 18, f"가로 {dims.get('가로')}cm", DIM_A)
        _tick_line(canvas, x0, y0 - h, x0, y0, DIM_B)
        label(x0 - 30, cy, f"세로\n{dims.get('세로')}cm", DIM_B)
        _tick_line(canvas, x0 + w, y0 - h, x0 + w + ox, y0 - h + oy, DIM_C)
        label(x0 + w + ox + 36, y0 - h + oy / 2, f"높이\n{dims.get('높이')}cm", DIM_C)

    elif shape_label == "정육면체":
        s, ox, oy = 80, 24, -17
        x0, y0 = cx - s / 2 - 8, cy + s / 2
        canvas.create_rectangle(x0, y0 - s, x0 + s, y0, outline=OUTLINE_NEUTRAL, width=2)
        for (ax, ay) in [(x0, y0 - s), (x0 + s, y0 - s), (x0 + s, y0)]:
            canvas.create_line(ax, ay, ax + ox, ay + oy, fill=OUTLINE_NEUTRAL, width=2)
        canvas.create_line(x0 + ox, y0 - s + oy, x0 + s + ox, y0 - s + oy, fill=OUTLINE_NEUTRAL, width=2)
        canvas.create_line(x0 + s + ox, y0 - s + oy, x0 + s + ox, y0 + oy, fill=OUTLINE_NEUTRAL, width=2)
        _tick_line(canvas, x0, y0, x0 + s, y0, DIM_A)
        label(cx - 4, y0 + 18, f"한 모서리 {dims.get('한 모서리')}cm", DIM_A)


def draw_clock_diagram(canvas, hour, minute):
    """Draws an analog clock face on a 300x300 canvas showing `hour`:`minute`.
    Sized up from the original 200x200, with a thicker face/hands and an outer
    ring of 5분 단위 minute numbers -- at the old size, Lv.3 (1분 단위) questions
    were hard to read precisely off the tick marks alone."""
    canvas.delete("all")
    cx, cy, r = 150, 150, 115
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=TEXT, width=4, fill="white")

    # 5분 단위 바깥쪽 눈금 숫자 -- 분침이 가리키는 분을 더 정확히 셀 수 있도록.
    for m in range(0, 60, 5):
        ang = math.radians(m * 6 - 90)
        tx, ty = cx + (r + 20) * math.cos(ang), cy + (r + 20) * math.sin(ang)
        canvas.create_text(tx, ty, text=str(m if m else 60), font=(FONT_NAME, 11), fill=PRIMARY)

    for h in range(1, 13):
        ang = math.radians(h * 30 - 90)
        tx, ty = cx + (r - 30) * math.cos(ang), cy + (r - 30) * math.sin(ang)
        canvas.create_text(tx, ty, text=str(h), font=(FONT_NAME, 18, "bold"), fill=TEXT)

    for m in range(60):
        ang = math.radians(m * 6 - 90)
        outer = r - 6
        inner = r - (20 if m % 5 == 0 else 10)
        x1, y1 = cx + outer * math.cos(ang), cy + outer * math.sin(ang)
        x2, y2 = cx + inner * math.cos(ang), cy + inner * math.sin(ang)
        canvas.create_line(x1, y1, x2, y2, fill=MUTED, width=3 if m % 5 == 0 else 1)

    hour_ang = math.radians((hour % 12) * 30 + minute * 0.5 - 90)
    minute_ang = math.radians(minute * 6 - 90)
    canvas.create_line(cx, cy, cx + (r * 0.5) * math.cos(hour_ang), cy + (r * 0.5) * math.sin(hour_ang),
                        fill=DIM_C, width=7, capstyle="round")
    canvas.create_line(cx, cy, cx + (r * 0.8) * math.cos(minute_ang), cy + (r * 0.8) * math.sin(minute_ang),
                        fill=PRIMARY, width=4, capstyle="round")
    canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=TEXT, outline=TEXT)


def draw_angle_diagram(canvas, degrees_list):
    """Draws each angle in `degrees_list` side by side on a 240x170 canvas,
    as two rays from a vertex with an arc and the degree value labeled --
    gives 초3/초4 각 문제 a picture of what the stated angle actually looks
    like, rather than only a number in the question text."""
    canvas.delete("all")
    n = max(1, len(degrees_list))
    slot_w = 240 // n
    colors = [DIM_A, DIM_B, DIM_C]
    for i, deg in enumerate(degrees_list):
        cx = slot_w * i + slot_w // 2 - 15
        cy = 130
        length = 70
        x1, y1 = cx + length, cy
        rad = math.radians(deg)
        x2, y2 = cx + length * math.cos(rad), cy - length * math.sin(rad)
        color = colors[i % len(colors)]
        canvas.create_line(cx, cy, x1, y1, fill=TEXT, width=2)
        canvas.create_line(cx, cy, x2, y2, fill=TEXT, width=2)
        arc_r = 32
        canvas.create_arc(cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r,
                            start=0, extent=deg, style="arc", outline=color, width=2)
        mid = math.radians(deg / 2)
        lx, ly = cx + (arc_r + 20) * math.cos(mid), cy - (arc_r + 20) * math.sin(mid)
        canvas.create_text(lx, ly, text=f"{deg}°", fill=color, font=(FONT_NAME, 13, "bold"))
        # small square marker for a right angle, matching the usual convention
        if deg == 90:
            s = 10
            canvas.create_rectangle(cx, cy - s, cx + s, cy, outline=color, width=2)


def _regular_polygon_points(cx, cy, r, n, rot=-90):
    pts = []
    for i in range(n):
        ang = math.radians(rot + 360 * i / n)
        pts += [cx + r * math.cos(ang), cy + r * math.sin(ang)]
    return pts


def draw_named_shape(canvas, shape_name):
    """Draws a plain outline of `shape_name` (원/삼각형/사각형/오각형/육각형)
    on a 200x170 canvas for the 초1 '모양' 이름 맞추기 문제 -- no dimension
    labels, since the point here is recognizing the shape, not measuring it."""
    canvas.delete("all")
    cx, cy, r = 100, 85, 62
    if shape_name == "원":
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=TEXT, width=3)
        return
    sides = {"삼각형": 3, "사각형": 4, "오각형": 5, "육각형": 6}[shape_name]
    rot = -90 if sides != 4 else -45  # square sits flat on its base, not on a corner
    pts = _regular_polygon_points(cx, cy, r, sides, rot=rot)
    canvas.create_polygon(pts, outline=TEXT, fill="", width=3)


def draw_bar_graph(canvas, categories, values, step):
    """Draws a simple bar graph with gridlines (0/step/2·3·4×step) on a
    240x170 canvas -- `step` must be the same per-unit increment gen_graph_read
    used to build `values` (each value is step times a 1~4 multiplier), so
    every value sits exactly on one of the 5 gridlines and the tallest bar
    never exceeds the top gridline (deriving step from the data instead,
    e.g. max(values)//4, can round down and make the tallest bar overflow)."""
    canvas.delete("all")
    margin_l, margin_b, margin_t, margin_r = 32, 24, 12, 10
    w, h = 240, 170
    plot_w = w - margin_l - margin_r
    plot_h = h - margin_b - margin_t
    top_v = step * 4
    for i in range(5):
        y = margin_t + plot_h - (plot_h * i / 4)
        canvas.create_line(margin_l, y, w - margin_r, y, fill="#e5edf2", width=1)
        canvas.create_text(margin_l - 6, y, text=str(step * i), fill=MUTED,
                             font=(FONT_NAME, 8), anchor="e")
    canvas.create_line(margin_l, margin_t, margin_l, margin_t + plot_h, fill=TEXT, width=2)
    canvas.create_line(margin_l, margin_t + plot_h, w - margin_r, margin_t + plot_h, fill=TEXT, width=2)
    n = len(categories)
    bar_slot = plot_w / n
    bar_w = bar_slot * 0.55
    colors = [DIM_A, DIM_B, DIM_C, PRIMARY, ACCENT_DARK]
    for i, (cat, val) in enumerate(zip(categories, values)):
        bar_h = plot_h * (val / top_v) if top_v else 0
        x0 = margin_l + bar_slot * i + (bar_slot - bar_w) / 2
        x1 = x0 + bar_w
        y1 = margin_t + plot_h
        y0 = y1 - bar_h
        canvas.create_rectangle(x0, y0, x1, y1, fill=colors[i % len(colors)], outline="")
        canvas.create_text((x0 + x1) / 2, y1 + 12, text=cat, fill=TEXT, font=(FONT_NAME, 9, "bold"))


class ShapeHomePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="도형", bg=BG, fg=TEXT, font=(FONT_NAME, 30, "bold")).pack(pady=(20, 4))
        tk.Label(self, text="공식을 먼저 볼까요, 바로 문제를 풀어볼까요?", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 14)).pack(pady=(0, 26))

        grid = tk.Frame(self, bg=BG)
        grid.pack()
        cards = [
            ("📐", "공식", "도형별 둘레·넓이·부피 공식 모아보기", self.app.show_shape_formulas, PRIMARY),
            ("✏", "문제풀이", "도형을 골라 직접 문제를 풀어보기", self.app.show_shape_select, PRIMARY),
            ("⚙", "설정", "자주 틀리는 숫자 연습", lambda: self.app.show_settings("shape"), PRIMARY_DARK),
            ("⏱", "시험", "제한시간 안에 풀어보기", self.app.show_shape_test_setup, ACCENT_DARK),
        ]
        for i, (symbol, label_text, desc, cmd, color) in enumerate(cards):
            card = tk.Frame(grid, bg=CARD, width=250, height=205,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, padx=12, pady=8)
            card.pack_propagate(False)
            tk.Label(card, text=symbol, bg=CARD, fg=color, font=(FONT_NAME, 26, "bold")).pack(pady=(16, 2))
            tk.Label(card, text=label_text, bg=CARD, fg=TEXT, font=(FONT_NAME, 16, "bold")).pack()
            tk.Label(card, text=desc, bg=CARD, fg=MUTED, font=(FONT_NAME, 10),
                      wraplength=220, justify="center").pack(pady=(3, 0))
            RoundButton(card, "시작하기", cmd, bg=color, size=11, width=9, pady=7).pack(pady=(10, 0))


class ShapeFormulaPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 도형", self.app.show_shape_home, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="도형 공식 모음", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 24, "bold")).pack(pady=(12, 16))

        legend = tk.Frame(self, bg=BG)
        legend.pack(pady=(0, 10))
        tk.Label(legend, text="●", bg=BG, fg=DIM_A, font=(FONT_NAME, 12, "bold")).pack(side="left")
        tk.Label(legend, text="가로형 길이(가로·밑변·윗변·아랫변·지름·한 변)", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 11)).pack(side="left", padx=(2, 14))
        tk.Label(legend, text="●", bg=BG, fg=DIM_B, font=(FONT_NAME, 12, "bold")).pack(side="left")
        tk.Label(legend, text="세로형 길이(세로·높이·반지름)", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 11)).pack(side="left", padx=(2, 0))

        scroll = ScrollableFrame(self, bg=BG, height=520)
        scroll.pack(fill="both", expand=True, padx=30, pady=(0, 14))

        for shape_label in SHAPE_ORDER:
            defs = SHAPES_BY_LABEL[shape_label]
            tk.Label(scroll.inner, text=shape_label, bg=BG, fg=TEXT,
                      font=(FONT_NAME, 16, "bold"), anchor="w").pack(fill="x", pady=(10, 4))

            # one diagram PER FORMULA -- each formula shows exactly the
            # dimensions it actually uses (e.g. 마름모 둘레 shows its side,
            # 마름모 넓이 shows both diagonals; 원 둘레 shows 지름, 원 넓이
            # shows 반지름 -- never left showing only the other formula's value)
            for sd in defs:
                row = tk.Frame(scroll.inner, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
                row.pack(fill="x", pady=5, padx=2)

                canvas = tk.Canvas(row, width=240, height=170, bg=CARD, highlightthickness=0)
                canvas.pack(side="left", padx=14, pady=10)
                sample_dims, _ = sd["gen"]()
                draw_shape_diagram(canvas, shape_label, sample_dims)

                text_col = tk.Frame(row, bg=CARD)
                text_col.pack(side="left", fill="both", expand=True, pady=12, padx=(0, 14))
                tk.Label(text_col, text=sd["quantity_label"], bg=CARD, fg=TEXT,
                          font=(FONT_NAME, 14, "bold"), anchor="w").pack(fill="x")
                tk.Label(text_col, text=f"{shape_label} {sd['formula_text']}", bg=CARD, fg=PRIMARY,
                          font=(FONT_NAME, 13, "bold"), anchor="w").pack(fill="x", pady=(6, 0))


class ShapeSelectPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        if self.app.shape_browse_return:
            back_label, back_action = self.app.shape_browse_return
        else:
            back_label, back_action = "← 도형", self.app.show_shape_home
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, back_label, back_action, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="어떤 도형을 풀어볼까요?", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 24, "bold")).pack(pady=(14, 4 if self.app.entry_grade else 24))
        if self.app.entry_grade:
            tk.Label(self, text=f"초등 {self.app.entry_grade}학년", bg=BG, fg=MUTED,
                      font=(FONT_NAME, 11)).pack(pady=(0, 20))

        grid = tk.Frame(self, bg=BG)
        grid.pack()
        for i, shape_label in enumerate(SHAPE_ORDER):
            defs = SHAPES_BY_LABEL[shape_label]
            quantities = " · ".join(sd["quantity_label"] for sd in defs)
            card = tk.Frame(grid, bg=CARD, width=230, height=150,
                              highlightbackground="#dbe7ee", highlightthickness=1)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10)
            card.pack_propagate(False)

            tk.Label(card, text=SHAPE_ICONS.get(shape_label, "◆"), bg=CARD, fg=PRIMARY,
                      font=(FONT_NAME, 30, "bold")).pack(pady=(16, 2))
            tk.Label(card, text=shape_label, bg=CARD, fg=TEXT, font=(FONT_NAME, 14, "bold")).pack()
            tk.Label(card, text=quantities, bg=CARD, fg=MUTED, font=(FONT_NAME, 10)).pack()

            def go(label=shape_label, defs=defs):
                if len(defs) > 1:
                    self.app.show_shape_quantity_select(label)
                else:
                    self.app.show_shape_practice(defs[0]["key"])

            RoundButton(card, "풀기", go, bg=ACCENT, fg=TEXT, size=10, width=8, pady=5).pack(pady=(6, 0))


class ShapeQuantitySelectPage(tk.Frame):
    def __init__(self, master, app, shape_label):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.shape_label = shape_label

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 0))
        RoundButton(top, "← 도형 목록", self.app.show_shape_select, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"{shape_label} — 무엇을 구할까요?", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 24, "bold")).pack(pady=(20, 30))

        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=80)

        for sd in SHAPES_BY_LABEL[shape_label]:
            row = tk.Frame(list_frame, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
            row.pack(fill="x", pady=6)
            text_col = tk.Frame(row, bg=CARD)
            text_col.pack(side="left", fill="both", expand=True, padx=18, pady=14)
            tk.Label(text_col, text=sd["quantity_label"], bg=CARD, fg=TEXT,
                      font=(FONT_NAME, 16, "bold"), anchor="w").pack(fill="x")
            tk.Label(text_col, text=sd["formula_text"], bg=CARD, fg=PRIMARY,
                      font=(FONT_NAME, 12), anchor="w").pack(fill="x", pady=(4, 0))
            RoundButton(row, "풀기", lambda k=sd["key"]: self.app.show_shape_practice(k),
                         bg=ACCENT, fg=TEXT, size=12, width=6, pady=8).pack(side="right", padx=16)


class ShapePracticePage(tk.Frame):
    def __init__(self, master, app, key):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.sd = SHAPE_DEFS_BY_KEY[key]
        self.decimal = self.sd["decimal"]
        self.is_circle = self.sd["shape_label"] == "원"
        self.use_pi = False

        self.correct_count = 0
        self.wrong_count = 0
        self.streak = 0
        self.state = "answering"
        self.dims = None
        self.answer = None
        self.recent = deque(maxlen=DEDUP_WINDOW)

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 목록으로", self.go_back, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")
        tk.Label(top, text=f"{self.sd['shape_label']} {self.sd['quantity_label']}", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 16, "bold")).pack(side="left", padx=(18, 0))
        if self.app.entry_grade:
            tk.Label(top, text=f"초등 {self.app.entry_grade}학년", bg=BG, fg=MUTED,
                      font=(FONT_NAME, 11)).pack(side="left", padx=(10, 0))
        self.score_label = tk.Label(top, text="", bg=BG, fg=MUTED, font=(FONT_NAME, 13))
        self.score_label.pack(side="right")

        formula_row = tk.Frame(self, bg=BG)
        formula_row.pack(fill="x", padx=24, pady=(6, 0))
        tk.Label(formula_row, text=f"공식: {self.sd['shape_label']} {self.sd['formula_text']}", bg=BG, fg=PRIMARY_DARK,
                  font=(FONT_NAME, 11, "bold")).pack(side="left")

        card = tk.Frame(self, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack(padx=60, pady=(24, 20), fill="both", expand=True)

        self.canvas = tk.Canvas(card, width=240, height=170, bg=CARD, highlightthickness=0)
        self.canvas.pack(pady=(20, 6))

        self.question_label = tk.Label(card, text="", bg=CARD, fg=TEXT, font=(FONT_NAME, 15),
                                         wraplength=560, justify="center")
        self.question_label.pack(pady=(0, 14))

        input_row = tk.Frame(card, bg=CARD)
        input_row.pack(pady=6)
        vcmd = (self.register(self._validate_num), "%P")
        self.answer_var = tk.StringVar()
        self.entry = tk.Entry(input_row, textvariable=self.answer_var, font=(FONT_NAME, 26),
                                width=8, justify="center", relief="solid", bd=2,
                                validate="key", validatecommand=vcmd)
        self.entry.pack(side="left", ipady=5)

        if self.is_circle:
            self.unit_buttons = {}
            unit_row = tk.Frame(input_row, bg=CARD)
            unit_row.pack(side="left", padx=(10, 0))
            for is_pi, unit_text in [(False, self.sd["unit"]), (True, f"π {self.sd['unit']}")]:
                b = tk.Button(unit_row, text=unit_text, font=(FONT_NAME, 12, "bold"),
                                relief="flat", bd=0, cursor="hand2", padx=10, pady=6,
                                highlightbackground="#dbe7ee", highlightthickness=1,
                                command=lambda p=is_pi: self.set_pi_mode(p))
                b.pack(side="left", padx=3)
                self.unit_buttons[is_pi] = b
            self._refresh_pi_toggle()
        else:
            tk.Label(input_row, text=self.sd["unit"], bg=CARD, fg=MUTED, font=(FONT_NAME, 14)).pack(side="left", padx=(8, 0))

        self.feedback_label = tk.Label(card, text=" ", bg=CARD, font=(FONT_NAME, 15, "bold"))
        self.feedback_label.pack(pady=(14, 0))

        self.main_btn = RoundButton(card, "확인", self.on_main_button, bg=ACCENT, fg=TEXT,
                                      size=15, width=12, pady=11)
        self.main_btn.pack(pady=(18, 26))

        self.app.set_enter_handler(self.on_main_button)
        self.next_problem()

    def go_back(self):
        if self.app.nav_return:
            _label, back_action = self.app.nav_return
            back_action()
            return
        shape_label = self.sd["shape_label"]
        if len(SHAPES_BY_LABEL[shape_label]) > 1:
            self.app.show_shape_quantity_select(shape_label)
        else:
            self.app.show_shape_select()

    def set_pi_mode(self, use_pi):
        if self.use_pi == use_pi:
            return
        self.use_pi = use_pi
        self.answer_var.set("")
        self._refresh_pi_toggle()

    def _refresh_pi_toggle(self):
        for is_pi, btn in self.unit_buttons.items():
            if is_pi == self.use_pi:
                btn.config(bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK)
            else:
                btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")

    def _pi_target(self):
        """Exact answer as a whole-number multiple of π (지름=원주의 계수,
        반지름²=넓이의 계수) -- lets kids answer without needing 3.14 at all."""
        if self.sd["key"] == "circle_circumference":
            return self.dims["지름"]
        return self.dims["반지름"] ** 2

    def _validate_num(self, proposed):
        if proposed == "":
            return True
        if self.is_circle and self.use_pi:
            return proposed.isdigit()
        if self.decimal:
            return proposed.count(".") <= 1 and proposed.replace(".", "").isdigit()
        return proposed.isdigit()

    def update_score(self):
        self.score_label.config(
            text=f"맞음 {self.correct_count}   틀림 {self.wrong_count}   연속정답 {self.streak}"
        )

    def next_problem(self):
        self.dims, self.answer = gen_shape_with_dedup(self.sd["gen"], self.recent)
        draw_shape_diagram(self.canvas, self.sd["shape_label"], self.dims)
        dims_phrase = ", ".join(f"{k} {v}cm" for k, v in self.dims.items())
        self.question_label.config(
            text=f"{dims_phrase}인 {self.sd['shape_label']}의 {self.sd['quantity_label']}를 구하세요."
        )
        self.answer_var.set("")
        self.feedback_label.config(text=" ", fg=TEXT)
        self.entry.config(state="normal", disabledbackground=CARD)
        self.entry.focus_set()
        self.main_btn.config(text="확인", bg=ACCENT, fg=TEXT)
        self.update_score()
        self.state = "answering"

    def on_main_button(self):
        if self.state == "answering":
            self.check_answer()
        else:
            self.next_problem()

    def check_answer(self):
        raw = self.answer_var.get().strip()
        if raw in ("", "."):
            return
        pi_mode = self.is_circle and self.use_pi
        try:
            if pi_mode:
                user_val = int(raw)
            elif self.decimal:
                user_val = float(raw)
            else:
                user_val = int(raw)
        except ValueError:
            return

        if pi_mode:
            target = self._pi_target()
            is_correct = user_val == target
            correct_text = f"{target}π"
        elif self.decimal:
            is_correct = abs(user_val - self.answer) < 0.005
            correct_text = f"{self.answer:g}{self.sd['unit']}"
        else:
            is_correct = user_val == self.answer
            correct_text = f"{self.answer}{self.sd['unit']}"

        if is_correct:
            self.correct_count += 1
            self.streak += 1
            self.feedback_label.config(text="정답이에요! 참 잘했어요", fg=GREEN_DARK)
        else:
            self.wrong_count += 1
            self.streak = 0
            unit_text = f" {self.sd['unit']}" if pi_mode else ""
            self.feedback_label.config(text=f"오답이에요. 정답은 {correct_text}{unit_text}예요", fg=RED)

        self.entry.config(state="disabled")
        self.main_btn.config(text="다음 문제 →", bg=PRIMARY, fg="white")
        self.update_score()
        self.state = "checked"
        self.focus_set()
        self.main_btn.focus_set()


class ShapeTestSetupPage(tk.Frame):
    """도형 시험 설정. 도형은 (치수 dict, 정답) 기반이라 사칙연산 등의
    op/OP_ANSWER_MODE 체계와 완전히 달라서 TestSetupPage를 공유하지 않고
    독립적으로 구현한다 (원의 π 토글, 오답노트는 범위를 좁혀 제외했다)."""

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        self.selected_key = SHAPE_DEFS[0]["key"]
        self.selected_count = TEST_QUESTION_COUNTS[0]
        self.selected_minutes = TEST_TIME_LIMITS[1]

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 도형", self.app.show_shape_home, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="도형 시험 설정", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 26, "bold")).pack(pady=(10, 16))

        self.section("어떤 도형 문제로 볼까요?")
        items = [(sd["key"], f"{sd['shape_label']} {sd['quantity_label']}") for sd in SHAPE_DEFS]
        self.build_chip_row(self, items, lambda: self.selected_key, self.pick_key, max_cols=4)

        self.section("몇 문제 풀까요?")
        self.build_number_row(self, TEST_QUESTION_COUNTS, "문제",
                                lambda: self.selected_count, self.pick_count,
                                COUNT_MIN, COUNT_MAX)

        self.section("제한시간은요?")
        self.build_number_row(self, TEST_TIME_LIMITS, "분",
                                lambda: self.selected_minutes, self.pick_minutes,
                                MINUTES_MIN, MINUTES_MAX)

        RoundButton(self, "시험 시작", self.start_test, bg=ACCENT, fg=TEXT,
                     size=15, width=14, pady=11).pack(pady=(20, 0))

    def section(self, text):
        tk.Label(self, text=text, bg=BG, fg=TEXT, font=(FONT_NAME, 13, "bold")).pack(pady=(10, 0))

    def build_chip_row(self, parent, items, selected_getter, on_pick, max_cols=6):
        row = tk.Frame(parent, bg=BG)
        row.pack(pady=(6, 0))
        buttons = {}

        def refresh():
            cur = selected_getter()
            for v, btn in buttons.items():
                if v == cur:
                    btn.config(bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK)
                else:
                    btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")

        for i, (value, label) in enumerate(items):
            b = tk.Button(row, text=label, font=(FONT_NAME, 12, "bold"),
                            relief="flat", bd=0, cursor="hand2", padx=12, pady=6,
                            highlightbackground="#dbe7ee", highlightthickness=1,
                            command=lambda v=value: (on_pick(v), refresh()))
            b.grid(row=i // max_cols, column=i % max_cols, padx=4, pady=3)
            buttons[value] = b
        refresh()
        return buttons, refresh

    def build_number_row(self, parent, presets, unit, getter, setter, lo, hi):
        row = tk.Frame(parent, bg=BG)
        row.pack(pady=(6, 0))
        buttons = {}
        var = tk.StringVar(value=str(getter()))
        guard = {"on": False}

        def style(cur):
            for v, btn in buttons.items():
                if v == cur:
                    btn.config(bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK)
                else:
                    btn.config(bg=CARD, fg=TEXT, activebackground="#eef3f6")

        def pick_preset(v):
            setter(v)
            guard["on"] = True
            var.set(str(v))
            guard["on"] = False
            style(v)

        for value in presets:
            b = tk.Button(row, text=f"{value}{unit}", font=(FONT_NAME, 12, "bold"),
                            relief="flat", bd=0, cursor="hand2", padx=14, pady=7,
                            highlightbackground="#dbe7ee", highlightthickness=1,
                            command=lambda v=value: pick_preset(v))
            b.pack(side="left", padx=5)
            buttons[value] = b

        def on_change(*_):
            if guard["on"]:
                return
            raw = var.get().strip()
            if raw.isdigit() and raw != "0":
                n = max(lo, min(hi, int(raw)))
                setter(n)
                style(n)
            else:
                style(-1)

        tk.Label(row, text="직접입력", bg=BG, fg=MUTED, font=(FONT_NAME, 11)).pack(side="left", padx=(14, 4))
        vcmd = (self.register(lambda p: p == "" or p.isdigit()), "%P")
        entry = tk.Entry(row, textvariable=var, font=(FONT_NAME, 12), width=5, justify="center",
                           relief="solid", bd=1, validate="key", validatecommand=vcmd)
        entry.pack(side="left")
        tk.Label(row, text=f"{unit} ({lo}~{hi})", bg=BG, fg=MUTED, font=(FONT_NAME, 10)).pack(side="left", padx=(4, 0))

        var.trace_add("write", on_change)
        style(getter())
        return buttons

    def pick_key(self, key):
        self.selected_key = key

    def pick_count(self, n):
        self.selected_count = max(COUNT_MIN, min(COUNT_MAX, n))

    def pick_minutes(self, m):
        self.selected_minutes = max(MINUTES_MIN, min(MINUTES_MAX, m))

    def start_test(self):
        self.app.show_shape_test(self.selected_key, self.selected_count, self.selected_minutes)


class ShapeTestPage(tk.Frame):
    def __init__(self, master, app, key, count, minutes):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.sd = SHAPE_DEFS_BY_KEY[key]
        self.decimal = self.sd["decimal"]
        self.count = count
        self.minutes = minutes

        self.questions = []
        recent = deque(maxlen=DEDUP_WINDOW)
        for _ in range(count):
            dims, answer = gen_shape_with_dedup(self.sd["gen"], recent)
            self.questions.append({"dims": dims, "answer": answer})

        self.user_answers = [None] * count
        self.index = 0
        self.remaining = minutes * 60
        self.finished = False
        self._timer_job = None

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(16, 0))
        RoundButton(top, "✕ 중단하기", self.confirm_quit, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")
        tk.Label(top, text=f"{self.sd['shape_label']} {self.sd['quantity_label']} 시험", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 15, "bold")).pack(side="left", padx=(16, 0))
        self.timer_label = tk.Label(top, text="", bg=BG, fg=PRIMARY, font=(FONT_NAME, 15, "bold"))
        self.timer_label.pack(side="right")

        self.progress_label = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT_NAME, 12))
        self.progress_label.pack(pady=(6, 0))

        card = tk.Frame(self, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack(padx=60, pady=(12, 20), fill="both", expand=True)

        self.canvas = tk.Canvas(card, width=220, height=155, bg=CARD, highlightthickness=0)
        self.canvas.pack(pady=(14, 4))

        self.question_label = tk.Label(card, text="", bg=CARD, fg=TEXT, font=(FONT_NAME, 14),
                                         wraplength=560, justify="center")
        self.question_label.pack(pady=(0, 10))

        input_row = tk.Frame(card, bg=CARD)
        input_row.pack(pady=6)
        vcmd = (self.register(self._validate_num), "%P")
        self.answer_var = tk.StringVar()
        self.entry = tk.Entry(input_row, textvariable=self.answer_var, font=(FONT_NAME, 24),
                                width=8, justify="center", relief="solid", bd=2,
                                validate="key", validatecommand=vcmd)
        self.entry.pack(side="left", ipady=5)
        tk.Label(input_row, text=self.sd["unit"], bg=CARD, fg=MUTED, font=(FONT_NAME, 13)).pack(side="left", padx=(8, 0))

        self.main_btn = RoundButton(card, "다음 →", self.submit_current, bg=ACCENT, fg=TEXT,
                                      size=14, width=12, pady=10)
        self.main_btn.pack(pady=(20, 24))

        self.app.set_enter_handler(self.submit_current)
        self.show_question()
        self._tick()

    def _validate_num(self, proposed):
        if proposed == "":
            return True
        if self.decimal:
            return proposed.count(".") <= 1 and proposed.replace(".", "").isdigit()
        return proposed.isdigit()

    def show_question(self):
        q = self.questions[self.index]
        draw_shape_diagram(self.canvas, self.sd["shape_label"], q["dims"])
        dims_phrase = ", ".join(f"{k} {v}cm" for k, v in q["dims"].items())
        self.question_label.config(
            text=f"{dims_phrase}인 {self.sd['shape_label']}의 {self.sd['quantity_label']}를 구하세요."
        )
        self.progress_label.config(text=f"{self.index + 1} / {self.count} 문제")
        self.answer_var.set("")
        self.entry.config(state="normal", disabledbackground=CARD)
        self.entry.focus_set()
        is_last = self.index == self.count - 1
        self.main_btn.config(text="제출하기" if is_last else "다음 →")

    def _read_current_answer(self):
        raw = self.answer_var.get().strip()
        if raw == "":
            return None
        try:
            return float(raw) if self.decimal else int(raw)
        except ValueError:
            return None

    def submit_current(self):
        if self.finished:
            return
        self.user_answers[self.index] = self._read_current_answer()
        if self.index < self.count - 1:
            self.index += 1
            self.show_question()
        else:
            self.finish(quit_early=False)

    def _tick(self):
        if self.finished:
            return
        mm, ss = divmod(max(self.remaining, 0), 60)
        self.timer_label.config(text=f"남은 시간 {mm:02d}:{ss:02d}",
                                  fg=RED if self.remaining <= 30 else PRIMARY)
        if self.remaining <= 0:
            self.finish(quit_early=False)
            return
        self.remaining -= 1
        self._timer_job = self.after(1000, self._tick)

    def confirm_quit(self):
        self.finish(quit_early=True)

    def finish(self, quit_early):
        if self.finished:
            return
        self.finished = True
        if self._timer_job is not None:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        if not quit_early and self.user_answers[self.index] is None:
            self.user_answers[self.index] = self._read_current_answer()
        elapsed = self.minutes * 60 - max(self.remaining, 0)
        self.app.show_shape_test_result(self.sd["key"], self.questions, self.user_answers,
                                          elapsed, self.minutes * 60)


class ShapeTestResultPage(tk.Frame):
    def __init__(self, master, app, key, questions, user_answers, elapsed_seconds, total_seconds):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.key = key
        sd = SHAPE_DEFS_BY_KEY[key]
        decimal = sd["decimal"]

        graded = []
        correct_n = 0
        for q, ua in zip(questions, user_answers):
            ans = q["answer"]
            if ua is None:
                ok, ua_text = False, "안 씀"
            elif decimal:
                ok = abs(ua - ans) < 0.005
                ua_text = _fmt_num(ua)
            else:
                ok = ua == ans
                ua_text = str(ua)
            if ok:
                correct_n += 1
            dims_phrase = ", ".join(f"{k} {v}cm" for k, v in q["dims"].items())
            ans_text = f"{_fmt_num(ans)}{sd['unit']}"
            graded.append({"prob": f"{dims_phrase} → {sd['quantity_label']}",
                             "user": ua_text, "answer": ans_text, "ok": ok})

        total = len(questions)
        accuracy = round(correct_n / total * 100) if total else 0
        mm, ss = divmod(elapsed_seconds, 60)

        save_history_entry({
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "op": key, "op_label": f"{sd['shape_label']} {sd['quantity_label']}", "level": 1,
            "correct": correct_n, "total": total, "accuracy": accuracy,
            "elapsed_seconds": elapsed_seconds,
        })

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(16, 0))
        RoundButton(top, "← 도형", self.app.show_shape_home, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text=f"{sd['shape_label']} {sd['quantity_label']} 시험 결과", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 22, "bold")).pack(pady=(10, 16))

        stat_row = tk.Frame(self, bg=BG)
        stat_row.pack()
        for label, value, color in [
            ("맞은 개수", f"{correct_n}/{total}", GREEN_DARK),
            ("정답률", f"{accuracy}%", PRIMARY),
            ("걸린 시간", f"{mm:02d}:{ss:02d}", TEXT),
        ]:
            box = tk.Frame(stat_row, bg=CARD, width=160, height=92,
                             highlightbackground="#dbe7ee", highlightthickness=1)
            box.pack_propagate(False)
            box.pack(side="left", padx=8)
            tk.Label(box, text=value, bg=CARD, fg=color, font=(FONT_NAME, 22, "bold")).pack(pady=(18, 0))
            tk.Label(box, text=label, bg=CARD, fg=MUTED, font=(FONT_NAME, 11)).pack()

        scroll = ScrollableFrame(self, bg=BG, height=260)
        scroll.pack(fill="both", expand=True, padx=40, pady=(18, 6))
        for i, g in enumerate(graded, start=1):
            row_bg = CARD if g["ok"] else "#fdeceb"
            row = tk.Frame(scroll.inner, bg=row_bg, highlightbackground="#dbe7ee", highlightthickness=1)
            row.pack(fill="x", pady=3, padx=2)
            mark_color = GREEN_DARK if g["ok"] else RED
            tk.Label(row, text=("○" if g["ok"] else "✕"), bg=row_bg, fg=mark_color,
                      font=(FONT_NAME, 13, "bold"), width=2).pack(side="left", padx=(10, 4), pady=8)
            tk.Label(row, text=f"{i}. {g['prob']} = {g['answer']}", bg=row_bg, fg=TEXT,
                      font=(FONT_NAME, 12), anchor="w", justify="left",
                      wraplength=460).pack(side="left", padx=4, pady=8)
            if not g["ok"]:
                tk.Label(row, text=f"내 답: {g['user']}", bg=row_bg, fg=RED,
                          font=(FONT_NAME, 11), anchor="e").pack(side="right", padx=10)

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=(12, 16))
        retry_minutes = max(1, round(total_seconds / 60))
        RoundButton(btn_row, "같은 설정으로 다시", lambda: self.app.show_shape_test(key, total, retry_minutes),
                     bg=PRIMARY, size=12, width=15, pady=9).pack(side="left", padx=6)
        RoundButton(btn_row, "시험 설정으로", self.app.show_shape_test_setup, bg=DISABLED, fg=TEXT,
                     size=12, width=12, pady=9).pack(side="left", padx=6)


class HistoryPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="기록", bg=BG, fg=TEXT, font=(FONT_NAME, 28, "bold")).pack(pady=(14, 4))
        tk.Label(self, text="지금까지 본 시험 결과예요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 13)).pack(pady=(0, 16))

        entries = load_history()
        total_tests = len(entries)
        avg_acc = round(sum(e["accuracy"] for e in entries) / total_tests) if total_tests else 0

        stat_row = tk.Frame(self, bg=BG)
        stat_row.pack()
        for label, value, color in [
            ("본 시험 수", f"{total_tests}회", PRIMARY),
            ("평균 정답률", f"{avg_acc}%", GREEN_DARK),
        ]:
            box = tk.Frame(stat_row, bg=CARD, width=180, height=90,
                             highlightbackground="#dbe7ee", highlightthickness=1)
            box.pack_propagate(False)
            box.pack(side="left", padx=10)
            tk.Label(box, text=value, bg=CARD, fg=color, font=(FONT_NAME, 22, "bold")).pack(pady=(18, 0))
            tk.Label(box, text=label, bg=CARD, fg=MUTED, font=(FONT_NAME, 11)).pack()

        if entries:
            scroll = ScrollableFrame(self, bg=BG, height=340)
            scroll.pack(fill="both", expand=True, padx=40, pady=(18, 10))
            for e in reversed(entries):
                row = tk.Frame(scroll.inner, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
                row.pack(fill="x", pady=4, padx=2)
                tk.Label(row, text=e["ts"], bg=CARD, fg=MUTED, font=(FONT_NAME, 11),
                          width=13, anchor="w").pack(side="left", padx=(14, 4), pady=10)
                tk.Label(row, text=f"{e['op_label']} Lv.{e['level']}", bg=CARD, fg=TEXT,
                          font=(FONT_NAME, 12, "bold"), width=14, anchor="w").pack(side="left", pady=10)
                acc_color = GREEN_DARK if e["accuracy"] >= 80 else (ACCENT_DARK if e["accuracy"] >= 50 else RED)
                tk.Label(row, text=f"{e['correct']}/{e['total']}문제 ({e['accuracy']}%)", bg=CARD, fg=acc_color,
                          font=(FONT_NAME, 12, "bold")).pack(side="left", padx=(4, 0), pady=10)
                mm, ss = divmod(e.get("elapsed_seconds", 0), 60)
                tk.Label(row, text=f"{mm:02d}:{ss:02d}", bg=CARD, fg=MUTED,
                          font=(FONT_NAME, 11)).pack(side="right", padx=14, pady=10)
        else:
            tk.Label(self, text="아직 시험 기록이 없어요.",
                      bg=BG, fg=MUTED, font=(FONT_NAME, 13)).pack(pady=60)

        RoundButton(self, "기록 전체 초기화", self.reset, bg=DISABLED, fg=TEXT,
                     size=12, width=14, pady=8).pack(pady=(6, 10))

    def reset(self):
        clear_history()
        self.app.show_history()


class VersionHistoryPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, "← 처음으로", self.app.show_main_menu, bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")

        tk.Label(self, text="버전 이력", bg=BG, fg=TEXT, font=(FONT_NAME, 28, "bold")).pack(pady=(14, 4))
        tk.Label(self, text="이 프로그램이 업데이트된 내용이에요", bg=BG, fg=MUTED,
                  font=(FONT_NAME, 13)).pack(pady=(0, 20))

        scroll = ScrollableFrame(self, bg=BG, height=460)
        scroll.pack(fill="both", expand=True, padx=50, pady=(0, 16))

        for entry in VERSION_HISTORY:
            row = tk.Frame(scroll.inner, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
            row.pack(fill="x", pady=6, padx=2)

            head = tk.Frame(row, bg=CARD)
            head.pack(fill="x", padx=18, pady=(14, 6))
            tk.Label(head, text=entry["version"], bg=CARD, fg=PRIMARY,
                      font=(FONT_NAME, 16, "bold")).pack(side="left")
            tk.Label(head, text=entry["date"], bg=CARD, fg=MUTED,
                      font=(FONT_NAME, 11)).pack(side="left", padx=(10, 0))

            for note in entry["notes"]:
                tk.Label(row, text=f"·  {note}", bg=CARD, fg=TEXT, font=(FONT_NAME, 12),
                          anchor="w", justify="left", wraplength=580).pack(fill="x", padx=22, pady=(0, 6))


class WrongAnswerReviewPage(tk.Frame):
    """Re-presents only the questions missed in a completed 시험, one at a
    time, with immediate right/wrong feedback (unlike the exam itself) --
    this is for remediation, not measurement."""

    def __init__(self, master, app, op, questions):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app
        self.op = op
        self.mode = OP_ANSWER_MODE[op]
        self.questions = questions
        self.index = 0
        self.correct_count = 0
        self.state = "answering"

        back_label, back_cmd = CATEGORY_BACK[OP_CATEGORY[op]]
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 0))
        RoundButton(top, back_label, getattr(self.app, back_cmd), bg=BG, fg=MUTED,
                     size=12, bold=False, pady=4).pack(side="left")
        tk.Label(top, text=f"{OP_LABELS[op]} 오답노트", bg=BG, fg=TEXT,
                  font=(FONT_NAME, 16, "bold")).pack(side="left", padx=(18, 0))
        self.progress_label = tk.Label(top, text="", bg=BG, fg=MUTED, font=(FONT_NAME, 13))
        self.progress_label.pack(side="right")

        card = tk.Frame(self, bg=CARD, highlightbackground="#dbe7ee", highlightthickness=1)
        card.pack(padx=60, pady=(30, 20), fill="both", expand=True)

        self.canvas, self.problem_label = build_question_display(card, self.mode)

        vcmd = (self.register(self._validate_num), "%P")
        self.widgets = build_mode_input(card, self.mode, vcmd)

        self.feedback_label = tk.Label(card, text=" ", bg=CARD, font=(FONT_NAME, 16, "bold"),
                                         wraplength=560, justify="center")
        self.feedback_label.pack(pady=(18, 0))

        self.main_btn = RoundButton(card, "확인", self.on_main_button, bg=ACCENT, fg=TEXT,
                                      size=16, width=12, pady=12)
        self.main_btn.pack(pady=(22, 30))

        self.app.set_enter_handler(self.on_main_button)
        self.show_question()

    def _validate_num(self, proposed):
        return validate_mode_num(self.mode, proposed)

    def show_question(self):
        q = self.questions[self.index]
        self.problem_label.config(text=q["prob_text"])
        if self.mode == "clock":
            draw_clock_diagram(self.canvas, q["hour"], q["minute"])
        self.progress_label.config(text=f"{self.index + 1} / {len(self.questions)}문제 복습중")
        clear_mode_input(self.widgets)
        self.feedback_label.config(text=" ", fg=TEXT)
        self.main_btn.config(text="확인", bg=ACCENT, fg=TEXT)
        self.state = "answering"

    def on_main_button(self):
        if self.state == "answering":
            self.check_answer()
        else:
            self.advance()

    def check_answer(self):
        q = self.questions[self.index]
        user_answer = read_mode_input(self.widgets)
        if user_answer is None:
            return
        is_correct, correct_text = grade_question(q, user_answer)

        if is_correct:
            self.correct_count += 1
            self.feedback_label.config(text="정답이에요! 이번엔 맞혔어요", fg=GREEN_DARK)
        else:
            self.feedback_label.config(text=f"이번에도 오답이에요. 정답은 {correct_text}예요", fg=RED)

        disable_mode_input(self.widgets)
        is_last = self.index == len(self.questions) - 1
        self.main_btn.config(text="복습 마치기" if is_last else "다음 →", bg=PRIMARY, fg="white")
        self.state = "checked"
        self.focus_set()
        self.main_btn.focus_set()

    def advance(self):
        if self.index < len(self.questions) - 1:
            self.index += 1
            self.show_question()
        else:
            self.app.show_review_done(self.op, len(self.questions), self.correct_count)


class ReviewDonePage(tk.Frame):
    def __init__(self, master, app, op, total, correct):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)
        self.app = app

        tk.Label(self, text="복습 완료!", bg=BG, fg=TEXT, font=(FONT_NAME, 32, "bold")).pack(pady=(160, 14))
        tk.Label(self, text=f"틀렸던 {total}문제 중 {correct}문제를 이번엔 맞혔어요",
                  bg=BG, fg=MUTED, font=(FONT_NAME, 15)).pack(pady=(0, 34))
        back_label, back_cmd = CATEGORY_BACK[OP_CATEGORY[op]]
        cat_name = CATEGORY_NAME[OP_CATEGORY[op]]
        # cat_name is already a full "...으로/로" phrase for some categories
        # (e.g. "gradenew" -> "처음으로") -- don't double up the particle.
        suffix = "" if cat_name.endswith(("로", "으로")) else _ro_josa(cat_name)
        RoundButton(self, f"{cat_name}{suffix}", getattr(self.app, back_cmd), bg=PRIMARY, size=14,
                     width=16, pady=10).pack()


def main():
    app = App()
    app.after(200, app.maybe_show_version_notice)
    app.after(800, app.maybe_check_for_update)
    app.mainloop()


if __name__ == "__main__":
    main()
