from collections import OrderedDict
from typing import List, MutableMapping, Any, Tuple, TypeVar, Union, Sequence  # noqa: F401

import yaslha


KeyType = Union[None, int, Tuple[int, ...]]
ValueType = Union[int, float, str, List[str]]   # SPINFO/DCINFO 3 and 4 may be multiple
ChannelType = Tuple[int, ...]
U = TypeVar('U', bound=KeyType)


def _float(obj):
    # type: (Any)->float
    if isinstance(obj, str):
        obj = obj.replace('d', 'e').replace('D', 'E')
    return float(obj)


def _clean(obj):
    # type: (Any)->Any
    if isinstance(obj, OrderedDict):
        return OrderedDict((k, _clean(v)) for k, v in obj.items()
                           if not (v is None or (hasattr(v, '__len__') and len(v) == 0)))
    elif isinstance(obj, dict):
        return dict((k, _clean(v)) for k, v in obj.items()
                    if not (v is None or (hasattr(v, '__len__') and len(v) == 0)))
    elif isinstance(obj, list):
        return list(v for v in obj if not (v is None or (hasattr(v, '__len__') and len(v) == 0)))
    else:
        return obj


def _flatten(obj, level=-1):
    # type: (Sequence[Any], int)->List[Any]
    return [element
            for item in obj
            for element in (_flatten(item, level-1)
                            if level != 0 and hasattr(item, '__iter__') and not isinstance(item, str)
                            else [item])]


BLOCKS_DEFAULT_ORDER = [
    'SPINFO', 'DCINFO', 'MODSEL', 'SMINPUTS', 'MINPAR', 'EXTPAR',
    'VCKMIN', 'UPMNSIN', 'MSQ2IN', 'MSU2IN', 'MSD2IN', 'MSL2IN', 'MSE2IN', 'TUIN', 'TDIN', 'TEIN',
    'MASS', 'NMIX', 'UMIX', 'VMIX', 'ALPHA', 'FRALPHA', 'HMIX', 'GAUGE', 'MSOFT',
    'MSQ2', 'MSU2', 'MSD2', 'MSL2', 'MSE2',
    'STOPMIX', 'SBOTMIX', 'STAUMIX', 'USQMIX', 'DSQMIX', 'SELMIX', 'SNUMIX',
    'AU', 'AD', 'AE', 'TU', 'TD', 'TE', 'YU', 'YD', 'YE',
]   # type: List[str]


def sort_blocks_default(block_names):
    # type: (List[str])->List[str]
    """Sort block names according to specified order."""
    result = []
    block_names = [n.upper() for n in block_names]
    peeked = OrderedDict([(k, False) for k in block_names])

    for name in [n.upper() for n in BLOCKS_DEFAULT_ORDER]:
        if name in block_names:
            result.append(name)
            peeked[name] = True

    return result + [k for k, v in peeked.items() if not v]


PID_GROUPS = ['sm', 'gluino', 'sq-up', 'sq-down', 'neut', 'char', 'slep', 'snu', 'susy', 'others', 'not_int']


def sort_pids_default(pids: List[U]) -> List[Union[U, int]]:
    """Sort block names according to specified order."""
    tmp = dict((key, []) for key in PID_GROUPS)  # type: MutableMapping[str, List[Union[U, int]]]

    for i in pids:
        if not isinstance(i, int):
            tmp['not_int'].append(i)  # fail safe
            continue

        j = i % 1000000
        if i < 1000000:
            tmp['sm'].append(i)
        elif i >= 3000000:
            tmp['others'].append(i)
        elif i == 1000021:
            tmp['gluino'].append(i)
        elif j <= 6:
            if j % 2:
                tmp['sq-down'].append(i)
            else:
                tmp['sq-up'].append(i)
        elif i in [1000022, 1000023, 1000025, 1000035]:
            tmp['neut'].append(i)
        elif i in [1000024, 1000037]:
            tmp['char'].append(i)
        elif j in [11, 13, 15]:
            tmp['slep'].append(i)
        elif j in [12, 14, 16]:
            tmp['snu'].append(i)
        else:
            tmp['susy'].append(i)
    return [pid for group in PID_GROUPS for pid in sorted(tmp[group])]


def copy_sorted_decay_block(decay, sort_by_br=True):
    # type: (yaslha.Decay, bool)->yaslha.Decay
    def ordering(pid):
        # type: (int)->Tuple[int, int, int]
        return (abs(pid) < 1000000, abs(pid), pid < 0)  # SUSY first, smaller first, positive first

    def ch_sorted(ch):
        # type: (ChannelType)->ChannelType
        return tuple(sorted(ch, key=lambda pid: ordering(pid)))

    def sort_key(ch):
        # type: (ChannelType)->List[int]
        return _flatten([len(ch), [ordering(pid) for pid in ch]])

    ch_mapping = [(ch, ch_sorted(ch), br) for ch, br in decay.items_br()]
    if sort_by_br:
        tmp = sorted(ch_mapping, key=lambda x: x[2], reverse=True)
        # group similar br (to absorb difference in float-precision)
        tmp2 = []
        i = 0
        while i < len(tmp):
            tmp2.append([tmp[i]])
            j = i+1
            while j < len(tmp):
                if tmp[j][2] < tmp[i][2] * 0.95:
                    break
                tmp2[-1].append(tmp[j])
                j += 1
            i = j
        ch_mapping = _flatten([sorted(x, key=lambda m: sort_key(m[1])) for x in tmp2], level=1)
    else:  # sort first by #daughter, and then abs(daughters)
        ch_mapping.sort(key=lambda m: sort_key(m[1]))

    new_decay = yaslha.Decay(decay)
    for mapping in ch_mapping:
        new_decay.rename_channel(mapping[0], mapping[1])
    return new_decay
