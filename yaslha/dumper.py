"""Dumpers to write SLHA data in various format."""

import enum
import json
import re
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import (
    Any,
    ClassVar,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import ruamel.yaml

import yaslha
import yaslha.block
import yaslha.config
import yaslha.line
import yaslha.utility
from yaslha._line import format_comment

BlockLike = Union[yaslha.block.Block, yaslha.block.InfoBlock, yaslha.block.Decay]
T = TypeVar("T")


@enum.unique
class BlocksOrder(enum.Enum):
    """Options for block ordering."""

    DEFAULT = 0
    KEEP = 1
    ABC = 2


@enum.unique
class ValuesOrder(enum.Enum):
    """Options for value ordering."""

    DEFAULT = 0
    KEEP = 1
    SORTED = 2


@enum.unique
class CommentsPreserve(enum.Enum):
    """Options for comment handling."""

    NONE = 0
    TAIL = 1
    ALL = 2

    @property
    def keep_line(self):
        # type: ()->bool
        """Return if to keep line-level comments."""
        return self == CommentsPreserve.ALL

    @property
    def keep_tail(self):
        # type: ()->bool
        """Return if to keep tail comments of value lines."""
        return self != CommentsPreserve.NONE


class AbsDumper(metaclass=ABCMeta):
    """Abstract class for YASLHA dumpers."""

    @abstractmethod
    def _read_config(self, sw: yaslha.config.SectionWrapper) -> None:
        self._config = {
            "blocks_order": sw.get_enum("blocks_order", BlocksOrder),
            "values_order": sw.get_enum("values_order", ValuesOrder),
            "comments_preserve": sw.get_enum("comments_preserve", CommentsPreserve),
        }  # type: MutableMapping[str, Any]

    @abstractmethod
    def config(self, k: str) -> Any:
        """Get a current value of configuration."""
        return self._config[k]

    @abstractmethod
    def set_config(self, k: str, v: Any) -> None:
        """Set configuration."""
        if any(
            [
                k == "blocks_order" and not isinstance(v, BlocksOrder),
                k == "values_order" and not isinstance(v, ValuesOrder),
                k == "comments_preserve" and not isinstance(v, CommentsPreserve),
            ]
        ):
            raise TypeError(k, v)
        self._config[k] = v

    @abstractmethod
    def __init__(self, **kw: Any) -> None:
        pass

    @abstractmethod
    def dump(self, slha: "yaslha.slha.SLHA") -> str:
        """Return dumped string of an SLHA object."""

    def _blocks_sorted(self, slha):
        # type: (yaslha.slha.SLHA)->List[Union[yaslha.Block, yaslha.InfoBlock]]
        slha.normalize(decays=False)
        if self.config("blocks_order") == BlocksOrder.KEEP:
            return list(slha.blocks.values())
        block_names = list(slha.blocks.keys())
        if self.config("blocks_order") == BlocksOrder.ABC:
            block_names.sort()
        else:
            block_names = yaslha.utility.sort_blocks_default(block_names)
        return [slha.blocks[name] for name in block_names]

    def _decays_sorted(self, slha):
        # type: (yaslha.slha.SLHA)->List[yaslha.Decay]
        slha.normalize(blocks=False)
        if self.config("values_order") == ValuesOrder.KEEP:
            return list(slha.decays.values())
        pids = list(slha.decays.keys())
        if self.config("values_order") == ValuesOrder.SORTED:
            pids.sort()
        else:
            pids = yaslha.utility.sort_pids_default(pids)
        return [slha.decays[pid] for pid in pids]

    def _block_lines_ordered(self, block):
        # type: (BlockLike)->Sequence[yaslha.line.AbsLine]
        sort = self.config("values_order") != ValuesOrder.KEEP
        if (
            isinstance(block, yaslha.block.Block)
            and self.config("values_order") == ValuesOrder.DEFAULT
            and block.name == "MASS"
        ):
            keys = yaslha.utility.sort_pids_default(list(block.keys()))
            return [block._data[k] for k in keys]
        else:
            return [line for _, line in block._lines(sort=sort)]

    @staticmethod
    def _document_out(lines: Sequence[str]) -> List[str]:
        return [
            "#"
            if not lines
            else line.replace(" ", "#", 1)
            if line.startswith(" ")
            else "#" + line.replace("  ", " ", 1)
            for line in lines
        ]


class SLHADumper(AbsDumper):
    """A dumper class for SLHA output."""

    def _update_line_option(self) -> None:
        self.line_option.block_str = self.config("block_str")
        self.line_option.decay_str = self.config("decay_str")
        self.line_option.comment = self.config("comments_preserve").keep_tail
        self.line_option.pre_comment = self.config("comments_preserve").keep_line

    def _read_config(self, sw: yaslha.config.SectionWrapper) -> None:
        super()._read_config(sw)
        self._config["separate_blocks"] = sw.getboolean("separate_blocks")
        self._config["forbid_last_linebreak"] = sw.getboolean("forbid_last_linebreak")
        self._config["document_blocks"] = sw.get_list("document_blocks")
        self._config["block_str"] = sw["block_str"]
        self._config["decay_str"] = sw["decay_str"]
        self._config["float_lower"] = sw.getboolean("float_lower")
        self._config["write_version"] = sw.getboolean("write_version")
        self._update_line_option()

    def config(self, k: str) -> Any:
        """Get a current value of configuration."""
        return super().config(k)

    def set_config(self, k: str, v: Any) -> None:
        """Set configuration."""
        # check before set
        pass
        # set
        super().set_config(k, v)
        # operations after set
        if k in ["block_str", "decay_str", "comments_preserve"]:
            self._update_line_option()

    def __init__(self, **kw: Any) -> None:
        self.line_option = yaslha.line.LineOutputOption()
        self._read_config(yaslha.cfg["SLHADumper"])
        for k, v in kw.items():
            self.set_config(k, v)

    def _version_comment(self) -> str:
        return "# written by {} {}".format(yaslha.__pkgname__, yaslha.__version__)

    def _version_comment_regexp(self) -> str:
        return r"^\s*#\s*written\s+by\s+{}\s+".format(yaslha.__pkgname__)

    def dump(self, slha: "yaslha.slha.SLHA") -> str:
        """Return SLHA-format text of an SLHA object."""
        document_blocks = [
            v.upper() for v in self.config("document_blocks")  # normalize to upper
        ]  # type: Sequence[str]

        lines = []  # type: List[str]
        for block in self._blocks_sorted(slha):
            lines.extend(
                self.dump_block(block, document_block=(block.name in document_blocks))
            )
            if self.config("separate_blocks"):
                lines.append("#")
        for decay in self._decays_sorted(slha):
            lines.extend(
                self.dump_block(decay, document_block=(decay.pid in document_blocks))
            )
            if self.config("separate_blocks"):
                lines.append("#")
        if self.config("separate_blocks"):
            lines.pop()
        if self.config("comments_preserve").keep_line:
            for c in slha.tail_comment:
                lines.append(format_comment(c, add_sharp=True, strip=False))

        # replace version string
        if self.config("write_version"):
            re_version = re.compile(self._version_comment_regexp())
            lines = [v for v in lines if not re_version.match(v)]
            lines.insert(0, self._version_comment())

        result = "\n".join(lines) + "\n"

        if self.config("forbid_last_linebreak"):
            result = result.rstrip()

        return result

    def dump_block(self, block, document_block=False):
        # type: (BlockLike, bool)->List[str]
        """Return SLHA-format text of a block."""
        lines = block.head.to_slha(self.line_option)
        for line in self._block_lines_ordered(block):
            lines.extend(line.to_slha(self.line_option))

        # special spacing for MASS block
        if isinstance(block, yaslha.block.Block) and block.name == "MASS":
            re_mass = re.compile(r"^\s*(\d+)")
            lines = [
                re_mass.sub(lambda x: " {:>9}".format(x.group(1)), i) for i in lines
            ]

        return self._document_out(lines) if document_block else lines


class AbsMarshalDumper(AbsDumper):
    """An abstract class for dumpers handling marshaled data."""

    SCHEME_VERSION = 3  # type: ClassVar[int]

    def _read_config(self, sw: yaslha.config.SectionWrapper) -> None:
        return super()._read_config(sw)

    def config(self, k: str) -> Any:
        """Get a current value of configuration."""
        return super().config(k)

    def set_config(self, k: str, v: Any) -> None:
        """Set configuration."""
        super().set_config(k, v)

    def _format_specification(self) -> Any:
        return OrderedDict(
            type="SLHA",
            formatter="{} {}".format(yaslha.__pkgname__, yaslha.__version__),
            scheme=self.SCHEME_VERSION,
        )

    def marshal(self, slha):
        # type: (yaslha.slha.SLHA)->Mapping[str, Any]
        """Return Mashaled object of an SLHA object."""
        blocks = OrderedDict()  # type: MutableMapping[str, Any]
        for block in self._blocks_sorted(slha):
            blocks[block.name] = self.marshal_block(block)
        decays = OrderedDict()  # type: MutableMapping[int, Any]
        for decay in self._decays_sorted(slha):
            decays[decay.pid] = self.marshal_block(decay)
        tail_comments = [format_comment(c, strip=False) for c in slha.tail_comment]

        result = OrderedDict()  # type: MutableMapping[str, Any]
        result["format"] = self._format_specification()
        if blocks:
            result["block"] = blocks
        if decays:
            result["decay"] = decays
        if self.config("comments_preserve").keep_line and tail_comments:
            result["tail_comments"] = tail_comments
        return result

    def marshal_block(self, block: "BlockLike") -> Mapping[str, Any]:
        """Return marshaled object of a block."""
        info = block.head.dump()
        value = []
        comment = []
        comment.extend(block.head._dump_comment())
        for line in self._block_lines_ordered(block):
            value.append(line.dump())
            comment.extend(line._dump_comment())

        comment = [
            c
            for c in comment
            if (c[0] == "pre" and self.config("comments_preserve").keep_line)
            or (c[0] != "pre" and self.config("comments_preserve").keep_tail)
        ]

        result = OrderedDict()  # type: MutableMapping[str, Any]
        if info:
            result["info"] = info
        if value:
            result["values"] = value
        if comment:
            result["comments"] = comment
        return result


class YAMLDumper(AbsMarshalDumper):
    """A dumper for YAML output."""

    def __init__(self, **kw: Any) -> None:
        self._read_config(yaslha.cfg["YAMLDumper"])
        for k, v in kw.items():
            self.set_config(k, v)

        self.yaml = ruamel.yaml.YAML()
        self.yaml.default_flow_style = None

        # we need not it is marked as omap (OrderedDict);
        # it could be just a dict as an output.
        # (but we may change the mind....)
        self.yaml.representer.yaml_representers[
            OrderedDict
        ] = self.yaml.representer.yaml_representers[dict]
        # # another idea...
        # def represent_list(self, data):
        #     flow_style = all(isinstance(i, str) or not hasattr(i, '__iter__')
        #                      for i in data)
        #     return self.represent_sequence(u'tag:yaml.org,2002:seq', data,
        #                                    flow_style=flow_style)
        # self.yaml.representer.yaml_representers[list] = represent_list

    def dump(self, slha: "yaslha.slha.SLHA") -> str:
        """Return YAML-format text of an SLHA object."""
        stream = ruamel.yaml.compat.StringIO()
        self.yaml.dump(self.marshal(slha), stream)
        return cast(str, stream.getvalue())


class JSONDumper(AbsMarshalDumper):
    """A dumper for JSON output."""

    def __init__(self, **kw: Any) -> None:
        self._read_config(yaslha.cfg["JSONDumper"])
        for k, v in kw.items():
            self.set_config(k, v)

        self.indent = 2

    def dump(self, slha: "yaslha.slha.SLHA") -> str:
        """Return JSON-format text of an SLHA object."""
        return json.dumps(self.marshal(slha), indent=self.indent)
