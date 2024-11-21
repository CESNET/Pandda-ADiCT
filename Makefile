BUILDDIR := build

.PHONY: all
all: clean pkg

.PHONY: clean
clean:
	rm -rf $(BUILDDIR)

.PHONY: build
build:
	mkdir -p build/ && cd $(BUILDDIR) && cmake -DCMAKE_INSTALL_PREFIX=/usr -Wdev ..

.PHONY: pkg
pkg: build
	cd $(BUILDDIR) && cpack -G RPM
