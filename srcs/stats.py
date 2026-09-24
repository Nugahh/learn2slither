"""Aggregate statistics computed from a batch of session records."""


def compute_stats(session_records):
    count = len(session_records)
    lengths = [record[0] for record in session_records]
    steps = [record[1] for record in session_records]
    capped = sum(1 for record in session_records if not record[2])
    return {
        "count": count,
        "avg_length": sum(lengths) / count,
        "max_length": max(lengths),
        "avg_duration": sum(steps) / count,
        "capped_percent": 100.0 * capped / count,
    }
