
all:

clean:
	$(RM) mcp.pdf
	$(RM) -r build

requires:
	echo mcp-helpers python3-sphinx texlive-latex-base

build/mcp.tex: index.rst
	sphinx-build -b latex -D latex_paper_size=letter . build

mcp.pdf: build/mcp.tex
	cd build && pdflatex mcp.tex
	cp build/mcp.pdf .

.PHONY:: all clean requires
