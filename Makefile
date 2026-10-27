.PHONY: docs test unittest record live resource rst_auto

PYTHON := $(shell which python)

PROJ_DIR      := .
DOC_DIR       := ${PROJ_DIR}/docs
BUILD_DIR     := ${PROJ_DIR}/build
DIST_DIR      := ${PROJ_DIR}/dist
TEST_DIR      := ${PROJ_DIR}/test
TESTFILE_DIR  := ${TEST_DIR}/testfile
DATASET_DIR   := ${TESTFILE_DIR}/dataset
SRC_DIR       := ${PROJ_DIR}/hfutils
TEMPLATES_DIR := ${PROJ_DIR}/templates
RESOURCE_DIR  := ${PROJ_DIR}/resource

RANGE_DIR      ?= .
RANGE_TEST_DIR := ${TEST_DIR}/${RANGE_DIR}
RANGE_SRC_DIR  := ${SRC_DIR}/${RANGE_DIR}

GAMES ?= arknights fgo genshin girlsfrontline azurlane

COV_TYPES ?= xml term-missing

# RST documentation generation variables
PYTHON_CODE_DIR   := ${SRC_DIR}
RST_DOC_DIR       := ${DOC_DIR}/source/api_doc
PYTHON_CODE_FILES := $(shell find ${PYTHON_CODE_DIR} -name "*.py" ! -name "__*.py" 2>/dev/null)
RST_DOC_FILES     := $(patsubst ${PYTHON_CODE_DIR}/%.py,${RST_DOC_DIR}/%.rst,${PYTHON_CODE_FILES})
PYTHON_NONM_FILES := $(shell find ${PYTHON_CODE_DIR} -name "__init__.py" 2>/dev/null)
RST_NONM_FILES    := $(foreach file,${PYTHON_NONM_FILES},$(patsubst %/__init__.py,%/index.rst,$(patsubst ${PYTHON_CODE_DIR}/%,${RST_DOC_DIR}/%,$(patsubst ${PYTHON_CODE_DIR}/__init__.py,${RST_DOC_DIR}/index.rst,${file}))))

package:
	$(PYTHON) -m build --sdist --wheel --outdir ${DIST_DIR}
build:
	pyinstaller -D -F $(shell python -m tools.resources) -n hfutils -c hfutils_cli.py
clean:
	rm -rf ${DIST_DIR} ${BUILD_DIR} *.egg-info
	rm -rf build dist hfutils.spec

test: unittest

unittest:
	UNITTEST=1 \
		pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" --cov-branch \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},) \
		$(if ${WORKERS},-n ${WORKERS},) \
		${PYTEST_ARGS}

# Re-record the cassettes of the tests under RANGE_DIR against the real Hugging Face (needs HF_TOKEN), see test/cassettes/README.md
record:
	UNITTEST=1 pytest "${RANGE_TEST_DIR}" -sv -m unittest --hf-record=rewrite ${PYTEST_ARGS}

# Run the tests against the real Hugging Face without any cassette (drift detection)
live:
	UNITTEST=1 pytest "${RANGE_TEST_DIR}" -sv -m unittest --hf-record=live ${PYTEST_ARGS}

# RST documentation generation: one page per module, one index per package (auto_rst.py), then the top-level index
rst_auto: ${RST_DOC_FILES} ${RST_NONM_FILES} auto_rst_top_index.py
	python auto_rst_top_index.py -i ${PYTHON_CODE_DIR} -o ${DOC_DIR}/source

${RST_DOC_DIR}/%.rst: ${PYTHON_CODE_DIR}/%.py auto_rst.py Makefile
	@mkdir -p $(dir $@)
	python auto_rst.py -i $< -o $@

# A package index carries the toctree that auto_rst.py builds by listing the package directory, so it goes stale when a module
# or subpackage appears or is edited beside it, not only when __init__.py itself changes: the wildcards need the stem, which is why
# they are deferred to the second expansion. A deleted module cannot make anything out of date: remove its page by hand.
.SECONDEXPANSION:

${RST_DOC_DIR}/%/index.rst: ${PYTHON_CODE_DIR}/%/__init__.py $$(wildcard ${PYTHON_CODE_DIR}/$$*/*.py) $$(wildcard ${PYTHON_CODE_DIR}/$$*/*/__init__.py) auto_rst.py Makefile
	@mkdir -p $(dir $@)
	python auto_rst.py -i $< -o $@

${RST_DOC_DIR}/index.rst: ${PYTHON_CODE_DIR}/__init__.py $(wildcard ${PYTHON_CODE_DIR}/*.py) $(wildcard ${PYTHON_CODE_DIR}/*/__init__.py) auto_rst.py Makefile
	@mkdir -p $(dir $@)
	python auto_rst.py -i $< -o $@

docs:
	$(MAKE) -C "${DOC_DIR}" build
pdocs:
	$(MAKE) -C "${DOC_DIR}" prod
