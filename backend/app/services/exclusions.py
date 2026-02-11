import pandas as pd


def apply_exclusions(data: pd.DataFrame, rules: list[dict]) -> tuple[pd.DataFrame, dict]:
    result = data.copy()
    provenance = {"rules": [], "initial_rows": int(len(data)), "removed_rows": 0}

    for rule in rules:
        name = rule["rule_name"]
        params = rule.get("params", {})
        before = len(result)

        if name == "exclude_duration_lt":
            threshold = float(params["seconds"])
            result = result[result["duration_sec"] >= threshold]
        elif name == "exclude_missing_timestamp_pct_gt":
            threshold = float(params["pct"])
            result = result[result["missing_timestamps_pct"] <= threshold]
        elif name == "exclude_pretest_score_gt":
            threshold = float(params["score"])
            result = result[result["pretest_score"] <= threshold]

        removed = before - len(result)
        provenance["rules"].append({"rule": name, "params": params, "removed": int(removed)})

    provenance["removed_rows"] = provenance["initial_rows"] - int(len(result))
    return result, provenance
