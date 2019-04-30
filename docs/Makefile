SPHINXBUILD   = sphinx-build
SPHINXAPIDOC  = sphinx-apidoc
SOURCEDIR     = .
BUILDDIR      = _build
TEXNAME       = yaslha

.PHONY: help clean Makefile pdf apidoc-init

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@rmdir $(BUILDDIR)

apidoc-init:
	$(SPHINXAPIDOC) -f -M -o . "../yaslha/" "../yaslha/tests/"

pdf: latex
	python ./_themes/latex_finalizer.py $(BUILDDIR)/latex/$(TEXNAME).tex
	export LATEXOPTS='' && cd $(BUILDDIR)/latex && latexmk -pdf --halt-on-error $(TEXNAME).tex
	cp -f $(BUILDDIR)/latex/$(TEXNAME).pdf doc.pdf

latexpdf:
	@$(SPHINXBUILD) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cp -f $(BUILDDIR)/latex/$(TEXNAME).pdf doc_before_finalize.pdf

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
