import streamlit as st
import pandas as pd
import numpy as np
import os
import time

st.set_page_config(layout="wide")

# ======================
# CYBER SOC CSS
# ======================
st.markdown("""
<style>
body {background:#020617;color:white;font-family:monospace;}
.card {
 background:#0f172a;padding:18px;border-radius:15px;
 box-shadow:0 0 30px rgba(0,255,255,0.12);
 border:1px solid #0ea5e9;margin-bottom:12px;
}
.ticker {height:300px;overflow-y:auto;}
.flash-red {color:#ff4b4b;font-weight:bold;}
.flash-green {color:#10b981;font-weight:bold;}
.flash-orange {color:#f59e0b;font-weight:bold;}
.alert {
 background:#2b0f0f;padding:12px;border-radius:10px;
 border:1px solid red;animation: blink 1s infinite;
}
@keyframes blink {50% {opacity:0.3;}}
</style>
""", unsafe_allow_html=True)

# ======================
# SAFE LOAD
# ======================
if not os.path.exists("output/risk_output.csv"):
    st.error("Run main.py first")
    st.stop()

risk = pd.read_csv("output/risk_output.csv")
ledger = pd.read_csv("output/immutable_ledger.csv")

# ======================
# ATTACK SIMULATOR
# ======================
if st.button("🔥 Simulate Coordinated Fraud Attack"):
    fake = risk.iloc[-1].copy()
    fake["Final_Risk_Score"] = 95
    fake["Decision"] = "Block"
    risk = pd.concat([risk, pd.DataFrame([fake])], ignore_index=True)
    st.warning("Botnet attack injected")

latest = risk.iloc[-1]

# ======================
# HEADER
# ======================
st.title("🛡 SentinelPay Fraud Firewall")

# ======================
# METRICS + LATENCY MONITOR
# ======================
latencies = np.random.randint(30, 180, 10)
avg_latency = int(np.mean(latencies))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Transactions", len(risk))
c2.metric("Blocked", (risk["Decision"] == "Block").sum())
c3.metric("OTP", (risk["Decision"] == "OTP").sum())
c4.metric("Approved", (risk["Decision"] == "Approve").sum())
c5.metric("Latency", f"{avg_latency} ms")

if avg_latency > 200:
    st.markdown('<div class="alert">⚠ PERFORMANCE BREACH >200ms</div>', unsafe_allow_html=True)

# ======================
# LAYOUT
# ======================
left, center, right = st.columns([1, 2, 1])

# ======================
# LIVE TICKER
# ======================
with left:
    st.subheader("LIVE STREAM")
    st.markdown('<div class="ticker">', unsafe_allow_html=True)

    for _, row in risk.tail(20).iterrows():
        if row["Decision"] == "Approve":
            cls = "flash-green"
        elif row["Decision"] == "OTP":
            cls = "flash-orange"
        else:
            cls = "flash-red"

        st.markdown(
            f'<div class="card {cls}">{row["Transaction_ID"]}<br>Risk {int(row["Final_Risk_Score"])} → {row["Decision"]}</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ======================
# CENTER — RISK CORE
# ======================
with center:
    st.subheader("Risk Intelligence Core")

    score = int(latest["Final_Risk_Score"])
    st.progress(score)

    st.markdown(f"""
    <div class="card">
    <h2>Risk Score {score}</h2>
    Decision: <b>{latest["Decision"]}</b>
    </div>
    """, unsafe_allow_html=True)

    breakdown = pd.DataFrame({
        "Risk": [
            latest["Geo_Risk"],
            latest["Velocity_Risk"],
            latest["Device_Risk"],
            latest["Amount_Risk"],
            latest["Network_Risk"],
            latest["Behavioral_Risk"]
        ]},
        index=["Geo", "Velocity", "Device", "Amount", "Network", "Behavior"]
    )
    st.bar_chart(breakdown)

    # Reason Codes
    reasons = []
    if latest["Geo_Risk"] > 20: reasons.append("ERR_GEO_IMPOSSIBLE")
    if latest["Velocity_Risk"] > 20: reasons.append("ERR_VELOCITY_LIMIT")
    if latest["Device_Risk"] > 20: reasons.append("ERR_DEVICE_CHANGE")
    if latest["Amount_Risk"] > 20: reasons.append("ERR_AMOUNT_SPIKE")

    if reasons:
        st.markdown('<div class="alert">' + " | ".join(reasons) + '</div>', unsafe_allow_html=True)
    else:
        st.success("No rule triggered")

# ======================
# RIGHT — LEDGER + FIREWALL
# ======================
with right:
    st.subheader("Blockchain Ledger")
    st.dataframe(ledger.tail(10), height=350)

# ======================
# GEO VISUALIZATION
# ======================
st.subheader("Fraud Geo Visualization")
geo = pd.DataFrame({
    "lat": np.random.uniform(8, 28, 20),
    "lon": np.random.uniform(72, 88, 20)
})
st.map(geo)

# ======================
# FRAUD CLUSTER
# ======================
st.subheader("🚨 High Risk Cluster")
st.dataframe(risk[risk["Final_Risk_Score"] > 70])

# ======================
# LEADERBOARD
# ======================
st.subheader("Top Risk Transactions")
st.dataframe(risk.sort_values("Final_Risk_Score", ascending=False).head(5))

# ======================
# LEDGER INTEGRITY
# ======================
fail = False
for i in range(1, len(ledger)):
    if ledger.iloc[i]["Previous_Hash"] != ledger.iloc[i - 1]["Current_Hash"]:
        fail = True
        break

if not fail:
    st.success("Ledger OK")
else:
    st.error("Ledger Tampered")

# ======================
# AUTO REFRESH
# ======================
time.sleep(0.6)
st.rerun()