def build_review_result(item: dict, score_result: dict) -> dict:
    return {
        "code": item["code"],
        "name": item.get("name"),
        "pick_date": item.get("pick_date"),
        "total_score": score_result["total_score"],
        "grade": score_result["grade"],
        "decision": score_result["decision"],
        "subscores": score_result.get("subscores", {}),
        "strengths": score_result["strengths"],
        "risks": score_result["risks"],
        "comment": score_result["comment"],
        "files": item.get("files", {}),
    }
