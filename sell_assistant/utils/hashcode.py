#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'Dhyana'


def convert_n_bytes(n, b):
    bits = b * 8
    return (n + 2 ** (bits - 1)) % 2 ** bits - 2 ** (bits - 1)


def convert_4_bytes(n):
    return convert_n_bytes(n, 4)


def get_hash_code(s):
    h = 0
    n = len(s)
    for i, c in enumerate(s):
        h += ord(c) * 31 ** (n - 1 - i)
    return convert_4_bytes(h)
