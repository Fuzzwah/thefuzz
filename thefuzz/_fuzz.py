#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals
from difflib import SequenceMatcher
from . import utils


###########################
# Basic Scoring Functions #
###########################

@utils.check_for_equivalence
@utils.check_empty_string
def ratio(s1, s2):
    s1, s2 = utils.make_type_consistent(s1, s2)

    m = SequenceMatcher(None, s1, s2)
    return utils.intr(100 * m.ratio())


@utils.check_for_equivalence
@utils.check_empty_string
def partial_ratio(s1, s2):
    """"Return the ratio of the most similar substring
    as a number between 0 and 100."""
    s1, s2 = utils.make_type_consistent(s1, s2)

    if len(s1) <= len(s2):
        shorter = s1
        longer = s2
    else:
        shorter = s2
        longer = s1

    m = SequenceMatcher(None, shorter, longer)
    blocks = m.get_matching_blocks()

    # each block represents a sequence of matching characters in a string
    # of the form (idx_1, idx_2, len)
    # the best partial match will block align with at least one of those blocks
    #   e.g. shorter = "abcd", longer = XXXbcdeEEE
    #   block = (1,3,3)
    #   best score === ratio("abcd", "Xbcd")
    scores = []
    for block in blocks:
        long_start = block[1] - block[0] if (block[1] - block[0]) > 0 else 0
        long_end = long_start + len(shorter)
        long_substr = longer[long_start:long_end]

        m2 = SequenceMatcher(None, shorter, long_substr)
        r = m2.ratio()
        if r > .995:
            return 100
        else:
            scores.append(r)

    return utils.intr(100 * max(scores))


##############################
# Advanced Scoring Functions #
##############################

def _sort_tokens(s):
    """Return a string with token sorted."""
    # pull tokens
    tokens = s.split()

    # sort tokens and join
    sorted_string = u" ".join(sorted(tokens))
    return sorted_string.strip()


# Sorted Token
#   find all alphanumeric tokens in the string
#   sort those tokens and take ratio of resulting joined strings
#   controls for unordered string elements
def _token_sort(s1, s2, partial):
    sorted1 = _sort_tokens(s1)
    sorted2 = _sort_tokens(s2)

    if partial:
        return partial_ratio(sorted1, sorted2)
    else:
        return ratio(sorted1, sorted2)


def token_sort_ratio(s1, s2, processor=None):
    """Return a measure of the sequences' similarity between 0 and 100
    but sorting the token before comparing.
    """
    return _token_sort(s1, s2, partial=False)


def partial_token_sort_ratio(s1, s2, processor=None):
    """Return the ratio of the most similar substring as a number between
    0 and 100 but sorting the token before comparing.
    """
    return _token_sort(s1, s2, partial=True)


def _token_set(s1, s2, partial):
    """Find all alphanumeric tokens in each string...
        - treat them as a set
        - construct two strings of the form:
            <sorted_intersection><sorted_remainder>
        - take ratios of those two strings
        - controls for unordered partial matches"""

    if s1 == s2:
        return 100

    if not utils.validate_string(s1):
        return 0
    if not utils.validate_string(s2):
        return 0

    # pull tokens
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())

    intersection = tokens1.intersection(tokens2)
    diff1to2 = tokens1.difference(tokens2)
    diff2to1 = tokens2.difference(tokens1)

    sorted_sect = " ".join(sorted(intersection))
    sorted_1to2 = " ".join(sorted(diff1to2))
    sorted_2to1 = " ".join(sorted(diff2to1))

    combined_1to2 = sorted_sect + " " + sorted_1to2
    combined_2to1 = sorted_sect + " " + sorted_2to1

    # strip
    sorted_sect = sorted_sect.strip()
    combined_1to2 = combined_1to2.strip()
    combined_2to1 = combined_2to1.strip()

    if partial:
        ratio_func = partial_ratio
    else:
        ratio_func = ratio

    pairwise = [
        ratio_func(sorted_sect, combined_1to2),
        ratio_func(sorted_sect, combined_2to1),
        ratio_func(combined_1to2, combined_2to1)
    ]
    return max(pairwise)


def token_set_ratio(s1, s2, processor=None):
    return _token_set(s1, s2, partial=False)


def partial_token_set_ratio(s1, s2, processor=None):
    return _token_set(s1, s2, partial=True)


def WRatio(s1, s2, processor=None):
    if not utils.validate_string(s1):
        return 0
    if not utils.validate_string(s2):
        return 0

    # should we look at partials?
    try_partial = True
    unbase_scale = .95
    partial_scale = .90

    base = ratio(s1, s2)
    len_ratio = float(max(len(s1), len(s2))) / min(len(s1), len(s2))

    # if strings are similar length, don't use partials
    if len_ratio < 1.5:
        try_partial = False

    # if one string is much much shorter than the other
    if len_ratio > 8:
        partial_scale = .6

    if try_partial:
        partial = partial_ratio(s1, s2) * partial_scale
        ptsor = partial_token_sort_ratio(s1, s2) \
            * unbase_scale * partial_scale
        ptser = partial_token_set_ratio(s1, s2) \
            * unbase_scale * partial_scale

        return utils.intr(max(base, partial, ptsor, ptser))
    else:
        tsor = token_sort_ratio(s1, s2) * unbase_scale
        tser = token_set_ratio(s1, s2) * unbase_scale

        return utils.intr(max(base, tsor, tser))
