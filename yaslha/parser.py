from typing import TypeVar, Union  # noqa: F401

import yaslha
import yaslha.exceptions as exceptions
import yaslha.line


SLHAParserStatesType = Union[None, 'yaslha.Block', 'yaslha.Decay']


class SLHAParser:
    def __init__(self, *args, **kwargs):
        pass

    def in_info_block(self, block_obj: 'yaslha.Block')->bool:
        """Method to decide if a block is an "info block" or not.

        Info blocks accepts only "InfoLine"s (1x,I5,3x,A), which have
        one (and only one) index followed by any string. InfoLines are
        not accepted by any other blocks.
        """
        return isinstance(block_obj, yaslha.Block) and block_obj.name.endswith('INFO')

    def parse(self, text: str)->'yaslha.SLHA':
        """Parse SLHA format text."""

        processing = None        # type: SLHAParserStatesType
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
            elif isinstance(obj, yaslha.line.DecayBlockLine):
                # Start a new decay block
                processing = yaslha.Decay(obj.pid, width=obj.width)
                slha.decays[obj.pid] = processing

            elif isinstance(obj, yaslha.line.CommentLine):
                # comment line
                pass  # TODO: handle comment lines

            elif obj:
                # data line
                if isinstance(processing, yaslha.Block) and self.in_info_block(processing):
                    # fill info block
                    if isinstance(obj, yaslha.line.InfoLine):
                        if obj.key in processing:
                            processing.get_line_obj(obj.key).append(obj.value, obj.comment)
                        else:
                            processing[obj.key] = obj
                    else:
                        exceptions.InvalidFormatWarning(line, f'InfoBlock {processing.name}').call()

                elif isinstance(processing, yaslha.Block):
                    # fill usual block
                    processing[obj.key] = obj

                elif isinstance(processing, yaslha.Decay):
                    # fill decay block
                    if isinstance(obj, yaslha.line.DecayLine):
                        processing[obj.key] = obj
                    else:
                        exceptions.InvalidFormatWarning(line, f'Decay {processing.pid}').call()

                else:
                    exceptions.OrphanLineWarning(line).call()
            else:
                exceptions.UnrecognizedLineWarning(line).call()
        return slha