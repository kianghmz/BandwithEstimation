import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

df = pd.read_excel("receiver_log.xlsx", sheet_name="All Data with Theories")
summary_df = pd.read_excel("receiver_log.xlsx", sheet_name="Summary by Group")

output_folder = os.path.expanduser("~/Desktop/pathkatana_group_plots")
os.makedirs(output_folder, exist_ok=True)

bandwidths = [200, 400, 600, 800, 1000, 1200]

for group_id in df['group_id'].unique():
    df_group = df[df['group_id'] == group_id].sort_values("packet_size")
    ref_row = df_group[df_group['is_reference']].iloc[0]
    ref_size = ref_row['packet_size']
    df_plot = df_group[df_group['packet_size'] > ref_size]

    best_b = int(summary_df[summary_df['group_id'] == group_id]['Best_Bandwidth_Mbps'].mode().iloc[0])
    best_mae = summary_df[summary_df['group_id'] == group_id]['MAE_ms'].iloc[0]
    best_mse = summary_df[summary_df['group_id'] == group_id]['MSE_ms'].iloc[0]
    best_sd = summary_df[summary_df['group_id'] == group_id]['SD_ms'].iloc[0]
    best_col = f"Delay_{best_b}Mbps"

    x = df_plot['packet_size']
    y = df_plot['absolute_delay_ms']

    dy = np.gradient(y, x)
    congestion_index = np.argmax(dy)
    congestion_point = x.iloc[congestion_index]

    plt.figure(figsize=(10, 6))
    x_smooth = np.linspace(x.min(), x.max(), 300)
    y_smooth = np.interp(x_smooth, x, y)
    plt.plot(x_smooth, y_smooth, label=f"Group {group_id} Smoothed", linestyle="--", linewidth=2)
    plt.scatter(x, y, color='purple', label="Measured Delay", marker='x', zorder=5)

    for b in bandwidths:
        col = f"Delay_{b}Mbps"
        if col in df_plot.columns:
            plt.plot(x, df_plot[col], linestyle=":", label=f"Theory {b} Mbps")

    plt.axvline(x=congestion_point, color='red', linestyle='--', linewidth=2, label="Start of Congestion")
    plt.title(f"Group {group_id} | Best Bandwidth = {best_b} Mbps | MAE = {best_mae:.4f} ms | "
              f"MSE = {best_mse:.4f} | SD = {best_sd:.4f}")
    plt.xlabel("Packet Size (Bytes)")
    plt.ylabel("Delay (ms)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    filename = f"group_{group_id}_smoothed_plot.png"
    plt.savefig(os.path.join(output_folder, filename))
    plt.close()

print(f"All plots saved to: {output_folder}")
