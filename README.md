# Lux-Eval

**Lux-Eval** is a local evaluation suite for Luxembourgish machine translation (MT), inspired by [MATEO](https://mateo.ivdnt.org/) (Vanroy et al., 2023).  
It provides an easy-to-use client and a Flask-based API for computing a range of MT evaluation metrics, either locally or via a server.

---

## Table of Contents
- [Features](#features)  
- [Installation](#installation)  
- [Getting Started](#getting-started)  
  - [1. Launch the Gateway](#1-launch-the-gateway)  
  - [2. Configure the Client](#2-configure-the-client)  
  - [3. Launch the Client](#3-launch-the-client)  
  - [Notes](#notes)  
- [Input Format](#input-format)  
- [Metrics](#metrics)  
  - [Reference-based](#reference-based)  
  - [Quality Estimation](#quality-estimation)  
- [Score Interpretation](#score-interpretation)  
  - [Recommendations](#recommendations)  
- [References](#references)  

---

## Features
- Evaluate Luxembourgish (lb) → target-language (tgt) MT output (e.g., fr, en, de, pt)  
- Support for multiple complementary evaluation metrics  
- System- and segment-level scoring
- Visual plots for performance insights
- Performs paired bootstrap resampling to test statistical significance
- Score interpretation aid  
- Modular architecture for adding new metrics  

---

## Installation: Client
Install the client on your local machine:

```bash
# Clone the Lux-Eval repository
git clone https://github.com/greenirvavril/lux-eval.git

# Navigate into the project directory
cd lux-eval

# Make the setup script executable
chmod +x setup_client.sh

# Run the setup script
./setup_client.sh
````

## Installation: Gateway
Install the gateway either on your local machine or on your server:

```bash
# Make the setup script executable
chmod +x setup_gateway.sh

# Run the setup script
./setup_gateway.sh
````

Note: To use [xCOMET-XL](https://huggingface.co/Unbabel/XCOMET-XL), you may have to acknowledge its license on Hugging Face Hub and [log-in into hugging face hub](https://huggingface.co/docs/huggingface_hub/quick-start).

---

## Getting Started

The client requires the **gateway's IP address** to connect. Follow these steps to get started.

### 1. Launch the Gateway

```bash
cd gateway
source main_venv/bin/activate
python main_gateway.py
```

Let it run until the output shows:

```
Gateway is running!
  - Local access (same machine): http://127.0.0.1:5000
  - Network access (other machines should use this IP): http://192.168.X.X:5000
```

* Use the **local access URL** if the gateway is running on the same machine as the client.
* Use the **network access URL** if the gateway is running on another machine on the same network.

---

### 2. Configure the Client

1. Copy the appropriate IP address from the gateway output.
2. Navigate to the client folder:

```bash
cd client
```

3. Open `client.py` and locate:

```python
URL = ""  # <-- enter your gateway IP, e.g.: "http://192.168.X.X:5000"
```

4. Paste the IP address and configure the metrics you want to use (`True` or `False`).
5. Save the file.

---

### 3. Launch the Client

In a new terminal:

```bash
cd client  # adjust path if necessary
source client_venv/bin/activate
python client.py
```

The client will connect to the gateway and start evaluating metrics as configured.

---

### Notes

* Ensure that **port 5000** is open on the gateway machine if running on a network.
* The gateway must be running before starting the client.
* For testing on the same machine, you can always use `http://127.0.0.1:5000`.

---

## Input Format

* **Candidate file(s):** MT model outputs (one file per system)
* **Source file:** original sentences (aligned with candidates)
* **Reference file:** gold-standard translations (used by reference-based metrics)

> All files must be plain `.txt`, aligned line-by-line (same number of lines, one segment per line).

---

## Metrics

### Reference-based

| Metric                                                    | Description                                       | Reference                         |
| --------------------------------------------------------- | ------------------------------------------------- | --------------------------------- |
| [BERTScore](https://github.com/Tiiiger/bert_score)        | Contextualised embeddings for semantic similarity | Zhang et al., 2019                |
| [BLEURT20](https://huggingface.co/lucadiliello/BLEURT-20) | Trained on human preference data                  | Sellam et al., 2020               |
| [xCOMET-XL](https://huggingface.co/Unbabel/XCOMET-XL)     | Trained on human preference data                  | Guerreiro et al., 2024            |
| [BLEU](https://github.com/mjpost/sacrebleu)               | N-gram overlap                                    | Papineni et al., 2002; Post, 2018 |
| [ChrF2](https://github.com/mjpost/sacrebleu)              | Character-level overlap                           | Popović, 2016; Post, 2018         |
| [TER](https://github.com/mjpost/sacrebleu)                | Edit distance to reference                        | Snover et al., 2006; Post, 2018   |

**Note:** BERTScore uses [xlm-roberta-large](https://huggingface.co/FacebookAI/xlm-roberta-large), except for English it uses [deberta-xlarge-mnli](https://huggingface.co/microsoft/deberta-xlarge-mnli) for English.

### Quality Estimation

| Metric                                                 | Description                                       | Reference                         |
| ------------------------------------------------------ | ------------------------------------------------- | --------------------------------- |
| [LuxEmbedder](https://github.com/fredxlpy/LuxEmbedder) | Luxembourgish sentence embeddings                 | Philippy et al., 2024             |

---

## Score Interpretation

* Results are exported to `.xlsx`, including an **accuracy matrix** with metric scores converted to probability percentages (cf. Kocmi et al., 2024).
* Matrix interpretation: similar to a correlation matrix; shows likelihood of one system outperforming another.
* **Note:** Luxembedder is excluded from the accuracy matrix due to conversion tool limitations.

### Recommendations

* For unrelated models: prioritise **BERTScore**, **BLEURT20**, and **xCOMET-XL**.
* Surface-overlap metrics (BLEU, ChrF2, TER) are limited and not recommended for cross-system comparison.
* Percentages in **accuracy matrix** do not add up due to conversion tool limitations. Prioritise positive scores (likelihood of model A being better than model B) over negative scores (likelihood of model B being worse than model A).
* **LuxEmbedder**: promising but unverified; scores min-max-normalised (0.8–1.0 to 0-100 range); can also be used for src -> lb.

---

## References
* Guerreiro, N. M., Rei, R., Stigt, D. V., Coheur, L., Colombo, P., & Martins, A. F. (2024). xcomet: Transparent machine translation evaluation through fine-grained error detection. Transactions of the Association for Computational Linguistics, 12, 979-995.
* Kocmi, T., Zouhar, V., Federmann, C., & Post, M. (2024). Navigating the metrics maze: Reconciling score magnitudes and accuracies. arXiv preprint arXiv:2401.06760.
* Papineni, K., Roukos, S., Ward, T., & Zhu, W. J. (2002, July). Bleu: a method for automatic evaluation of machine translation. In Proceedings of the 40th annual meeting of the Association for Computational Linguistics (pp. 311-318).
* Philippy, F., Guo, S., Klein, J., & Bissyandé, T. F. (2024). LuxEmbedder: A cross-lingual approach to enhanced Luxembourgish sentence embeddings. arXiv preprint arXiv:2412.03331.
* Popović, M. (2016, August). chrF deconstructed: beta parameters and n-gram weights. In Proceedings of the First Conference on Machine Translation: Volume 2, Shared Task Papers (pp. 499-504).
* Post, M. (2018). A call for clarity in reporting BLEU scores. arXiv preprint arXiv:1804.08771.
* Sellam, T., Das, D., & Parikh, A. P. (2020). BLEURT: Learning robust metrics for text generation. arXiv preprint arXiv:2004.04696.
* Snover, M., Dorr, B., Schwartz, R., Micciulla, L., & Makhoul, J. (2006). A study of translation edit rate with targeted human annotation. In Proceedings of the 7th Conference of the Association for Machine Translation in the Americas: Technical Papers (pp. 223-231).
* Vanroy, B., Tezcan, A., & Macken, L. (2023). MATEO: MAchine Translation Evaluation Online. In M. Nurminen, J. Brenner, M. Koponen, S. Latomaa, M. Mikhailov, F. Schierl, … H. Moniz (Eds.), Proceedings of the 24th Annual Conference of the European Association for Machine Translation (pp. 499–500). Tampere, Finland: European Association for Machine Translation (EAMT).
* Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., & Artzi, Y. (2019). Bertscore: Evaluating text generation with bert. arXiv preprint arXiv:1904.09675.
