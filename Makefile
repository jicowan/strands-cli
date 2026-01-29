.PHONY: build install clean patch minor major release

# Default version increment type is patch
VERSION_TYPE ?= patch

# File paths
INIT_FILE := src/strands_cli/__init__.py
PYPROJECT_FILE := pyproject.toml
VERSION_FILE := .version

# Get current version from __init__.py
CURRENT_VERSION := $(shell grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' $(INIT_FILE) | tr -d '"')

# Split version into components
MAJOR := $(shell echo $(CURRENT_VERSION) | cut -d. -f1)
MINOR := $(shell echo $(CURRENT_VERSION) | cut -d. -f2)
PATCH := $(shell echo $(CURRENT_VERSION) | cut -d. -f3)

# Increment version based on VERSION_TYPE
ifeq ($(VERSION_TYPE), major)
	NEW_VERSION := $(shell echo $$(($(MAJOR)+1)).0.0)
else ifeq ($(VERSION_TYPE), minor)
	NEW_VERSION := $(shell echo $(MAJOR).$$(($(MINOR)+1)).0)
else
	NEW_VERSION := $(shell echo $(MAJOR).$(MINOR).$$(($(PATCH)+1)))
endif

# Check if build package is installed
check-build:
	@which pip3 >/dev/null || (echo "pip3 not found. Please install Python3 and pip3"; exit 1)
	@pip3 list | grep -q "build " || pip3 install build

# Default target
build: check-build increment-version
	@echo "Building strands-cli version $(NEW_VERSION)"
	python3 -m build
	@echo "Build complete!"

# Install locally in development mode
install: build
	pip3 install -e .

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Increment version in files
increment-version:
	@echo "Incrementing version from $(CURRENT_VERSION) to $(NEW_VERSION) ($(VERSION_TYPE))"
	@sed -i.bak 's/__version__ = "[0-9]\+\.[0-9]\+\.[0-9]\+"/__version__ = "$(NEW_VERSION)"/' $(INIT_FILE)
	@rm -f $(INIT_FILE).bak
	@sed -i.bak 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+"/version = "$(NEW_VERSION)"/' $(PYPROJECT_FILE)
	@rm -f $(PYPROJECT_FILE).bak
	@echo "$(NEW_VERSION)" > $(VERSION_FILE)
	@echo "Version updated to $(NEW_VERSION)"

# Convenience targets for different version increments
patch:
	@$(MAKE) VERSION_TYPE=patch build

minor:
	@$(MAKE) VERSION_TYPE=minor build

major:
	@$(MAKE) VERSION_TYPE=major build

# Create a release - builds and tags in git
release: build
	@echo "Creating git tag for version $(NEW_VERSION)"
	git add $(INIT_FILE) $(PYPROJECT_FILE) $(VERSION_FILE)
	git commit -m "Release version $(NEW_VERSION)"
	git tag -a v$(NEW_VERSION) -m "Version $(NEW_VERSION)"
	@echo "Tagged version $(NEW_VERSION)"
	@echo "To push tags to remote, run: git push && git push --tags"

# Show help
help:
	@echo "Available targets:"
	@echo "  build       - Build the package (increments patch version by default)"
	@echo "  install     - Build and install the package in development mode"
	@echo "  clean       - Remove build artifacts"
	@echo "  check-build - Ensure the Python build package is installed"
	@echo "  patch       - Increment patch version (1.2.3 -> 1.2.4) and build"
	@echo "  minor       - Increment minor version (1.2.3 -> 1.3.0) and build"
	@echo "  major       - Increment major version (1.2.3 -> 2.0.0) and build"
	@echo "  release     - Build and create a git tag for the new version"
	@echo ""
	@echo "Current version: $(CURRENT_VERSION)"
	@echo ""
	@echo "Note: The build process automatically installs required dependencies like 'build'"