# cSpell:words docutils

import re

import docutils.nodes
import sphinx.writers.latex


class MyTranslator(sphinx.writers.latex.LaTeXTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bibcache_dict = self.gen_bibcache_dict()

    def gen_bibcache_dict(self):
        bibcache = self.builder.env.bibtex_cache
        result = {}
        for cite_key in bibcache.get_all_cited_keys():
            # cited_docnames = bibcache.get_cited_docnames(cite_key)
            label = bibcache.get_label_from_key(cite_key)
            result[label] = cite_key
        return result

    re_uri = re.compile("%(.+?)#(.+?)")

    def visit_reference(self, node):
        if node.get("internal") and self.re_uri.match(node.get("refuri", "")):
            label = node.astext().lstrip("[").rstrip("]")
            key = self.bibcache_dict.get(label)
            if key:
                # special treatment for cite
                self.body.append(r"\cite{" + key + "}")
                raise docutils.nodes.SkipNode
        # otherwise usual treatment
        super().visit_reference(node)

    def visit_citation_reference(self, node):
        origref = str(node.children[0])[1:-1]
        if self.in_title:
            pass
        else:
            self.body.append("\\cite{%s}" % (origref))
            raise docutils.nodes.SkipNode

    def visit_field_list(self, node):
        self.body.append("\\begin{description}\n")
        if self.table:
            self.table.has_problematic = True

    def depart_field_list(self, node):
        self.body.append("\\end{description}\n")

    def visit_field_name(self, node):
        self.in_term += 1
        ctx = ""
        if node.get("ids"):
            ctx = "\\phantomsection"
            for node_id in node["ids"]:
                ctx += self.hypertarget(node_id, anchor=False)
        ctx += "}] \\leavevmode"
        self.body.append("\\item[\\mdseries\\sffamily{")
        self.context.append(ctx)

    def visit_emphasis(self, node):
        if node.get("refclass") == "type":
            self.body.append(r"\emphasisfortype{")
        else:
            return super().visit_emphasis(node)

    def visit_desc_parameter(self, node):
        if not self.first_param:
            self.body.append(", ")
        else:
            self.first_param = 0
        if not node.hasattr("noemph"):
            self.body.append(r"\paramemph{")

    def visit_figure(self, node):
        if node.attributes.get("subfigure") != 2:
            return super().visit_figure(node)

        labels = self.hypertarget_to(node)
        self.restrict_footnote(node)
        if self.table:
            raise NotImplementedError
        elif node.get("align", "") in ("left", "right"):
            raise NotImplementedError
        elif self.in_minipage:
            raise NotImplementedError
        else:
            self.body.append("\n\\begin{subfigure}[t]{0.49\\textwidth}\n\\centering\n")
            if any(isinstance(child, docutils.nodes.caption) for child in node):
                self.body.append("\\capstart\n")
            self.context.append(labels + "\\end{subfigure}")
        for child in node:
            if isinstance(child, docutils.nodes.image):
                child["width"] = "0.9\\textwidth"


def setup(app):
    app.set_translator("latex", MyTranslator)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
