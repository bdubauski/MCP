
all:

clean:
	$(RM) api.rst
	$(RM) mcp.pdf
	$(RM) -r build

api.rst:
	pip3 install -e ..
	../lib/api_server/api_server & echo $$! > /tmp/mcp_api_server.pid
	sleep 2
	cinp-autodoc > api.rst
	sleep 1
	kill $(shell cat /tmp/mcp_api_server.pid )

requires:
	echo python3-pip python3-sphinx texlive texlive-latex-extra cinp-utils

build/mcp.tex: index.rst api.rst
	sphinx-build -b latex -D latex_paper_size=letter . build

mcp.pdf: build/mcp.tex
	cd build && pdflatex mcp.tex
	cp build/mcp.pdf .

.PHONY:: all clean requires
