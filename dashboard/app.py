import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import networkx as nx

st.set_page_config(layout="wide")

# ======================
# CYBER SOC CSS
# ======================
st.markdown("""
<style>
body {background:#020617;color:white;font-family:monospace;}
.card {
 background:#0f172a;padding:18px;border-radius:15px;
 box-shadow:0 0 25px rgba(0,255,255,0.12);
 border:1px solid #0ea5e9;margin-bottom:12px;
}
.alert {
 background:#2b0f0f;padding:15px;border-radius:10px;
 border:1px solid red;animation: blink 1s infinite;
}
@keyframes blink {50% {opacity:0.35;}}
.ticker {height:250px;overflow-y:auto;}
.badge {
 background:#022c22;padding:8px;border-radius:8px;
 border:1px solid #10b981;
}
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
latest = risk.iloc[-1]

# ======================
# HEADER
# ======================
st.title("🛡️ SentinelPay Autonomous Fraud Defense")
#st.markdown('<div class="badge">AI FIREWALL ACTIVE</div>', unsafe_allow_html=True)

# ======================
# METRICS
# ======================
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Transactions", len(risk))
c2.metric("Blocked", (risk["Decision"]=="Block").sum())
c3.metric("OTP", (risk["Decision"]=="OTP").sum())
c4.metric("Approved", (risk["Decision"]=="Approve").sum())
c5.metric("Latency", f"{np.random.randint(9,28)} ms")

# ======================
# ATTACK SIMULATOR
# ======================
if st.button("🔥 Simulate Coordinated Fraud Attack"):
    fake = latest.copy()
    fake["Final_Risk_Score"]=95
    fake["Decision"]="Block"
    risk = pd.concat([risk,pd.DataFrame([fake])])
    st.warning("Attack injected into system")

# ======================
# LAYOUT
# ======================
left,center,right = st.columns([1,2,1])

# ======================
# LIVE STREAM
# ======================
with left:
    st.subheader("LIVE FRAUD STREAM")
    st.markdown('<div class="ticker">', unsafe_allow_html=True)
    for _,row in risk.tail(12).iterrows():
        icon="🟢" if row["Decision"]=="Approve" else "🟠" if row["Decision"]=="OTP" else "🔴"
        st.markdown(f'<div class="card">{icon} {row["Transaction_ID"]}<br>Risk:{int(row["Final_Risk_Score"])}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ======================
# ANALYSIS CORE
# ======================
with center:
    st.subheader("Transaction Intelligence Core")

    score=int(latest["Final_Risk_Score"])
    gauge="🟢" if score<40 else "🟠" if score<70 else "🔴"

    st.markdown(f'<div class="card"><h2>{gauge} Risk Score {score}</h2>Decision: {latest["Decision"]}</div>', unsafe_allow_html=True)

    # Radar
    radar = pd.DataFrame({
        "risk":[latest["Geo_Risk"],latest["Velocity_Risk"],latest["Device_Risk"],
                latest["Amount_Risk"],latest["Network_Risk"],latest["Behavioral_Risk"]]},
        index=["Geo","Velocity","Device","Amount","Network","Behavior"]
    )
    st.line_chart(radar)

    # AI reasoning
    reasons=[]
    if latest["Geo_Risk"]>15: reasons.append("Geo jump anomaly")
    if latest["Velocity_Risk"]>15: reasons.append("Velocity burst")
    if latest["Device_Risk"]>15: reasons.append("Device mismatch")
    if latest["Behavioral_Risk"]>15: reasons.append("Dormant reactivation")
    if latest["Amount_Risk"]>15: reasons.append("Amount spike")

    if reasons:
        st.markdown('<div class="alert">'+" | ".join(reasons)+"</div>", unsafe_allow_html=True)
    else:
        st.success("Behavior normal")

# ======================
# BLOCKCHAIN EXPLORER
# ======================
with right:
    st.subheader("Blockchain Explorer")
    st.dataframe(ledger.tail(12), height=350)

# ======================
# FRAUD MAP
# ======================
st.subheader("Geo Jump Detection Map")
geo = pd.DataFrame({
    "lat":np.random.uniform(8,28,12),
    "lon":np.random.uniform(72,88,12)
})
st.map(geo)

# ======================
# FRAUD NETWORK GRAPH
# ======================
#st.subheader("Fraud Network Graph")
#G = nx.erdos_renyi_graph(10,0.3)
#edges = pd.DataFrame(list(G.edges()), columns=["source","target"])
#st.dataframe(edges)

# ======================
# LEADERBOARD
# ======================
st.subheader("Fraud Leaderboard")
top=risk.sort_values("Final_Risk_Score",ascending=False).head(5)
st.dataframe(top[["Transaction_ID","Final_Risk_Score","Decision"]])

# ======================
# HEAT ZONE
# ======================
st.subheader("🚨 High Risk Cluster")
st.dataframe(risk[risk["Final_Risk_Score"]>70])

# ======================
# INTEGRITY CHECK
# ======================
fail=False
for i in range(1,len(ledger)):
    if ledger.iloc[i]["Previous_Hash"]!=ledger.iloc[i-1]["Current_Hash"]:
        fail=True
        break

if fail:
    st.error("🚨 Blockchain Tampering Detected")
else:
    st.success("✅ Ledger Integrity Verified")

# ======================
# AUTO REFRESH
# ======================
time.sleep(0.6)
st.rerun()