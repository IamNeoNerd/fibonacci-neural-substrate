import gradio as gr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_data(days=30):
    """Generates mock telemetry to demonstrate Fibonacci compression."""
    start_time = datetime.now() - timedelta(days=days)
    data = []
    current_time = start_time
    while current_time < datetime.now():
        # Simulate CPU spikes and heartbeat lag
        cpu = 20 + 60 * np.sin(current_time.timestamp() / 3600) + np.random.normal(0, 5)
        lag = 0.1 if cpu < 90 else np.random.uniform(0.1, 35) # Pulse lag on high CPU
        data.append({"ts": current_time, "cpu": max(0, min(100, cpu)), "lag": lag})
        current_time += timedelta(seconds=5)
    return pd.DataFrame(data)

def compress_fibonacci(df, level=1):
    """
    Simulates the CHITTA Fibonacci Compression.
    Level 1: 3-hour windows (F4)
    Level 2: 13-hour windows (F7)
    """
    window_size = "3H" if level == 1 else "13H"
    compressed = df.resample(window_size, on='ts').agg({
        'cpu': ['first', 'max', 'min', 'last', 'mean'],
        'lag': 'max'
    })
    compressed.columns = ['open', 'high', 'low', 'close', 'avg', 'peak_lag']
    return compressed.reset_index()

def explorer_ui(level_input):
    df = generate_mock_data(days=30)
    compressed = compress_fibonacci(df, level=int(level_input))
    
    info = f"### CHITTA Matrix Insight (Level {level_input})\n"
    info += f"- **Original Samples:** {len(df):,}\n"
    info += f"- **Compressed Nodes:** {len(compressed):,}\n"
    info += f"- **Compression Ratio:** {len(df)/len(compressed):.2f}:1\n"
    
    return info, compressed.head(20)

with gr.Blocks(title="CHITTA Explorer") as demo:
    gr.Markdown("# 🕉️ CHITTA Explorer")
    gr.Markdown("### Visualize the Fibonacci Neural Substrate's Cognitive Memory")
    
    with gr.Row():
        level = gr.Radio(choices=["1", "2"], label="Compression Level (Kalp)", value="1")
        btn = gr.Button("Analyze Substrate")
    
    output_text = gr.Markdown()
    output_df = gr.DataFrame()
    
    btn.click(fn=explorer_ui, inputs=level, outputs=[output_text, output_df])
    
    gr.Markdown("---")
    gr.Markdown("Explore the full paper at: [GitHub: iamneonerd/chitta-fns](https://github.com/IamNeoNerd/fibonacci-neural-substrate)")

if __name__ == "__main__":
    demo.launch()
