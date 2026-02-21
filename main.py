import pandas as pd
import hashlib
import os
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, time

os.makedirs("output", exist_ok=True)

# =====================
# LOAD DATA
# =====================
user_df = pd.read_excel("data/sentinelpay_user_master.xlsx")
tx_df = pd.read_excel("data/sentinelpay_transaction_stream.xlsx")

user_map = user_df.set_index("User_ID").to_dict("index")

# =====================
# MEMORY STATE
# =====================
last_tx = {}
session_seen = set()
daily_tx_count = {}
ledger = []

# =====================
# HELPERS
# =====================
def haversine(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lat2): return 0
    R = 6371
    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*R*asin(sqrt(a))

def hash_record(data):
    return hashlib.sha256(str(data).encode()).hexdigest()

def parse_time(val):
    if isinstance(val, time): return val
    if isinstance(val, str):
        for f in ["%H:%M:%S","%H:%M","%I:%M %p"]:
            try: return datetime.strptime(val,f).time()
            except: pass
    if isinstance(val, pd.Timestamp): return val.time()
    return time(0,0)

# =====================
# RISK ENGINES
# =====================
def geo_risk(user, tx, prev):
    risk = 0
    home_dist = haversine(user["Home_Latitude"], user["Home_Longitude"], tx["Latitude"], tx["Longitude"])
    if home_dist > 500: risk += 40
    if home_dist > 1000: risk += 70
    if tx.get("Is_International_IP",0): risk += 50

    if prev is not None:
        d = haversine(prev["Latitude"], prev["Longitude"], tx["Latitude"], tx["Longitude"])
        t = (tx["Timestamp"] - prev["Timestamp"]).total_seconds()/3600
        if t > 0 and d/t > 900:
            risk += 80
    return min(risk,100)

def velocity_risk(user, tx, uid):
    risk = 0
    daily_tx_count[uid] = daily_tx_count.get(uid,0)+1

    if tx["Amount"] == 1: risk += 40
    if tx.get("Failed_Attempts_Last_10_Min",0) > 3: risk += 50
    if daily_tx_count[uid] > 2*user["Avg_Transactions_Per_Day"]: risk += 40
    return min(risk,100)

def device_risk(user, tx, prev):
    risk = 0
    if tx["Device_ID"] != user["Registered_Device_ID"]: risk += 60
    if prev is not None and prev["Device_ID"] != tx["Device_ID"]: risk += 70
    return min(risk,100)

def amount_risk(user, tx, uid):
    risk = 0
    if tx["Amount"] > 3*user["Avg_Transaction_Amount"]: risk += 50
    if tx["Amount"] > user["Max_Transaction_Amount"]: risk += 70
    if tx["Amount"] > user["Daily_Transaction_Limit"]: risk += 90
    return min(risk,100)

def network_risk(tx):
    risk = 0
    if tx["Network_Type"] not in ["WiFi","4G","5G"]: risk += 40
    if pd.notna(tx["Session_ID"]) and tx["Session_ID"] in session_seen: risk += 80
    if pd.notna(tx["Session_ID"]): session_seen.add(tx["Session_ID"])
    return min(risk,100)

def behavioral_risk(user, tx):
    risk = 0
    t = tx["Timestamp"].time()
    start = parse_time(user["Usual_Login_Time_Start"])
    end = parse_time(user["Usual_Login_Time_End"])

    if not (start <= t <= end): risk += 40
    if user["KYC_Status"] != "Full": risk *= 1.2
    if user["Risk_Category"] == "High": risk *= 1.3

    return min(int(risk),100)

# =====================
# DECISION ENGINE (YOUR METRICS)
# =====================
def decision_engine(score):
    score = int(score)
    if score <= 50: return "Approve"
    elif score <= 69: return "OTP"
    else: return "Block"

# =====================
# PROCESS
# =====================
outputs = []

for _, row in tx_df.iterrows():

    tx = row.copy()
    uid = tx["User_ID"]

    if uid not in user_map:
        continue

    user = user_map[uid]
    tx["Timestamp"] = pd.to_datetime(tx["Timestamp"])

    prev = last_tx.get(uid)

    g = geo_risk(user, tx, prev)
    v = velocity_risk(user, tx, uid)
    d = device_risk(user, tx, prev)
    a = amount_risk(user, tx, uid)
    n = network_risk(tx)
    b = behavioral_risk(user, tx)

    final = 0.2*g + 0.2*v + 0.15*d + 0.15*a + 0.15*n + 0.15*b
    final = min(100, int(final))

    decision = decision_engine(final)

    prev_hash = ledger[-1]["Current_Hash"] if ledger else "GENESIS"
    record = {
        "Transaction_ID": tx["Transaction_ID"],
        "Timestamp": str(tx["Timestamp"]),
        "Final_Risk_Score": final,
        "Decision": decision,
        "Previous_Hash": prev_hash
    }
    record["Current_Hash"] = hash_record(record)
    ledger.append(record)

    last_tx[uid] = tx

    outputs.append({
        "Transaction_ID": tx["Transaction_ID"],
        "Geo_Risk": g,
        "Velocity_Risk": v,
        "Device_Risk": d,
        "Amount_Risk": a,
        "Network_Risk": n,
        "Behavioral_Risk": b,
        "Final_Risk_Score": final,
        "Decision": decision
    })

# =====================
# SAVE OUTPUT
# =====================
pd.DataFrame(outputs).to_csv("output/risk_output.csv", index=False)
pd.DataFrame(ledger).to_csv("output/immutable_ledger.csv", index=False)

# =====================
# INTEGRITY CHECK
# =====================
for i in range(1, len(ledger)):
    if ledger[i]["Previous_Hash"] != ledger[i-1]["Current_Hash"]:
        print("Ledger Integrity FAILED")
        break
else:
    print("Ledger Integrity OK")