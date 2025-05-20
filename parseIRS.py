#!/usr/bin/env python3
import os
import re
import multiprocessing as mp
import matplotlib.pyplot as plt
from lxml import etree

TAX_DIR = "/stat129/tax23"

# Choose your KEYWORD:
KEYWORD = re.compile(r"religion", re.IGNORECASE)

# Candidate revenue paths:
CANDIDATE_REVENUE_XPATHS = [
    "/Return/ReturnData/IRS990/TotalRevenueCurrentYear",
    "/Return/ReturnData/IRS990/TotalRevenue",
    "/Return/ReturnData/IRS990/CYTotalRevenueAmt",
    "/Return/ReturnData/IRS990/RevenueAmt",
]

def parse_and_filter(xml_path):
    """
    Parse one XML file. If the mission statement contains KEYWORD,
    return (org_name, revenue). Otherwise, return None.
    """
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()

        # Organization name
        org_name = root.xpath("string(/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt)").strip()

        # Mission statement
        mission = root.xpath("string(/Return/ReturnData/IRS990/MissionDesc)").strip()

        # Check if it matches the KEYWORD first, to save time
        if not KEYWORD.search(mission):
            return None

        # Try multiple revenue fields
        revenue = 0.0
        for xp in CANDIDATE_REVENUE_XPATHS:
            val_str = root.xpath(f"string({xp})").strip().replace(",", "")
            if val_str:
                try:
                    test_val = float(val_str)
                    revenue = test_val
                    break
                except ValueError:
                    pass

        return (org_name, revenue)

    except Exception:
        # If the file is malformed or there's an error, return None
        return None


def main():

    all_files = [os.path.join(TAX_DIR, f) for f in os.listdir(TAX_DIR) if f.endswith(".xml")]

    print(f"Found {len(all_files)} .xml files; running multiprocessing parse...")

    # Create a pool with as many processes as you have cores (or specify a smaller/larger number)
    with mp.Pool() as pool:
        # Map each filename to a worker
        results = pool.map(parse_and_filter, all_files)

    # Filter out None
    filtered = [r for r in results if r is not None]
    print(f"{len(filtered)} nonprofits matched the keyword '{KEYWORD.pattern}'.")

    # Sort by revenue descending
    filtered.sort(key=lambda x: x[1], reverse=True)

    # Show top 5
    top5 = filtered[:5]
    print("\nTop 5 matching nonprofits by revenue:")
    for i, (nm, rev) in enumerate(top5, 1):
        print(f"{i}. {nm} => ${rev:,.2f}")


if __name__ == "__main__":
    main()
