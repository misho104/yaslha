# cSpell:words docutils toctree sphinx isalpha astext numentries blist toctreenode
# cSpell:words rindex tocs nodetext


import re

from docutils import nodes, transforms
from docutils.parsers.rst.roles import set_classes
from docutils.parsers.rst.directives.images import Figure as FigureDirective
from sphinx import addnodes
from sphinx.domains.python import PyXRefRole
from sphinx.environment.adapters.toctree import TocTree
from sphinx.environment.collectors.toctree import TocTreeCollector
from sphinx.transforms import SphinxContentsFilter
from sphinx.writers.html import HTMLTranslator


def typ_role_options(target, options={}):
    refdomain = options.pop("refdomain", "py")
    reftype = options.pop("reftype", "class")
    return {
        **options,
        **{
            "class": ["py-typ"],
            "refspecific": True,
            "refexplicit": False,
            "refdomain": refdomain,
            "reftype": reftype,
            "reftarget": target,
        },
    }


class TwoFigureDirective(FigureDirective):
    def run(self):
        nodes = super().run()
        nodes[0].attributes["subfigure"] = 2
        return nodes


class typ_role_class:
    options = {"refdomain": str, "reftype": str}

    def __call__(self, name, rawtext, text, lineno, inliner, options={}, content=[]):
        set_classes(options)
        parsed = re.findall(r"([A-Za-z_.]+|[^A-Za-z_.]+)", text)
        children = [
            addnodes.pending_xref(
                "", nodes.Text(t, ""), **(typ_role_options(t, options))
            )
            if t[0].isalpha()
            else nodes.Text(t, "")
            for t in parsed
        ]
        return [nodes.emphasis(rawtext, "", *children, refclass="type")], []


typ_role = typ_role_class()


def ar_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    set_classes(options)
    if "classes" not in options:
        options["classes"] = ["py-ar"]
    elif "py-ar" not in options["classes"]:
        options["classes"].append("py-ar")
    return [nodes.inline(rawtext, text, **options)], []


def math_if_latex_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [nodes.math(rawtext, text, no_math="html")], []


class MyPyXRefRole(PyXRefRole):
    re_target_exp = re.compile(
        r"\A(?P<prefix>\W+)?(?P<context>\w.+)\.(?P<target>[^.]+)\Z"
    )

    def process_link(self, env, refnode, has_explicit_title, title, target):
        new_target = None
        m = self.re_target_exp.match(target)
        if m:  # attr of another class
            refnode["reftype"] = "class"
            new_target = (m.group("prefix") or "") + m.group("context")
            return super().process_link(
                env, refnode, has_explicit_title, title, new_target
            )
        else:  # this class' attribute; no link.
            processed = super().process_link(
                env, refnode, has_explicit_title, title, target
            )
            return processed[0], ""


class MyTocTreeCollector(TocTreeCollector):  # noqa: D101
    def process_doc(self, app, doctree):  # noqa: C901, D102
        docname = app.env.docname
        numentries = [0]  # nonlocal again...

        def traverse_in_section(node, cls):
            result = []
            if isinstance(node, cls):
                result.append(node)
            for child in node.children:
                if isinstance(child, nodes.section):
                    continue
                result.extend(traverse_in_section(child, cls))
            return result

        def build_toc(node, depth=1):
            entries = []
            for sectionnode in node:
                if isinstance(sectionnode, addnodes.only):
                    onlynode = addnodes.only(expr=sectionnode["expr"])
                    blist = build_toc(sectionnode, depth)
                    if blist:
                        onlynode += blist.children  # type: ignore
                        entries.append(onlynode)
                    continue
                if isinstance(sectionnode, addnodes.desc) and sectionnode[
                    "objtype"
                ] in ["class", "function", "data"]:
                    pass
                elif not isinstance(sectionnode, nodes.section):
                    for toctreenode in traverse_in_section(
                        sectionnode, addnodes.toctree
                    ):
                        item = toctreenode.copy()
                        entries.append(item)
                        # important: do the inventory stuff
                        TocTree(app.env).note(docname, toctreenode)
                    continue
                title = sectionnode[0]
                # copy the contents of the section title, but without references
                # and unnecessary stuff
                visitor = SphinxContentsFilter(doctree)
                title.walkabout(visitor)
                nodetext = visitor.get_entry_text()
                anchorname = None
                objtype = sectionnode.get("objtype")
                if isinstance(sectionnode, addnodes.desc) and objtype in [
                    "class",
                    "function",
                    "data",
                ]:
                    names = [n for n in nodetext if isinstance(n, addnodes.desc_name)]
                    signature = [
                        n for n in sectionnode.traverse(addnodes.desc_signature)
                    ]
                    if not (names and signature):
                        raise RuntimeError(sectionnode)
                    if objtype == "data":
                        name = "".join([n.astext() for n in names])
                    else:
                        name = objtype + " " + "".join([n.astext() for n in names])
                    nodetext = [nodes.Text(name)]
                    anchorname = "#" + signature[0]["ids"][0]
                if not numentries[0]:
                    # for the very first toc entry, don't add an anchor
                    # as it is the file's title anyway
                    anchorname = ""
                elif not anchorname:
                    anchorname = "#" + sectionnode["ids"][0]
                numentries[0] += 1
                # make these nodes:
                # list_item -> compact_paragraph -> reference
                reference = nodes.reference(
                    "",
                    "",
                    internal=True,
                    refuri=docname,
                    anchorname=anchorname,
                    *nodetext,
                )
                if objtype:
                    reference["objtype"] = objtype
                para = addnodes.compact_paragraph("", "", reference)
                item = nodes.list_item("", para)
                sub_item = build_toc(sectionnode, depth + 1)
                item += sub_item
                entries.append(item)
            if entries:
                return nodes.bullet_list("", *entries)
            return []

        toc = build_toc(doctree)
        if toc:
            app.env.tocs[docname] = toc
        else:
            app.env.tocs[docname] = nodes.bullet_list("")
        app.env.toc_num_entries[docname] = numentries[0]


class ReturnTypeAddRole(transforms.Transform):
    default_priority = 780

    def apply(self):
        for field in self.document.traverse(nodes.field):
            if any(n.astext() == "Returns" for n in field.traverse(nodes.field_name)):
                for node in field.traverse(condition=lambda n: n.children):
                    if isinstance(node.children[0], nodes.emphasis):
                        orig = node.children[0]
                        node.children[0] = typ_role(
                            None, orig.rawsource, orig.astext(), None, None
                        )[0][0]


class MyHtmlTranslator(HTMLTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # change toc tree
    def visit_bullet_list(self, node):
        for n in node.traverse(nodes.reference):
            if not n.children:
                continue
            # modify usual "section" index
            if n.get("objtype"):
                # Remove section number from class, functions, etc. in TOC-lines.
                n["secnumber"] = ""
            elif len(n.get("secnumber", [])) > 1 and len(n.children) == 1:
                pass
                # # Remove parent-package name from TOC lines.
                # orig_text = n.children[0].astext()
                # try:
                #     strip = orig_text.split(" ")[0].rindex(".")
                #     n.children[0] = nodes.Text(orig_text[strip + 1:], orig_text)
                # except ValueError:
                #     pass
        return super().visit_bullet_list(node)

    def visit_math(self, node):
        if "html" in node.get("no_math", "").split(","):
            self.body.append(node.astext())
            raise nodes.SkipNode
        return super().visit_math(node)


class twofigure(nodes.General, nodes.Element):
    pass


def setup(app):  # noqa: D103
    app.add_role("typ", typ_role)
    app.add_role("ar", ar_role)
    app.add_role("m", math_if_latex_role)
    # MyPyXRefRole is imported in conf.py
    app.add_env_collector(MyTocTreeCollector)
    app.add_transform(ReturnTypeAddRole)
    app.add_directive("twofigure", TwoFigureDirective)
    app.set_translator("html", MyHtmlTranslator)
    app.set_translator("readthedocs", MyHtmlTranslator)
    app.set_translator("readthedocssinglehtmllocalmedia", MyHtmlTranslator)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
