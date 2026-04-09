INPUT_PDF ?= pipeline_root/input/arvms_specs/arvms_spec/arvms_spec.pdf
SRC := pipeline_root/src

PDF_NAME := $(notdir $(INPUT_PDF))
PDF_STEM := $(basename $(PDF_NAME))
INPUT_TO_SPEC_PARENT := $(patsubst pipeline_root/input/%,%,$(dir $(INPUT_PDF)))
ARTIFACTS := pipeline_root/artifacts/$(INPUT_TO_SPEC_PARENT)
OUTPUT_DIR := pipeline_root/output/$(INPUT_TO_SPEC_PARENT)
REPORT_PATH := $(OUTPUT_DIR)$(PDF_STEM)_ai_analyzes.html

s0:
	python3 $(SRC)/S0_extractor.py $(INPUT_PDF)

s1:
	python3 $(SRC)/S1_normalizer.py $(ARTIFACTS)/00_raw_extract.json

s2:
	python3 $(SRC)/S2_preflight.py $(ARTIFACTS)/01_normalized.json

s3:
	python3 $(SRC)/S3_ai_structurer.py $(ARTIFACTS)/01_normalized.json

s4:
	python3 $(SRC)/S4_ai_analyzer.py $(ARTIFACTS)/03_ai_structured.json

s5:
	python3 $(SRC)/S5_renderer.py $(ARTIFACTS)/04_ai_analyzed.json

pipeline: s0 s1 s2 s3 s4 s5
	@printf "HTML report: %s\n" "$(REPORT_PATH)"

analyze: pipeline

render-arch:
	plantuml -tsvg architecture/pipeline_overview_v1.puml

.PHONY: s0 s1 s2 s3 s4 s5 pipeline analyze render-arch
