import enum
import logging
import sys

import click

import yaslha
import yaslha.dumper


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

__scriptname__ = yaslha.__pkgname__ + '/converter'
__version__ = yaslha.__version__

ACCEPTED_TYPES = ['SLHA', 'YAML', 'JSON']  # decided to use capital letters


class CaseInsensitiveChoice(click.Choice):
    # TODO: use upcoming `case_insensitive` feature
    # https://github.com/pallets/click/pull/887/commits/138a6e3ad1dbe657e09717bc05ebfbc535f4770d
    def __init__(self, choices):
        self.keys = dict()
        for c in choices:
            if isinstance(c, enum.Enum):
                self.keys[c.name.upper()] = c
            else:
                self.keys[c.upper()] = c
        super().__init__(self.keys.keys())

    def convert(self, value, param, ctx):
        return self.keys[super().convert(value.upper(), param, ctx)]


@click.command(help='Convert SLHA from/to YAML and JSON', context_settings=dict(help_option_names=['-h', '--help']))
# @click.option('--input-type', type=CaseInsensitiveChoice(['Auto'] + ACCEPTED_TYPES), default='Auto',show_default=True)
@click.option('--input-type', type=CaseInsensitiveChoice(['SLHA']), default='SLHA',
              help='(JSON/YAML input is not yet implemented.)')
@click.option('--output-type', type=CaseInsensitiveChoice(ACCEPTED_TYPES), default='SLHA', show_default=True)
@click.argument('input', type=click.Path(exists=True, dir_okay=False), required=False)
@click.argument('output', type=click.Path(dir_okay=False), required=False)
@click.option('-S', 'input_type', flag_value='SLHA', help='synonym of --input-type=SLHA')
@click.option('-J', 'input_type', flag_value='JSON', help='(not implemented)')
@click.option('-Y', 'input_type', flag_value='YAML', help='(not implemented)')
@click.option('-s', 'output_type', flag_value='SLHA', help='synonym of --output-type=SLHA')
@click.option('-j', 'output_type', flag_value='JSON', help='synonym of --output-type=JSON')
@click.option('-y', 'output_type', flag_value='YAML', help='synonym of --output-type=YAML')
@click.option('--comments', type=CaseInsensitiveChoice(yaslha.dumper.CommentsPreserve), default='NONE',
              help='comments to be kept', show_default=True)
@click.option('--blocks', type=CaseInsensitiveChoice(yaslha.dumper.BlocksOrder), default='DEFAULT',
              help='Order of SLHA blocks')
@click.option('--values', type=CaseInsensitiveChoice(yaslha.dumper.ValuesOrder), default='DEFAULT',
              help='Order of values')
@click.version_option(__version__, '-V', '--version', prog_name=yaslha.__pkgname__ + '/converter')
# @click.option('-v', '--verbose', is_flag=True, default=False, help="Show verbose output")
def convert(**kwargs):
    # TODO: use 'input-type' option
    # input_type = kwargs['input_type'] or 'Auto'
    output_type = kwargs['output_type'] or 'SLHA'

    if kwargs['input']:
        with open(kwargs['input']) as f:
            input_string = f.read()
    else:
        input_string = sys.stdin.read()
    slha = yaslha.parse(input_string)

    output_string = yaslha.dump(data=slha, output_type=output_type,
                                comments_preserve=yaslha.dumper.CommentsPreserve(kwargs['comments']),
                                blocks_order=yaslha.dumper.BlocksOrder(kwargs['blocks']),
                                values_order=yaslha.dumper.ValuesOrder(kwargs['values']),
                                )

    if kwargs['output']:
        with open(kwargs['output'], 'w') as f:
            f.write(output_string)
    else:
        print(output_string)


@click.command(help='Merge two SLHA files', context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-e', is_flag=True, default=False, help='Read from STDIN and append to the SLHA data')
@click.argument('input', nargs=-1, type=click.Path(exists=True, dir_okay=False), required=False)
@click.version_option(__version__, '-V', '--version', prog_name=yaslha.__pkgname__ + '/merger')
@click.pass_context  # for help
def merge(ctx, **kwargs):
    slha = yaslha.SLHA()
    for i in kwargs['input']:
        with open(kwargs['input']) as f:
            slha.merge(yaslha.parse(f.read()))
    if kwargs['e']:
        slha.merge(yaslha.parse(sys.stdin.read()))

    if not (slha.blocks or slha.decays):
        click.echo(ctx.get_usage())
        ctx.exit(1)

    output_string = yaslha.dump(data=slha, output_type='SLHA',
                                comments_preserve=yaslha.dumper.CommentsPreserve.ALL,
                                blocks_order=yaslha.dumper.BlocksOrder.KEEP,
                                values_order=yaslha.dumper.ValuesOrder.KEEP,
                                )
    print(output_string)
