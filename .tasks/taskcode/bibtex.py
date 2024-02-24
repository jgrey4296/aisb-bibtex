#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

printer = logmod.getLogger("doot._printer")
from random import choice, choices

import doot
import doot.errors
from doot.structs import DootKey
import bib_middleware as BM
import bibtexparser as BTP
from bibtexparser import middlewares as ms

MYBIB                              = "#my_bibtex"
MAX_TAGS                           = 7
UPDATE        : Final[DootKey] = DootKey.make("update_")
FROM_KEY      : Final[DootKey] = DootKey.make("from")

def select_one_entry(spec, state):
    bib_db     = FROM_KEY.to_type(spec, state, type_=BTP.Library)
    update_key = UPDATE.redirect(spec)
    entries    = bib_db.entries
    entry      = choice(entries)
    # TODO have white/black list

    if bool(entry):
        return {update_key : entry}

def build_working_parse_stack(spec, state):
    read_mids = [
        BM.DuplicateHandler(),
        ms.ResolveStringReferencesMiddleware(True),
        ms.RemoveEnclosingMiddleware(True),
        # BM.LatexReader(True, keep_braced_groups=True, keep_math_mode=True),
        BM.IsbnValidator(True),
        ms.SeparateCoAuthors(True),
        BM.NameReader(True),
        BM.TitleReader()
    ]
    return {spec.kwargs.update_ : read_mids}

def build_working_write_stack(spec, state):
    """ Doesn't encode into latex """
    write_mids = [
        BM.NameWriter(True),
        ms.MergeCoAuthors(True),
        # BM.LatexWriter(keep_math=True, enclose_urls=False),
        BM.IsbnWriter(True),
        ms.AddEnclosingMiddleware(allow_inplace_modification=True, default_enclosing="{", reuse_previous_enclosing=False, enclose_integers=True),
    ]
    return {spec.kwargs.update_ : write_mids}

def build_export_write_stack(spec,state):
    """ encodes into latex for compilation """
    write_mids = [
        BM.NameWriter(True),
        ms.MergeCoAuthors(True),
        BM.LatexWriter(keep_math=True, enclose_urls=False),
        BM.IsbnWriter(True),
        ms.AddEnclosingMiddleware(allow_inplace_modification=True, default_enclosing="{", reuse_previous_enclosing=False, enclose_integers=True),
    ]
    return {spec.kwargs.update_ : write_mids}


def oldest(job, specs:list) -> list:
    # Sorts oldest -> newest
    by_mod_time = sorted(specs, key=lambda x: x.extra.fpath.stat().st_mtime)
    return by_mod_time[0:job.spec.extra.select_limit]
