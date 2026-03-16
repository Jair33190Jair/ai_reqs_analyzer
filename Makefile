SPEC      := arvms_spec
ARTIFACTS := pipeline_root/artifacts/arvms_specs/$(SPEC)
SRC       := pipeline_root/src

s0:
	python3 $(SRC)/S0_extractor.py pipeline_root/input/arvms_specs/$(SPEC)

s1:
	python3 $(SRC)/S1_normalizer.py $(ARTIFACTS)/00_raw_extract.json

s2:
	python3 $(SRC)/S2_preflight.py $(ARTIFACTS)/01_normalized.json

s3:
	python3 $(SRC)/S3_llm_chunker.py $(ARTIFACTS)/01_normalized.json

pipeline: s0 s1 s2 s3

.PHONY: s0 s1 s2 s3 pipeline
