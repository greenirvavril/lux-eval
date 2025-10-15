import mt_thresholds
import pandas as pd

_thresholds_raw = {
    "bleu": [
        88.33333333333225,
        0.9663926931178954
    ],
    "chrf": [
        92.999999999972,
        1.1142732157139852
    ],
    "spBLEU101": [
        84.58445492823891,
        1.262507595109315
    ],
    "spBLEU200": [
        90.99999999998793,
        0.8079046528617078
    ],
    "bleurt-default": [
        94.66666666666666,
        0.4947232832741672
    ],
    "bleurt20": [
        98.33333333332963,
        1.3727206190931929
    ],
    "comet20": [
        97.33333333332897,
        0.7266990738678005
    ],
    "comet22": [
        96.22374133884283,
        2.8359194570556636
    ],
    "comet21qe": [
        93.7997435048193,
        43.38413992717536
    ],
    "cometkiwi22": [
        98.88141616584615,
        2.719280643871758
    ],
    "xcometXXL": [
        98.93432477039522,
        1.1629533711748128
    ],
    "xcometxl": [
        96.56738237041118,
        1.4535595865214588
    ],
    "cometkiwiXXL": [
        96.23167242471065,
        1.2826577343149304
    ],
    "bertscore": [
        94.99999999999999,
        2.6823162097239917
    ],
    "cometkiwi23-xl-src": [
        96.39080593943235,
        1.8888877927713834
    ],
    "metricx-23-large": [
        93.60777624544488,
        26.277850179370947
    ],
    "metricx-23-qe-large": [
        97.99999999782683,
        15.541455989240491
    ],
}

metrics_list = list(_thresholds_raw.keys())

def format_accuracy_matrix_data(dic: dict):

    model_names = list(dic.keys())

    metric_names = list(dic[model_names[0]].keys())
    metric_names.pop(0)

    if "sacrebleu" in metric_names:
        metric_names.remove("sacrebleu")
        metric_names.append("bleu")
        metric_names.append("chrf")
        sacrebleu = True

    metric_names = [m for m in metric_names if m in metrics_list] # removing any metric that is not in the metrics_list.

    metric_dict = {}

    for metric_name in metric_names:
            metric_dict[metric_name] = []

    for metric_name in metric_names:
        for model in model_names:
            if metric_name == "bleu":
                metric_dict[metric_name].append(dic[model]["sacrebleu"][metric_name])
            elif metric_name == "chrf":
                metric_dict[metric_name].append(dic[model]["sacrebleu"]["chrF2"])
            else:
                metric_dict[metric_name].append(dic[model][metric_name]["system_score"])

    llm_scores = pd.DataFrame(metric_dict, index=model_names)

    return llm_scores

def accuracy_matrix(df, writer, sheet_name="accuracy_matrix"):
    def shade_from_prob(prob: float):
        """Return RGB color based on probability thresholds (discrete bins)."""
        if prob > 0.99:        # Virtually certain
            return 35, 177, 80       # Dark green
        elif prob > 0.90:      # Very likely
            return 101, 255, 0     # Bright green
        elif prob > 0.66:      # Likely
            return 196, 240, 0      # Light green
        elif prob >= 0.33:     # About as likely as not
            return 250, 255, 4    # yellow
        elif prob < 0.01:      # Exceptionally unlikely
            return 245, 0, 0        # red
        elif prob < 0.10:      # Very unlikely
            return 248, 151, 54        # orange
        else:                  # Unlikely (< 33%)
            return 249, 211, 2    # yellowish-orange

    # Use provided writer, do not create a new file
    workbook  = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet
    worksheet.set_column(0, len(df) * len(df.columns), 20)

    # Legend with shaded text cells
    legend_text = [
        ("Virtually certain: > 99%", 1.0),
        ("Very likely: > 90%", 0.95),
        ("Likely: > 66%", 0.75),
        ("About as likely as not: 33% – 66%", 0.5),
        ("Unlikely: < 33%", 0.25),
        ("Very unlikely: < 10%", 0.05),
        ("Exceptionally unlikely: < 1%", 0.001),
    ]

    worksheet.write(0, 0, "Probability Legend:")
    for i, (text, prob) in enumerate(legend_text):
        r, g, b = shade_from_prob(prob)
        color = f'#{r:02x}{g:02x}{b:02x}'
        fmt = workbook.add_format({'bg_color': color, 'border': 1})
        worksheet.write(i + 1, 0, text, fmt)  # Shaded legend text in column A

    row_offset = len(legend_text) + 3  # Extra space after legend

    for metric_name in df.columns:
        worksheet.write(row_offset, 0, f"{metric_name} Difference Matrix")
        for i, row_llm in enumerate(df.index):
            worksheet.write(row_offset + i + 1, 0, row_llm)
            worksheet.write(row_offset, i + 1, row_llm)
        for i, row_llm in enumerate(df.index):
            for j, col_llm in enumerate(df.index):
                if row_llm == col_llm:
                    continue
                diff = df.loc[row_llm, metric_name] - df.loc[col_llm, metric_name]
                prob = mt_thresholds.accuracy(diff, metric_name) / 100
                r, g, b = shade_from_prob(prob)
                color = f'#{r:02x}{g:02x}{b:02x}'
                fmt = workbook.add_format({
                    'bg_color': color,
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1
                })
                display = f"{diff:.2f} ({int(prob*100)}%)"
                worksheet.write(row_offset + i + 1, j + 1, display, fmt)
        row_offset += len(df) + 3
    worksheet.freeze_panes(len(legend_text) + 3, 1)