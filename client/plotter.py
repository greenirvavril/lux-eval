import matplotlib.pyplot as plt
import numpy as np

cmap = plt.get_cmap("Set2")
def bar_plot(dic: dict, output_path: str):
    """
    dic = {
        'chatgpt': {'bleurt20 ↑': 75.6, 'bertscore ↑': 92.8, 'bleu ↑': 32.6, 'chrF2 ↑': 52.3, 'TER ↓': 55.0},
        'deepl': {...},
        ...
    }
    """
    models = list(dic.keys())
    # Take metric names from the first model
    metrics = list(next(iter(dic.values())).keys())

    # Build scores dict {metric: [values per model]}
    scores = {metric: [dic[model][metric] for model in models] for metric in metrics}

    num_models = len(models)
    num_metrics = len(metrics)

    bar_width = 0.15  # adjust as needed
    bar_positions = np.arange(num_metrics) * (bar_width * (num_models + 1))

    plt.figure(figsize=(12, 6))
    for i, model in enumerate(models):
        plt.bar(
            [pos + i * bar_width for pos in bar_positions],
            [scores[metric][i] for metric in metrics],
            width=bar_width,
            color=cmap(i),
            label=model
        )

    # Labels and formatting
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xlabel('Metric')
    plt.ylabel('Score')
    plt.title('Model Performance Comparison')
    plt.xticks(bar_positions + bar_width * (num_models - 1) / 2, metrics, rotation=30, ha="right")
    plt.legend()

    # Save and show
    plt.savefig(output_path, bbox_inches="tight")
    #plt.show()

def radar_plot(dic: dict, output_path: str):
    """
    dic = {
        'chatgpt': {'bleurt20 ↑': 75.6, 'bertscore ↑': 92.8, 'bleu ↑': 32.6, 'chrF2 ↑': 52.3, 'TER ↓': 55.0},
        'deepl': {...},
        ...
    }
    """
    models = list(dic.keys())
    # Extract metric names from the first model
    metrics = list(next(iter(dic.values())).keys())
    num_metrics = len(metrics)

    # Compute angle of each axis
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    # Dynamic figure width based on number of metrics
    base_width = 6
    additional_width_per_metric = 0.5
    fig_width = base_width + additional_width_per_metric * num_metrics
    fig_height = 6

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), subplot_kw=dict(polar=True))

    # Plot each model
    for i, model in enumerate(models):
        values = [dic[model][metric] for metric in metrics]
        values += values[:1]  # close the loop
        color = cmap(i)
        ax.fill(angles, values, alpha=0.25, color=color)
        ax.plot(angles, values, label=model, color=color)
        ax.scatter(angles, values, color=color, zorder=5)

    # Set the labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)

    # Add legend
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

    # Add title
    plt.title('Model Performance Radar Chart')

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    #plt.show()

def lm_metric_scatter_plot(dic: dict, metric: str, output_path: str):

    title = f"Model Scores - {metric}"

    # Define a colormap to dynamically assign colors
    models = list(dic.keys())
    scores = {}
    for model in models:
        scores[model] = dic[model][metric]["segment_scores"]

    # Calculate the number of data points
    num_range = len(scores[models[0]]) if models else 0

    # Dynamically calculate figure size
    base_width = 8  # Base width for the plot
    additional_width_per_model = 0.5  # Additional width per model
    fig_width = base_width + additional_width_per_model * len(models)
    fig_height = 6  # Fixed height for the plot

    # Create a figure and axis with dynamic width
    plt.figure(figsize=(fig_width, fig_height))

    # Plot each model's scores
    for i, (model, model_scores) in enumerate(scores.items()):
        plt.scatter(range(1, num_range + 1), model_scores, color=cmap(i), label=model, alpha=0.6)

    # Add labels and title
    plt.xlabel('Segments')
    plt.ylabel('Score')
    plt.title(title)
    plt.legend(title='System', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Add grid for better readability
    plt.grid(True)

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    #plt.show()