"""Parsers for SLHA package.

Parsers for SLHA-format, JSON-format, and YAML-format are provided.
"""

import logging
from typing import Any, List, Optional, Type, Union

import yaslha.line
import yaslha.slha
from yaslha.block import AbsBlock, Block, Decay, InfoBlock

SLHAParserStatesType = Union[None, Block, InfoBlock, Decay]


logger = logging.getLogger(__name__)


class SLHAParser:
    """SLHA-format file parser."""

    def __init__(self, **kw: Any) -> None:
        self.processing = None  # type: SLHAParserStatesType

    def _parse_line(self, line: str) -> Optional[yaslha.line.AbsLine]:
        if not line.strip():
            return None  # empty line will be ignored
        if isinstance(self.processing, InfoBlock):
            classes = [
                yaslha.line.BlockHeadLine,
                yaslha.line.DecayHeadLine,
                yaslha.line.InfoLine,
                yaslha.line.CommentLine,
            ]  # type: List[Type[yaslha.line.AbsLine]]
        elif isinstance(self.processing, Block):
            classes = [
                yaslha.line.BlockHeadLine,
                yaslha.line.DecayHeadLine,
                yaslha.line.NoIndexLine,
                yaslha.line.OneIndexLine,
                yaslha.line.TwoIndexLine,
                yaslha.line.ThreeIndexLine,
                yaslha.line.DecayLine,  # for extensions
                yaslha.line.CommentLine,
            ]
        elif isinstance(self.processing, yaslha.Decay):
            classes = [
                yaslha.line.BlockHeadLine,
                yaslha.line.DecayHeadLine,
                yaslha.line.DecayLine,
                yaslha.line.CommentLine,
            ]
        elif self.processing is None:
            classes = [
                yaslha.line.BlockHeadLine,
                yaslha.line.DecayHeadLine,
                yaslha.line.CommentLine,
            ]
        else:
            logger.critical("Unexpected state: %s", self.processing)
            raise RuntimeError

        for c in classes:
            obj = c.construct(line)
            if obj:
                return obj
        raise ValueError(line)

    def parse(self, text: str) -> yaslha.slha.SLHA:
        """Parse SLHA format text and return SLHA object."""
        self.processing = None
        slha = yaslha.slha.SLHA()
        comment_lines = []  # type: List[str]

        for line in text.splitlines():
            try:
                obj = self._parse_line(line)
                if obj is None:
                    continue
            except ValueError:
                logger.warning("Unrecognized line: %s", line)
                continue

            # comment handling
            if isinstance(obj, yaslha.line.CommentLine):
                comment_lines.append(obj.comment)
                continue
            elif isinstance(obj, yaslha.line.AbsLine):
                obj.pre_comment = comment_lines
                comment_lines = []
            else:
                raise NotImplementedError(obj)

            # line handling
            if isinstance(obj, yaslha.line.BlockHeadLine):
                self.processing = AbsBlock.new(obj)
                assert self.processing is not None
                slha.add_block(self.processing)
            elif isinstance(obj, yaslha.line.DecayHeadLine):
                self.processing = Decay(obj)
                assert self.processing is not None
                slha.add_block(self.processing)
            elif isinstance(obj, yaslha.line.InfoLine):
                if not isinstance(self.processing, InfoBlock):
                    logger.critical("InfoLine found outside of INFO block: %s", line)
                    raise ValueError(self.processing)
                self.processing.append_line(obj)
            elif isinstance(obj, yaslha.line.ValueLine):
                if self.processing is None:
                    logger.critical("ValueLine found outside of block: %s", line)
                    raise ValueError(self.processing)
                self.processing.update_line(obj)
            else:
                raise TypeError(obj)

        # tail comments
        slha.tail_comment = comment_lines
        self.processing = None
        return slha
