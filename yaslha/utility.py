"""Utility module."""

from collections import OrderedDict, defaultdict
from typing import List, MutableMapping, Sequence, TypeVar, Union

from yaslha._line import KeyType

T = TypeVar("T", int, KeyType)


BLOCKS_DEFAULT_ORDER = [
    "SPINFO",
    "DCINFO",
    "MODSEL",
    "SMINPUTS",
    "MINPAR",
    "EXTPAR",
    "VCKMIN",
    "UPMNSIN",
    "MSQ2IN",
    "MSU2IN",
    "MSD2IN",
    "MSL2IN",
    "MSE2IN",
    "TUIN",
    "TDIN",
    "TEIN",
    "MASS",
    "NMIX",
    "UMIX",
    "VMIX",
    "ALPHA",
    "FRALPHA",
    "HMIX",
    "GAUGE",
    "MSOFT",
    "MSQ2",
    "MSU2",
    "MSD2",
    "MSL2",
    "MSE2",
    "STOPMIX",
    "SBOTMIX",
    "STAUMIX",
    "USQMIX",
    "DSQMIX",
    "SELMIX",
    "SNUMIX",
    "AU",
    "AD",
    "AE",
    "TU",
    "TD",
    "TE",
    "YU",
    "YD",
    "YE",
]  # type: Sequence[str]


def sort_blocks_default(block_names: Sequence[str]) -> List[str]:
    """Sort block names according to specified order."""
    result = []
    block_names = [n.upper() for n in block_names]
    peeked = OrderedDict([(k, False) for k in block_names])

    for name in [n.upper() for n in BLOCKS_DEFAULT_ORDER]:
        if name in block_names:
            result.append(name)
            peeked[name] = True

    return result + [k for k, v in peeked.items() if not v]


def sort_pids_default(pids: Sequence[T]) -> List[Union[T, int]]:
    """Sort block names according to specified order."""
    tmp = defaultdict(list)  # type: MutableMapping[str, List[Union[T, int]]]

    for i in pids:
        if not isinstance(i, int):
            tmp["11_not_int"].append(i)  # fail safe
            continue

        j = i % 1000000
        if i < 1000000:
            tmp["01_sm"].append(i)
        elif i >= 3000000:
            tmp["10_others"].append(i)
        elif i == 1000021:
            tmp["02_gluino"].append(i)
        elif j <= 6:
            if j % 2:
                tmp["04_sq-down"].append(i)
            else:
                tmp["03_sq-up"].append(i)
        elif i in [1000022, 1000023, 1000025, 1000035]:
            tmp["05_neut"].append(i)
        elif i in [1000024, 1000037]:
            tmp["06_char"].append(i)
        elif j in [11, 13, 15]:
            tmp["07_slep"].append(i)
        elif j in [12, 14, 16]:
            tmp["08_snu"].append(i)
        else:
            tmp["09_susy"].append(i)
    return [pid for group in sorted(tmp.keys()) for pid in sorted(tmp[group])]
