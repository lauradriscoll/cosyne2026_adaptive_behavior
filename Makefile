MAIN    = main
TECTONIC = tools/bin/tectonic.exe

# Download URL for the Tectonic binary (Windows x64)
TECTONIC_VERSION = 0.17.0
TECTONIC_URL = https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-$(TECTONIC_VERSION)-x86_64-pc-windows-msvc.zip

.PHONY: all panels pdf clean tectonic

# Build placeholder panels then compile the PDF
all: panels pdf

# Generate panel PDFs from figure scripts
panels:
	python figures/fig1/make_panels.py
	python figures/fig2/make_panels.py

# Generate placeholder panels (useful before real data is loaded)
panels-placeholder:
	python tools/make_panels_example.py

# Compile the LaTeX document using the local Tectonic binary
pdf: $(TECTONIC)
	$(TECTONIC) $(MAIN).tex

# Download Tectonic if not present
$(TECTONIC):
	$(MAKE) tectonic

tectonic:
	python tools/download_tectonic.py

# Remove LaTeX build artifacts (keeps panel PDFs and Tectonic binary)
clean:
	rm -f $(MAIN).pdf
