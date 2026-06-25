#!/usr/bin/env python3
"""Simple test to validate the downloader script logic."""

import sys
import json
import csv
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent / "src"))

from post_downloader import extract_metrics, write_csv


def test_extract_metrics():
    """Test metric extraction from Buffer response format."""
    # Empty metrics
    result = extract_metrics([])
    assert result == {
        "reactions": None,
        "comments": None,
        "impressions": None,
        "reach": None,
        "engagement_rate": None,
    }

    # Sample metrics from Buffer
    metrics = [
        {"type": "reactions", "value": 42},
        {"type": "comments", "value": 5},
        {"type": "impressions", "value": 1250},
        {"type": "reach", "value": 890},
        {"type": "engagementRate", "value": 3.76},
    ]
    result = extract_metrics(metrics)
    assert result["reactions"] == 42
    assert result["comments"] == 5
    assert result["impressions"] == 1250
    assert result["reach"] == 890
    assert result["engagement_rate"] == 3.76
    print("✓ extract_metrics passed")


def test_write_csv():
    """Test CSV writing with sample posts."""
    sample_posts = [
        {
            "id": "post-1",
            "sentAt": "2026-06-24T10:30:00Z",
            "text": "Great post about AI 🤖",
            "metadata": {
                "linkedin": {
                    "firstComment": "📚 Read more: https://example.com"
                }
            },
            "metrics": [
                {"type": "reactions", "value": 42},
                {"type": "comments", "value": 5},
            ],
            "metricsUpdatedAt": "2026-06-24T15:00:00Z",
        },
        {
            "id": "post-2",
            "sentAt": "2026-06-23T14:15:00Z",
            "text": "Another great post",
            "metadata": {"linkedin": {}},
            "metrics": [
                {"type": "reactions", "value": 28},
            ],
            "metricsUpdatedAt": "2026-06-23T18:00:00Z",
        },
    ]

    output_path = "/tmp/test_linkedin_posts.csv"
    write_csv(sample_posts, output_path)

    # Verify the file was created and has correct content
    with open(output_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["post_id"] == "post-1"
    assert rows[0]["text"] == "Great post about AI 🤖"
    assert rows[0]["reactions"] == "42"
    assert rows[0]["comments"] == "5"
    assert rows[0]["first_comment"] == "📚 Read more: https://example.com"

    assert rows[1]["post_id"] == "post-2"
    assert rows[1]["reactions"] == "28"
    assert rows[1]["comments"] == ""  # None becomes empty string

    print("✓ write_csv passed")
    Path(output_path).unlink()


if __name__ == "__main__":
    test_extract_metrics()
    test_write_csv()
    print("\n✅ All tests passed!")
