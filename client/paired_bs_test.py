from argparse import Namespace
from collections import defaultdict
import numpy as np
import os
from sacrebleu.metrics.base import Metric as SbMetric
from sacrebleu.significance import PairedTest, Result, _compute_p_value, estimate_ci
from typing import Dict, List, Tuple


def paired_bs(
    metric_sentence_scores: Dict[str, List[List[float]]],
    paired_bs_n: int = 1000,
):
    """
    :param metric_sentence_scores: a dictionary of metric_name to a list of list of sentence-level scores
    where each item corresponds to the results of one system
    :param paired_bs_n: how many partitions to use in bootstrap sampling
    :return: a dictionary with keys metrics and as values a list of dicts, where each dict
    contains the results for a system
    """
    # This seed is also used in sacrebleu
    seed = int(os.environ.get("SACREBLEU_SEED", "12345"))
    rng = np.random.default_rng(seed)
    dataset_size = len(next(iter(metric_sentence_scores.values()))[0])
    idxs = rng.choice(dataset_size, size=(paired_bs_n, dataset_size), replace=True)

    results = defaultdict(list)
    for metric_name, all_sys_scores in metric_sentence_scores.items():
        all_sys_scores = np.array(all_sys_scores)
        scores_bl, all_sys_scores = all_sys_scores[0], all_sys_scores[1:]
        # Baseline
        real_mean_bl = scores_bl.mean().item()
        # First create (n_samples, dataset_size) array that contains n_samples partitions
        # of 'dataset_size' items, randomly picked.
        # Then calculate corpus scores, which here are the average over the dataset_size,
        # so we end up with an array of (n_samples,)
        bs_scores_bl = scores_bl[idxs].mean(axis=1)
        bs_bl_mean, bl_ci = estimate_ci(bs_scores_bl)

        results[metric_name].append(Result(score=real_mean_bl, p_value=None, mean=bs_bl_mean, ci=bl_ci))

        for scores_sys in all_sys_scores:
            # The real, final score for this metric (average of all sentence scores)
            real_mean_sys = scores_sys.mean().item()
            # The remainder is borrowed and slightly adapted from sacrebleu
            diff = abs(real_mean_bl - real_mean_sys)
            # size (n_samples,)
            bs_sys_scores = scores_sys[idxs].mean(axis=1)

            # 1. bs_mean_sys: the "true" mean score estimated from bootstrap resamples of the system
            # 2. sys_ci: the 95% confidence interval around the true mean score `bs_mean_sys`
            bs_mean_sys, sys_ci = estimate_ci(bs_sys_scores)
            sample_diffs = np.abs(bs_sys_scores - bs_scores_bl)
            stats = sample_diffs - sample_diffs.mean()
            p = _compute_p_value(stats, diff)
            results[metric_name].append(Result(score=real_mean_sys, p_value=p, mean=bs_mean_sys, ci=sys_ci))

    return dict(results)

def paired_bs_sacrebleu(
    named_systems: List[Tuple[str, List[str]]], metrics: Dict[str, SbMetric], references: List[str], args: Namespace
):
    """
    :param named_systems: A lisf of (system_name, system_hypotheses) tuples on
    which the test will be applied.
    :param metrics: A dictionary of `Metric` instances that will be computed
    for each system.
    :param references: A sequence of reference documents with document being
    defined as a sequence of reference strings. If `None`, already cached references
    will be used through each metric's internal cache.
    :return:
    """
    res = PairedTest(
        named_systems=named_systems,
        metrics=metrics,
        n_samples=1000,
        references=[references],
        test_type="bs",
    )

    signatures, results = res()
    signatures = {k: v.format(args.short) for k, v in signatures.items()}

    return results, signatures