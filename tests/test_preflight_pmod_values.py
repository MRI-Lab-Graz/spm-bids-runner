"""bidspm turns n/a in a parametric-modulator column into 1 without a warning (convertOnsetTsvToMat.m): a modelled trial
with n/a there silently gets a wrong value, so readiness stops the subject."""
import json
from pathlib import Path

from lib.preflight import run_preflight
from tests.preflight_support import make_trees

HDR = "onset\tduration\ttrial_type\tresponse_validity\thuman_rating\n"
GOOD = HDR + "1\t1\titem\tvalid\t3.5\n5\t1\titem\tinvalid\tn/a\n9\t1\trating\tn/a\tn/a\n"
VALID_NA = HDR + "1\t1\titem\tvalid\tn/a\n5\t1\titem\tvalid\t2\n9\t1\trating\tn/a\tn/a\n"
CHAIN = [{"Name": "Filter", "Input": "trial_type", "Query": "trial_type==item", "Output": "trial_item"},
         {"Name": "Filter", "Input": "trial_item", "Query": "response_validity==valid", "Output": "valid_item"}]
PMOD = [{"Name": "human_mod", "Conditions": ["valid_item.item"], "Values": ["human_rating"], "PolynomialExpansion": 2}]


def _model(tmp, instructions=CHAIN, pmods=PMOD):
    software = {"SPM": {"ParametricModulations": pmods}} if pmods else {}
    node = {"Level": "Run", "Name": "run_level", "GroupBy": ["run", "subject"],
            "Model": {"Type": "glm", "X": ["valid_item.item", 1], "HRF": {"Variables": ["valid_item.item"], "Model": "spm"},
                      "Software": software},
            "Transformations": {"Transformer": "bidspm", "Instructions": instructions}}
    path = Path(tmp) / "model.json"
    path.write_text(json.dumps({"Name": "m", "BIDSModelVersion": "1.0.0", "Input": {"task": ["x"]}, "Nodes": [node]}))
    return path


def _items(tmp, events_02, **kw):
    bids, fmriprep = make_trees(tmp, subjects=("01", "02"), events=GOOD)
    (bids / "sub-02" / "func" / "sub-02_task-x_events.tsv").write_text(events_02)
    report = run_preflight(bids, fmriprep, model_file=_model(tmp, **kw), tasks=["x"], space="MNI", validator="skip")
    return [c for c in report["checks"] if c["id"] == "pmod_value"], report


def test_na_on_a_modelled_trial_is_an_error_for_that_subject_only(tmp_path):
    items, report = _items(tmp_path, VALID_NA)
    assert report["verdict"] == "blocked"
    (item,) = items
    assert item["severity"] == "error" and item["subject"] == "02"
    assert "human_rating" in item["message"] and "sub-02_task-x_events.tsv" in item["message"] and "1 " in item["message"]
    assert "xclude the subject" in item["fix"]


def test_na_only_on_filtered_out_trials_passes(tmp_path):
    items, _ = _items(tmp_path, GOOD)
    assert items == []


def test_no_modulator_no_check(tmp_path):
    items, _ = _items(tmp_path, VALID_NA, pmods=None)
    assert items == []


def test_unevaluable_filter_is_skipped_not_guessed(tmp_path):
    ins = [{"Name": "Filter", "Input": "trial_type", "Query": "trial_type==item", "Output": "trial_item"},
           {"Name": "Filter", "Input": "trial_item", "Query": "human_rating >= 1", "Output": "valid_item"}]
    items, _ = _items(tmp_path, VALID_NA, instructions=ins)
    assert items == []
