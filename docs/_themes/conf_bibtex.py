# cSpell:words pybtex unsrt arxiv eprint
import re

import pybtex.plugin
import pybtex.richtext
import pybtex.style.labels.alpha
from pybtex.style.formatting import toplevel
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.formatting.unsrt import date, pages
from pybtex.style.template import (  # noqa: F401
    field,
    first_of,
    href,
    join,
    names,
    optional,
    optional_field,
    sentence,
    tag,
    together,
    words,
)


def format_collaboration(entry, for_label=False):
    collaboration = entry.fields.get("collaboration")
    if collaboration:
        if collaboration.lower().endswith(" collaboration"):
            collaboration = collaboration[:-14]
    return collaboration


class MylabelStyle(pybtex.style.labels.alpha.LabelStyle):
    def author_key_label(self, entry):
        # overwrite by collaboration
        collaboration = format_collaboration(entry)
        if collaboration:
            collaboration = re.sub(r"[^A-Za-z0-9]", "", collaboration)
            return collaboration[:4]
        return super().author_key_label(entry)

    def format_labels(self, sorted_entries):
        return super().format_labels(sorted_entries)

    def format_label(self, entry):
        return super().format_label(entry)


class MyStyle(UnsrtStyle):
    default_sorting_style = "author_year_title"
    default_label_style = "alpha"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.abbreviate_names = True
        self.label_style = MylabelStyle()
        self.format_labels = self.label_style.format_labels

    def format_author_or_editor(self, e):
        collaboration = format_collaboration(e)
        if collaboration:
            return join[tag("strong")[collaboration], " Collaboration"]

        return first_of[optional[self.format_names("author")], self.format_editor(e)]

    def format_title(self, e, which_field, as_sentence=True):
        title_math_match = re.compile("\$(.*?)\$")
        title_raw = e.fields[which_field].lstrip("{").rstrip("}")
        title = title_math_match.sub(r"\(\1\)", title_raw)
        formatted_title = tag("em")[pybtex.richtext.Text(title)]
        if as_sentence:
            return sentence[formatted_title]
        else:
            return formatted_title

    def format_repository(self, e):
        return first_of[
            optional[
                href[join["https://github.com/", field("github", raw=True)], "(GitHub)"]
            ]
        ]

    def get_article_template(self, e):
        arxiv_url = join["https://arxiv.org/abs/", field("eprint", raw=True)]
        doi_url = join["https://doi.org/", field("doi", raw=True)]
        journal_text = join(" ")[
            field("journal"),
            tag("strong")[field("volume")],
            join["(", field("year"), ")"],
            pages,
        ]

        journal = first_of[
            optional[
                join[
                    href[doi_url, journal_text],
                    " [",
                    href[arxiv_url, field("eprint", raw=True)],
                    "]",
                ]
            ],
            optional[
                join[
                    journal_text, " [", href[arxiv_url, field("eprint", raw=True)], "]"
                ]
            ],
            optional[href[doi_url, journal_text]],
            optional[journal_text],
            optional[href[arxiv_url, join["arXiv:", field("eprint", raw=True)]]],
        ]

        template = toplevel[
            sentence[self.format_author_or_editor(e)],
            self.format_title(e, "title"),
            optional[sentence[journal]],
            sentence[optional_field("note")],
            self.format_repository(e),
        ]
        return template

    def get_misc_template(self, e):
        howpublished = first_of[
            # url format
            sentence[
                href[field("url", raw=True), field("url", raw=True)],
                optional[join["Retrieved ", field("retrieved")]],
            ],
            # raw format
            sentence[optional[field("howpublished")], optional[date]],
        ]

        template = toplevel[
            optional[sentence[self.format_author_or_editor(e)]],
            optional[sentence[self.format_names("author")]],
            optional[self.format_title(e, "title")],
            optional[howpublished],
            sentence[optional_field("note")],
        ]
        return template

    def get_techreport_template(self, e):
        if "number" in e.fields and "url" in e.fields:
            number = href[field("url", raw=True), field("number")]
            linked = True
        else:
            number = optional_field("number")
            linked = False

        template = toplevel[
            sentence[self.format_author_or_editor(e)],
            self.format_title(e, "title"),
            sentence[number, field("institution"), optional_field("address"), date],
            sentence[optional_field("note")],
        ]
        if not linked:
            template = template.append(self.format_web_refs(e))

        return template


pybtex.plugin.register_plugin("pybtex.style.formatting", "default", MyStyle)


def setup(app):
    return {"parallel_read_safe": True, "parallel_write_safe": True}
