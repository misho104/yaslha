from typing import Union, List, Tuple, cast, Any  # noqa: F401

import yaslha
import yaslha.exceptions as exceptions
import yaslha.line
from yaslha.line import CommentPosition


SLHAParserStatesType = Union[None, 'yaslha.Block', 'yaslha.Decay']


class SLHAParser:
    def __init__(self, **kwargs):
        # type: (Any)->None
        pass

    def in_info_block(self, block_obj):
        # type: (yaslha.Block)->bool
        """Method to decide if a block is an "info block" or not.

        Info blocks accepts only "InfoLine"s (1x,I5,3x,A), which have
        one (and only one) index followed by any string. InfoLines are
        not accepted by any other blocks.
        """
        return isinstance(block_obj, yaslha.Block) and block_obj.name.endswith('INFO')

    def parse(self, text):
        # type: (str)->yaslha.SLHA
        """Parse SLHA format text."""

        processing = None        # type: SLHAParserStatesType
        comment = list()         # type: List[yaslha.line.CommentLine]
        slha = yaslha.SLHA()

        for line in text.splitlines():
            # parse line; special treatment for INFO blocks.
            if isinstance(processing, yaslha.Block) and self.in_info_block(processing):
                obj = yaslha.line.parse_string_in_info_block(line)
            else:
                obj = yaslha.line.parse_string(line)

            if isinstance(obj, yaslha.line.BlockLine):
                # Start a new block
                processing = yaslha.Block(obj.name, q=obj.q, head_comment=obj.comment)
                slha.blocks[obj.name] = processing
                if comment:
                    processing.set_line_comment(CommentPosition.Prefix, comment)
                    comment = list()

            elif isinstance(obj, yaslha.line.DecayBlockLine):
                # Start a new decay block
                processing = yaslha.Decay(obj.pid, width=obj.width)
                slha.decays[obj.pid] = processing
                if comment:
                    processing.set_line_comment(CommentPosition.Prefix, comment)
                    comment = list()

            elif isinstance(obj, yaslha.line.CommentLine):
                # A comment line, which will be appended to the next object
                comment.append(obj)

            elif obj:
                # data line
                if isinstance(processing, yaslha.Block) and self.in_info_block(processing):
                    # fill INFO block
                    if isinstance(obj, yaslha.line.InfoLine):
                        if obj.key in processing:
                            line_obj = processing.get_line_obj(obj.key)
                            assert(isinstance(line_obj, yaslha.line.InfoLine))
                            line_obj.append(obj.value, obj.comment)
                        else:
                            processing[obj.key] = obj
                    else:
                        exceptions.InvalidFormatWarning(line, 'InfoBlock ' + processing.name).call()

                elif isinstance(processing, yaslha.Block):
                    # fill usual block
                    processing[obj.key] = obj

                elif isinstance(processing, yaslha.Decay):
                    # fill decay block
                    if isinstance(obj, yaslha.line.DecayLine):
                        processing[cast(Tuple[int], obj.key)] = obj
                    else:
                        exceptions.InvalidFormatWarning(line, 'Decay {}'.format(processing.pid)).call()

                else:
                    exceptions.OrphanLineWarning(line).call()
                    continue

                if comment:
                    keys_len = len(processing.keys())
                    if keys_len == 0:
                        pass  # because obj not added
                    elif keys_len == 1:
                        processing.set_line_comment(CommentPosition.Heading, comment)
                        comment = list()
                    else:
                        processing.set_line_comment(obj.key, comment)
                        comment = list()
            else:
                exceptions.UnrecognizedLineWarning(line).call()
        if comment:
            slha.tail_comment = comment
        return slha
