

import pandas as pd, requests, xml.etree.ElementTree as ET, math, random, sys


key_path = "/stat129/llm_api_key"
with open(key_path) as f:
    api_key = f.read().strip()


def llm(textdata,
        prompt="",
        API_URL="https://llm.nrp-nautilus.io/v1/chat/completions",
        key=api_key,
        model="llama3-sdsc",
        max_tokens=8,
        temperature=0.2,
        kwargs={}):
    payload = {
        "model": model,
        "messages":[{"role":"user","content":prompt + textdata}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        **kwargs
    }
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {key}"}
    r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    return r.json()["choices"][0]["message"]["content"].strip() if r.ok else ""


TAGS = ["MissionDesc","ActivityOrMissionDesc","PrimaryExemptPurposeTxt","Desc"]
def mission_from_xml(path):
    try:
        root = ET.parse(path).getroot()
        for t in TAGS:
            el = root.find(f".//{t}")
            if el is not None and el.text and el.text.strip():
                return " ".join(el.text.split())
    except ET.ParseError:
        pass
    return ""

def wilson(s, n, z=1.645):
    ph = s/n
    d  = 1 + z*z/n
    c  = ph + z*z/(2*n)
    sp = z * math.sqrt(ph*(1-ph)/n + z*z/(4*n*n))
    return (c-sp)/d, (c+sp)/d

def classify():
    CSV_PATH = "/stat129/llm-summary.csv"
    df = pd.read_csv(CSV_PATH, header=None,
                     names=["ein","name","xml_path","keywords","mission_long"])
    df = df.head(100).copy()

    prompt = ("Which ONE of the following IRS 501(c) categories best describes "
              "this organization? Respond with exactly one word – "
              "Charitable, Religious, Foundation, Political, Other. "
              "Mission: ")

    missions = []
    for p in df["xml_path"]:
        missions.append(mission_from_xml(p))
    df["mission_extracted"] = missions
    df["llm_category"] = [llm(m, prompt) for m in df["mission_extracted"]]

    df.to_csv("llm_results.csv", index=False)

    audit = df.sample(30, random_state=42).reset_index(drop=True)
    audit["human_ok"] = pd.NA
    audit.to_csv("sample30.csv", index=False)
    print("✓ wrote llm_results.csv and sample30.csv – fill 'human_ok' then run:")
    print("  /opt/anaconda/bin/ipython llm_categorize_irs.py --ci sample30.csv")

def evaluate(csv):
    df = pd.read_csv(csv)
    if df["human_ok"].isna().any():
        sys.exit("Fill 'human_ok' with 1 (reasonable) or 0 (not).")
    s = int(df["human_ok"].sum()); n = len(df)
    lo, hi = wilson(s, n)
    print(f"Accuracy {s}/{n} = {s/n:.3f}")
    print(f"90 % Wilson CI: ({lo:.3f}, {hi:.3f})")

if __name__ == "__main__":
    if "--ci" in sys.argv:
        evaluate(sys.argv[sys.argv.index("--ci")+1])
    else:
        classify()
