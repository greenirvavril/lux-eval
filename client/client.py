import accuracy_matrice as am
from argparse import Namespace
import helpers as h
import metrics as m
import os
import paired_bs_test as pbt
import pandas as pd
import plotter
from sacrebleu.metrics import BLEU, CHRF, TER
import sys

def luxeval(sacrebleu: bool, 
              bleurt20: bool, 
              comet: bool,
              bertscore: bool, 
              luxembedder: bool, 
              ip_url: str):

    quality_estimation_metrics = {
        "luxembedder": luxembedder,
    }
    reference_based_metrics = {
        "bertscore": bertscore,
        "bleurt20": bleurt20,
        "xcometxl": comet,
        "sacrebleu": sacrebleu,
    }
    
    metric_flags = {**quality_estimation_metrics, **reference_based_metrics}

    # Prepping dict with individual routes for the flask calls
    url_dict = {}
    ip_url = ip_url.strip("/")
    for metric, enabled in metric_flags.items():
        if enabled:
            url_dict[metric] = f"{ip_url}/{metric}"

    # ========================
    # 1. Ask for language code
    # ========================
    while True:
        lang_code = input("Enter target language code (e.g., en, de, fr, pt): ").strip().lower()
        if not lang_code:
            print("Language code cannot be empty. Please enter a valid code.")
            continue
        if len(lang_code) != 2:
            print("Language code should be 2 letters (ISO 639-1). Please try again.")
            continue
        bertscore_langs = {"en", "de", "fr", "es", "zh", "ja", "ru", "pt"}
        if bertscore and lang_code not in bertscore_langs:
            print(f"Warning: '{lang_code}' may not be supported by BERTScore.")
            continue
        break

    # ===================================
    # 2. Ask for number of models to load
    # ===================================
    while True:
        try:
            num_models = int(input("Enter the number of models you want to compare: ").strip())
            if num_models < 1:
                print("You must compare at least one model.")
                continue
            break
        except ValueError:
            print("Please enter a valid integer.")

    # ===================================
    # 3. Ask for source file
    # ===================================
    sr_dict = {}
    has_source = None
    while has_source not in {"y", "n"}:
        has_source = input("Do you have a source file? (y/n): ").strip().lower()

    source_path = None
    if has_source == "y":
        while True:
            source_path = os.path.normpath(input("Drag and drop source file and press ENTER: ").strip().strip("'").strip('"'))
            if os.path.exists(source_path):
                sr_dict["source_path"] = source_path
                break
            print(f"Source file {source_path} does not exist. Please try again.")
    else:  # user said "n"
        if any(quality_estimation_metrics.values()):
            print("Must provide source file for quality estimation metrics (e.g., luxembedder). Exiting.")
            sys.exit(1)

    # ===================================
    # 4. Ask for reference file
    # ===================================
    has_reference = None
    while has_reference not in {"y", "n"}:
        has_reference = input("Do you have a reference file? (y/n): ").strip().lower()

    reference_path = None
    if has_reference == "y":
        while True:
            reference_path = os.path.normpath(input("Drag and drop reference file and press ENTER: ").strip().strip("'").strip('"'))
            if os.path.exists(reference_path):
                sr_dict["reference_path"] = reference_path
                break
            print(f"Reference file {reference_path} does not exist. Please try again.")
    else:  # user said "n"
        if any(reference_based_metrics.values()):
            print("Must provide reference file for reference-based metrics (e.g., BERTScore, SacreBLEU, BLEURT20). Exiting.")
            sys.exit(1)

    # ===================================
    # 5. Ask for model files
    # ===================================
    m_dict = {}
    for i in range(num_models):
        while True:
            if i == 0:
                print("NOTE: the first model you enter will serve as baseline.")
            m_path = os.path.normpath(input(f"Drag and drop model file {i + 1} and press ENTER: ").strip().strip("'").strip('"'))
            if os.path.exists(m_path):
                m_name = os.path.splitext(os.path.basename(m_path))[0]
                m_dict[m_name] = {"file_path": m_path}
                break
            print(f"{m_path} does not exist, please enter a valid file path.")

    print("All inputs successfully collected.")

    named_systems = []
    paired_bs_input = {name: [] for name, enabled in metric_flags.items() if enabled and name != "sacrebleu"}

    # Scoring loop
    for model in m_dict:
        candidate_path = m_dict[model]["file_path"]

        for metric_name, enabled in metric_flags.items():
            if not enabled:
                continue

            files = {"candidate": candidate_path}
            if has_reference:
                files["reference"] = reference_path
            if has_source:
                files["source"] = source_path
            scores = m.score_metric(url_dict[metric_name], model, files, metric_name, language=lang_code)
            m_dict[model][metric_name] = scores

            if metric_name != "sacrebleu":  # only those have segment_scores
                paired_bs_input[metric_name].append(scores["segment_scores"])

        with open(m_dict[model]["file_path"], "r") as file:
            model_lines = [line.strip("\n") for line in file.readlines()]
        named_systems.append((model, model_lines))

    # Paired bootstrap tests
    significance_dict = pbt.paired_bs(paired_bs_input)
    if has_reference == "y":
        with open(reference_path, "r") as file:
            reference_lines = [line.strip("\n") for line in file.readlines()]

    if sacrebleu:
        sacrebleu_dict = {"BLEU": BLEU(), "chrF2": CHRF(), "TER": TER()}
        args = Namespace(short=False)
        results, _ = pbt.paired_bs_sacrebleu(named_systems, sacrebleu_dict, reference_lines, args)
    else:
        results = {}

    model_names = list(m_dict.keys())
    data = {"system": model_names}

    for metric, value in significance_dict.items():
        data[f"{metric} (μ ± 95% CI)"] = [h.format_score(*vals) for vals in h.extract_values(value)]

    for metric, value in results.items():
        if metric == "System":
            continue
        data[f"{metric} (μ ± 95% CI)"] = [h.format_score(*vals) for vals in h.extract_values(value)]

    df = pd.DataFrame(data)

    if not df.empty:
        df.loc[0, 'system'] = f"Baseline: {df.loc[0, 'system']}"

    if sacrebleu:
        df = df.style.apply(h.highlight_max, subset=df.columns[1:-1]).apply(h.highlight_min, subset=['TER (μ ± 95% CI)'])
    else:
        df = df.style.apply(h.highlight_max)

    if has_source == "y":
        with open(source_path, "r") as file:
            source_lines = [line.strip() for line in file.readlines()]

    # Prepare metric DataFrames for Excel export
    df_dict = {}
    for metric_name, enabled in metric_flags.items():
        if enabled and metric_name != "sacrebleu":
            metric_data = {}

            # Always include source/reference if they exist
            if "source_path" in sr_dict and os.path.exists(sr_dict["source_path"]):
                with open(sr_dict["source_path"], "r") as f:
                    source_lines = [line.strip() for line in f.readlines()]
                metric_data["source"] = source_lines

            if "reference_path" in sr_dict and os.path.exists(sr_dict["reference_path"]):
                with open(sr_dict["reference_path"], "r") as f:
                    reference_lines = [line.strip() for line in f.readlines()]
                metric_data["reference"] = reference_lines

            # Add candidate lines and scores for each model
            for model_name in model_names:
                candidate_path = m_dict[model_name]["file_path"]
                with open(candidate_path, "r") as f:
                    model_lines = [line.strip() for line in f.readlines()]
                metric_data[model_name + "_lines"] = model_lines
                metric_data[model_name + "_score"] = m_dict[model_name][metric_name]["segment_scores"]

            df_dict[metric_name] = pd.DataFrame(metric_data)

    # Create results folder
    folder_name = "results"
    folder_counter = 0
    directory = os.path.dirname(list(sr_dict.values())[0])  # base folder from first file
    folder_path = os.path.join(directory, folder_name)
    while os.path.exists(folder_path):
        folder_counter += 1
        folder_path = os.path.join(directory, f"{folder_name}_{folder_counter}")
    os.makedirs(folder_path)

    # Export all data to Excel
    excel_path = os.path.join(folder_path, f"results_{folder_counter}.xlsx")
    formatted_matrice_input = am.format_accuracy_matrix_data(m_dict)

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        # Main CI table
        df.to_excel(writer, sheet_name='ci', index=False)
        # Individual metric sheets
        for metric_name, metric_df in df_dict.items():
            metric_df.to_excel(writer, sheet_name=metric_name, index=False)
        # Accuracy matrix
        am.accuracy_matrix(formatted_matrice_input, writer, sheet_name="accuracy_matrice")

    print(f"Excel file saved: {excel_path}")


    combined_dict = {}
    for model_name in m_dict:
        model_scores = {}
        for metric_name, enabled in metric_flags.items():
            if enabled and metric_name != "sacrebleu":
                _, metric_sys_score = m_dict[model_name][metric_name].values()
                model_scores[metric_name + " ↑"] = metric_sys_score
        combined_dict[model_name] = model_scores

        if sacrebleu:
            model_bleuscores = m_dict[model_name]["sacrebleu"]
            combined_dict[model_name]["bleu ↑"] = model_bleuscores["bleu"]
            combined_dict[model_name]["chrF2 ↑"] = model_bleuscores["chrF2"]
            combined_dict[model_name]["TER ↓"] = model_bleuscores["TER"]

    plotter.bar_plot(combined_dict, os.path.join(folder_path, "bar_plot.png"))
    plotter.radar_plot(combined_dict, os.path.join(folder_path, "radar_plot.png"))

    for metric_name, enabled in metric_flags.items():
        if enabled and metric_name != "sacrebleu":
            plotter.lm_metric_scatter_plot(m_dict, metric_name, os.path.join(folder_path, f"{metric_name}_scatter_plot.png"))

##########################################

URL = "" # <-- enter your ip, e.g.,: "http://##.####.#.##:####"

# example call
luxeval(sacrebleu=True,
          bleurt20=True,
          comet=True,
          bertscore=True,
          luxembedder=True,
          ip_url=URL)
