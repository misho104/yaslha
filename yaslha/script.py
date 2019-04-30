"""Scripts of this package."""

import enum
import logging
import re
import sys
from typing import (  # noqa: F401
    Any,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Type,
    Union,
)

import click
import coloredlogs

import yaslha
import yaslha.dumper

logger = logging.getLogger(__name__)


ACCEPTED_TYPES = ["SLHA", "YAML", "JSON"]  # decided to use capital letters


class _Choice(click.Choice):
    def __init__(self, choices: Union[Sequence[str], Type[enum.Enum]]) -> None:
        if isinstance(choices, enum.EnumMeta):
            self.keys = {c.name.upper(): c for c in choices}  # type: ignore
        else:
            self.keys = {c.upper(): c.upper() for c in choices}
        super().__init__(self.keys.keys())

    def convert(self, value, param, ctx):  # type: ignore
        return self.keys[super().convert(value.upper(), param, ctx)]


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    yaslha.__version__, "-V", "--version", prog_name=yaslha.__pkgname__
)
def main() -> None:
    """Handle SLHA format data."""
    coloredlogs.install(logger=logging.getLogger(), fmt="%(levelname)8s %(message)s")


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--input-type",
    type=_Choice(["AUTO", *ACCEPTED_TYPES]),
    default="AUTO",
    show_default=True,
    help="(JSON/YAML input is not yet implemented.)",
    hidden=True,  # until other parsers are implemented
)
@click.option(
    "--output-type",
    type=_Choice(ACCEPTED_TYPES),
    default="SLHA",
    show_default=True,
    help="Output format.",
)
@click.argument("input", type=click.Path(exists=True, dir_okay=False), required=False)
@click.argument("output", type=click.Path(dir_okay=False), required=False)
@click.option("-S", "input_type", flag_value="SLHA", hidden=True)
@click.option("-J", "input_type", flag_value="JSON", hidden=True)
@click.option("-Y", "input_type", flag_value="YAML", hidden=True)
@click.option("-s", "output_type", flag_value="SLHA", hidden=True)
@click.option("-j", "output_type", flag_value="JSON", hidden=True)
@click.option("-y", "output_type", flag_value="YAML", hidden=True)
@click.option(
    "--comments",
    type=_Choice(yaslha.dumper.CommentsPreserve),
    default="NONE",
    show_default=True,
    help="Comment types to keep.",
)
@click.option(
    "--blocks",
    type=_Choice(yaslha.dumper.BlocksOrder),
    default="DEFAULT",
    help="Order of blocks.",
)
@click.option(
    "--values",
    type=_Choice(yaslha.dumper.ValuesOrder),
    default="DEFAULT",
    help="Order of values.",
)
def convert(**kwargs):
    # type: (Any)->None
    """Convert or reformat SLHA data files.

    Currently this package converts SLHA input to SLHA, JSON, or YAML format.
    Text from the standard input (STDIN) is used if no file is specified.
    Shorthanded options -s -y -j are available for --output-type option.
    """
    input_type = kwargs["input_type"] or "AUTO"
    output_type = kwargs["output_type"] or "SLHA"

    if kwargs["input"]:
        with open(kwargs["input"]) as f:
            input_string = f.read()
    else:
        logger.warning("Reading from STDIN...")
        input_string = sys.stdin.read()
    slha = yaslha.parse(input_string, input_type=input_type)

    output_string = yaslha.dump(
        slha=slha,
        output_type=output_type,
        comments_preserve=yaslha.dumper.CommentsPreserve(kwargs["comments"]),
        blocks_order=yaslha.dumper.BlocksOrder(kwargs["blocks"]),
        values_order=yaslha.dumper.ValuesOrder(kwargs["values"]),
    )

    if kwargs["output"]:
        with open(kwargs["output"], "w") as f:
            f.write(output_string)
    else:
        print(output_string)


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-e", is_flag=True, default=False, help="Read the last data to merge from STDIN." ""
)
@click.argument(
    "input", nargs=-1, type=click.Path(exists=True, dir_okay=False), required=True
)
@click.pass_context  # for help
def merge(ctx, **kwargs):
    # type: (click.core.Context, Any)->None
    """Merge SLHA files.

    Input and output are in SLHA format. Duplicated data are overwritten by
    later files. If -e option is specified, input from standard input (STDIN)
    is used as the last data.
    """
    slha = yaslha.SLHA()
    for i in kwargs["input"]:
        with open(i) as f:
            slha.merge(yaslha.parse(f.read()))
    if kwargs["e"]:
        slha.merge(yaslha.parse(sys.stdin.read()))

    if not (slha.blocks or slha.decays):
        click.echo(ctx.get_usage())
        ctx.exit(1)

    output_string = yaslha.dump(
        slha=slha,
        output_type="SLHA",
        comments_preserve=yaslha.dumper.CommentsPreserve.ALL,
        blocks_order=yaslha.dumper.BlocksOrder.KEEP,
        values_order=yaslha.dumper.ValuesOrder.KEEP,
    )
    print(output_string)


@main.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("blocks", type=str, required=True)
@click.argument("input", type=click.Path(exists=True, dir_okay=False), required=False)
@click.pass_context  # for help
def extract(ctx, **kwargs):
    # type: (click.core.Context, Any)->None
    """Extract specified blocks from SLHA file.

    BLOCKS is a comma-separated list of block names (or decay-block PIDs) to
    extract and INPUT is the input SLHA file. If INPUT is not specified, data
    is read from standard input (STDIN).
    """
    blocks = kwargs["blocks"].split(",")
    if not blocks:
        click.echo("No blocks specified.")
        exit(1)

    if kwargs["input"]:
        with open(kwargs["input"]) as f:
            input_string = f.read()
    else:
        input_string = sys.stdin.read()
    slha = yaslha.parse(input_string)
    dumper = yaslha.dumper.SLHADumper()

    output_list = []  # type: List[Sequence[str]]
    for block in blocks:
        if re.match(r"^\d+$", block):
            try:
                output_list.append(dumper.dump_block(slha.decays[int(block)]))
            except KeyError:
                click.echo("DECAY block for PID {} not found.".format(block))
                exit(1)
        else:
            try:
                output_list.append(dumper.dump_block(slha.blocks[block]))
            except KeyError:
                click.echo("Block {} not found".format(block.upper()))
                exit(1)
    output_string = "\n".join("\n".join(block) for block in output_list)
    print(output_string)
