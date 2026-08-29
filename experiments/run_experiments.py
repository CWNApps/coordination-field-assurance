#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, replace
from pathlib import Path

from cwn_coordination_assurance.fixtures import deployment
from cwn_coordination_assurance.integrity import sign_record, verify_record
from cwn_coordination_assurance.metrics import baseline_ce, evaluate_deployment, weighted_adjacency
from cwn_coordination_assurance.models import Deployment, Surface
from cwn_coordination_assurance.optimizer import best_single_intervention
from cwn_coordination_assurance.simulator import alert_precision, simulate_diffusion


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"


def mean(xs): return sum(xs) / len(xs) if xs else 0.0


def run() -> dict:
    results: dict[str, object] = {"seed": 20260828, "claim_level": "synthetic_falsification_only", "experiments": []}
    ex = results["experiments"]

    clique = evaluate_deployment(deployment(20, topology="clique"))
    split = evaluate_deployment(deployment(20, topology="disconnected"))
    ex.append({"id":"E01","name":"topology counterexample","baseline_same_inputs":baseline_ce(20,10,1,1),"clique_tcr":clique.temporal_reachability_ratio,"split_tcr":split.temporal_reachability_ratio,"finding":"baseline has no topology input"})

    n = 1200
    ex.append({"id":"E02","name":"broadcast accounting","naive_pair_write_units":n*(n-1)/2*10,"emitted_write_units":n*10,"overcount_factor":(n-1)/2,"finding":"pairings times per-agent writes double counts broadcast emission"})

    ephemeral = evaluate_deployment(deployment(8, stagger=True, persistence=0))
    durable = evaluate_deployment(deployment(8, stagger=True, persistence=20))
    ex.append({"id":"E03","name":"temporal overlap","ephemeral_tcr":ephemeral.temporal_reachability_ratio,"durable_tcr":durable.temporal_reachability_ratio})

    chain = evaluate_deployment(deployment(10, topology="chain"))
    ex.append({"id":"E04","name":"multi-surface composition","per_surface_agents":2,"max_baseline_ce":chain.baseline_ce_max,"temporal_reachability":chain.temporal_reachability_ratio,"finding":"max-per-surface misses causal paths across surfaces"})

    high_vis_d = deployment(10)
    s = high_vis_d.surfaces[0]
    low_vis_s = replace(s, read_visibility=.01)
    low_vis_d = replace(high_vis_d, surfaces=(low_vis_s,))
    ex.append({"id":"E05","name":"read visibility","baseline_high":evaluate_deployment(high_vis_d).baseline_ce_max,"baseline_low":evaluate_deployment(low_vis_d).baseline_ce_max,"capacity_high":evaluate_deployment(high_vis_d).information_capacity_upper_bound_bits,"capacity_low":evaluate_deployment(low_vis_d).information_capacity_upper_bound_bits})

    ex.append({"id":"E06","name":"entropy blindness","writes":1000,"constant_unique_symbols":1,"diverse_unique_symbols":1000,"finding":"write counts do not estimate information without symbol distribution"})

    ex.append({"id":"E07","name":"persistence sensitivity","ce_p1":baseline_ce(10,1,1,1),"ce_p10":baseline_ce(10,1,1,10),"ce_p100":baseline_ce(10,1,1,100),"finding":"unvalidated P directly controls score by orders of magnitude"})

    _, below_m = weighted_adjacency(deployment(30, topology="chain"))
    _, above_m = weighted_adjacency(deployment(30, topology="clique"))
    below=[]; above=[]
    for seed in range(200):
        below.append(max(simulate_diffusion(below_m,.15,.4,20,seed)))
        above.append(max(simulate_diffusion(above_m,.55,.05,20,seed)))
    ex.append({"id":"E08","name":"criticality phase behavior","below_mean_peak":mean(below),"above_mean_peak":mean(above),"runs":200,"finding":"topology and dynamics create threshold-like behavior absent from CE"})

    ex.append({"id":"E09","name":"single-intervention optimizer","result":best_single_intervention(deployment(20,topology="clique",persistence=10))})

    ex.append({"id":"E10","name":"base-rate precision","prevalence":.001,"tpr":1.0,"fpr":.052,"precision":alert_precision(.001,1,.052),"finding":"attractive sensitivity can still produce unusable alert precision"})

    rec={"deployment_id":"d0","metric_version":"CFA-0.2.0-research","root":"abc"}
    sig=sign_record(rec,b"development-test-key")
    ex.append({"id":"E11","name":"receipt tamper","valid":verify_record(rec,sig,b"development-test-key"),"tampered_valid":verify_record({**rec,"root":"evil"},sig,b"development-test-key")})

    d=deployment(12)
    low_rate=replace(d,surfaces=(replace(d.surfaces[0],writes_per_writer_hour=1),))
    ex.append({"id":"E12","name":"rate limiting","before":asdict(evaluate_deployment(d)),"after":asdict(evaluate_deployment(low_rate))})

    eph=replace(d,surfaces=(replace(d.surfaces[0],persistence_hours=0,persistence_class="ephemeral"),))
    dur=replace(d,surfaces=(replace(d.surfaces[0],persistence_hours=24,persistence_class="durable"),))
    ex.append({"id":"E13","name":"ephemerality","ephemeral_criticality":evaluate_deployment(eph).spectral_criticality_proxy,"durable_criticality":evaluate_deployment(dur).spectral_criticality_proxy})

    identity_alias_ce=baseline_ce(100,1,1,1); principal_ce=baseline_ce(10,1,1,1)
    ex.append({"id":"E14","name":"identity alias inflation","alias_ce":identity_alias_ce,"principal_ce":principal_ce,"factor":identity_alias_ce/principal_ce})

    rng=random.Random(20260828)
    coeff_rank_flips=0
    for _ in range(10000):
        p=rng.uniform(1,100)
        if baseline_ce(10,2,8,p) > baseline_ce(40,3,6,1): coeff_rank_flips += 1
    ex.append({"id":"E15","name":"coefficient uncertainty","draws":10000,"rank_flip_rate":coeff_rank_flips/10000,"finding":"ordinal ranking is unstable under plausible unvalidated persistence weights"})

    results["summary"]={"experiment_count":len(ex),"all_deterministic":True,"production_claim":False}
    return results


def main():
    parser=argparse.ArgumentParser(description="Run the deterministic experiment suite")
    parser.add_argument("--out-dir",type=Path,default=OUT,
                        help="artifact directory (default: results/); use a temp dir to avoid mutating the tree")
    out=parser.parse_args().out_dir
    out.mkdir(parents=True,exist_ok=True)
    result=run()
    (out/"experiments.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    lines=["# Deterministic Experiment Report","","> Synthetic falsification evidence only. This is not a reproduction of the 2026 incident and not production validation.",""]
    for e in result["experiments"]:
        lines += [f"## {e['id']} — {e['name']}","", "```json",json.dumps(e,indent=2,sort_keys=True),"```",""]
    (out/"experiments.md").write_text("\n".join(lines),encoding="utf-8",newline="\n")
    print(json.dumps(result["summary"],sort_keys=True))


if __name__ == "__main__": main()

