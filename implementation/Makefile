.PHONY: segment package validate stamp verify verify-local tamper test-tamper clean-generated

PACKAGE=data/packages/camera-001-20260615T210000Z

segment:
	python3 src/segmenter/segment_video.py

package:
	python3 src/packager/create_package.py

validate:
	python3 src/gateway/validate_package.py

stamp:
	python3 src/anchor/stamp_manifest.py

verify:
	python3 src/verifier/verify_package.py

verify-local:
	python3 src/verifier/verify_package.py --skip-ots

tamper:
	bash scripts/make_tampered_cases.sh $(PACKAGE)

test-tamper: tamper
	! python3 src/verifier/verify_package.py --package data/tampered/case-01-segment-bytes-modified --skip-ots --report reports/case-01-segment-bytes-modified_report.json
	! python3 src/verifier/verify_package.py --package data/tampered/case-02-segment-removed --skip-ots --report reports/case-02-segment-removed_report.json
	! python3 src/verifier/verify_package.py --package data/tampered/case-03-manifest-modified --skip-ots --report reports/case-03-manifest-modified_report.json
	! python3 src/verifier/verify_package.py --package data/tampered/case-04-segment-reordered-in-manifest --skip-ots --report reports/case-04-segment-reordered-in-manifest_report.json

clean-generated:
	rm -rf data/segments/* data/packages/* data/tampered/* reports/*
	touch data/segments/.gitkeep data/packages/.gitkeep data/tampered/.gitkeep reports/.gitkeep
