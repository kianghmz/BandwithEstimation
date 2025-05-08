import pandas as pd
import numpy as np

sender_df = pd.read_excel("sender_log.xlsx")
receiver_df = pd.read_excel("receiver_log.xlsx")

df = pd.merge(
    sender_df,
    receiver_df,
    on=["run_id", "group_id", "packet_id", "packet_size"],
    suffixes=('_send', '_recv')
)

summary = []
all_data = []

for run_id in df['run_id'].unique():
    for group_id in df[df['run_id'] == run_id]['group_id'].unique():
        group_df = df[(df['run_id'] == run_id) & (df['group_id'] == group_id)].copy()

        if len(group_df) < 6:
            print(f"Skipped run={run_id}, group={group_id} (insufficient data)")
            continue

        group_df = group_df.sort_values("packet_size")
        group_df['delay_ms'] = (group_df['receive_time_ns'] - group_df['send_time_ns_send']) / 1e6

        group_df = group_df[group_df['delay_ms'] >= 0]
        group_df = group_df[group_df['delay_ms'] < 1000]

        if len(group_df) < 6:
            print(f"Skipped run={run_id}, group={group_id} (invalid delays)")
            continue

        group_df['delay_ms_smooth'] = group_df['delay_ms'].rolling(window=3, center=True).mean().bfill().ffill()

        delay_diffs = group_df['delay_ms_smooth'].diff().fillna(0)
        threshold = delay_diffs.mean() + delay_diffs.std()
        ref_candidates = group_df[delay_diffs < threshold]
        ref_index = ref_candidates['delay_ms_smooth'].idxmin() if not ref_candidates.empty else group_df.index[0]
        ref_delay = group_df.loc[ref_index, 'delay_ms_smooth']
        ref_size = group_df.loc[ref_index, 'packet_size']

        group_df['is_reference'] = False
        group_df.at[ref_index, 'is_reference'] = True
        group_df['absolute_delay_ms'] = (group_df['delay_ms_smooth'] - ref_delay).clip(lower=0)

        best_B, min_mse, best_mae = None, float("inf"), None
        for B in range(200, 1201, 10):
            theory = [(s * 8 / 1e6 / B) - (ref_size * 8 / 1e6 / B) for s in group_df['packet_size']]
            col_name = f"Delay_{B}Mbps"
            group_df[col_name] = theory
            mse = np.mean((group_df['absolute_delay_ms'] - theory) ** 2)
            if mse < min_mse:
                min_mse, best_B = mse, B
                best_mae = np.mean(np.abs(group_df['absolute_delay_ms'] - theory))

        sd = np.std(group_df['absolute_delay_ms'] - group_df[f"Delay_{best_B}Mbps"])

        summary.append({
            "run_id": run_id,
            "group_id": group_id,
            "Best_Bandwidth_Mbps": best_B,
            "MSE_ms": round(min_mse, 4),
            "MAE_ms": round(best_mae, 4),
            "SD_ms": round(sd, 4),
            "Ref_Packet_Size": ref_size,
            "Ref_Index": int(ref_index)
        })

        all_data.append(group_df)

summary_df = pd.DataFrame(summary)
combined_df = pd.concat(all_data, ignore_index=True)

with pd.ExcelWriter("receiver_log.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    combined_df.to_excel(writer, sheet_name="All Data with Theories", index=False)
    summary_df.to_excel(writer, sheet_name="Summary by Group", index=False)

print("Analyzer finished.")
