# Makefile for LaTeX compilation

# Main document (without .tex extension)
MAIN = main

# LaTeX compiler
LATEX = pdflatex

# All source files
TEXFILES = $(wildcard *.tex)

.PHONY: all clean distclean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex $(TEXFILES)
	$(LATEX) -interaction=nonstopmode $(MAIN)
	bibtex $(MAIN)
	$(LATEX) -interaction=nonstopmode $(MAIN)
	$(LATEX) -interaction=nonstopmode $(MAIN)

clean:
	rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz comment.cut

distclean: clean
	rm -f $(MAIN).pdf
