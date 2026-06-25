#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BUFFER_API_URL = "https://api.buffer.com"

QUERY_CHANNELS = """
query GetChannels {
  account {
    channels { id name service }
  }
}
"""

QUERY_SENT_POSTS = """
query GetSentPosts($orgId: OrganizationId!, $channelId: ChannelId!, $after: String) {
  posts(
    first: 50
    after: $after
    input: {
      organizationId: $orgId
      filter: {
        status: [sent]
        channelIds: [$channelId]
      }
      sort: [{ field: dueAt, direction: desc }]
    }
  ) {
    edges {
      node {
        id
        text
        sentAt
        externalLink
        metadata {
          ... on LinkedInPostMetadata {
            firstComment
            linkAttachment {
              url
            }
          }
        }
        metrics {
          type
          value
        }
        metricsUpdatedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def run_buffer_query(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against the Buffer API."""
    api_key = os.environ.get("BUFFER_API_KEY")
    if not api_key:
        raise ValueError(
            "BUFFER_API_KEY not found in environment. "
            "Please add it to your .env file."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {"query": query, "variables": variables or {}}
    resp = requests.post(BUFFER_API_URL, headers=headers, json=payload)

    data = resp.json()
    if "errors" in data:
        errors = data["errors"]
        # Some errors (like INSUFFICIENT_SCOPE) are partial — GraphQL still returns data
        ignorable_codes = {"INSUFFICIENT_SCOPE", "FORBIDDEN"}
        fatal_errors = [e for e in errors if e.get("extensions", {}).get("code") not in ignorable_codes]
        if fatal_errors:
            raise RuntimeError(f"Buffer API error: {fatal_errors}")
        # Log scope/permission warnings but continue with partial data
        for e in errors:
            logger.warning(f"Buffer API warning ({e.get('path', '?')}): {e['message']}")

    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

    return data.get("data", {})


def get_linkedin_channel_id() -> str:
    """Discover the first LinkedIn channel ID from the Buffer account.

    Falls back to BUFFER_CHANNEL_ID env var if API query fails (due to permissions).
    """
    channel_id = os.environ.get("BUFFER_CHANNEL_ID")
    if channel_id:
        logger.info(f"Using BUFFER_CHANNEL_ID from env: {channel_id}")
        return channel_id

    try:
        data = run_buffer_query(QUERY_CHANNELS)
        channels = data.get("account", {}).get("channels", [])

        linkedin_channels = [ch for ch in channels if ch.get("service") == "linkedin"]
        if not linkedin_channels:
            raise RuntimeError("No LinkedIn channels found in Buffer account")

        channel_id = linkedin_channels[0]["id"]
        logger.info(f"LinkedIn Channel ID: {channel_id}")
        return channel_id
    except RuntimeError as e:
        if "Not authorized" in str(e):
            raise RuntimeError(
                f"Could not read channels from Buffer API (permission denied). "
                f"Set BUFFER_CHANNEL_ID in your .env file. "
                f"Find it in Buffer dashboard under Settings → Channels → LinkedIn"
            )
        raise


def fetch_all_sent_posts(org_id: str, channel_id: str) -> list[dict]:
    """Fetch all sent LinkedIn posts using cursor-based pagination."""
    all_posts = []
    after_cursor = None
    page_count = 0

    while True:
        page_count += 1
        logger.info(f"Fetching page {page_count}...")

        variables = {
            "orgId": org_id,
            "channelId": channel_id,
            "after": after_cursor,
        }

        data = run_buffer_query(QUERY_SENT_POSTS, variables)
        posts_response = data.get("posts", {})
        edges = posts_response.get("edges", [])

        for edge in edges:
            all_posts.append(edge.get("node", {}))

        page_info = posts_response.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        logger.info(f"Page {page_count}: {len(edges)} posts, hasNextPage={has_next}")

        if not has_next:
            break

        after_cursor = page_info.get("endCursor")

    logger.info(f"Total posts fetched: {len(all_posts)}")
    return all_posts


def extract_metrics(metrics: list[dict]) -> dict:
    """Extract metric values by type from the metrics array."""
    result = {
        "reactions": None,
        "comments": None,
        "impressions": None,
        "reach": None,
        "engagement_rate": None,
    }

    if not metrics:
        return result

    for metric in metrics:
        metric_type = metric.get("type", "").lower()
        value = metric.get("value")

        if metric_type == "reactions":
            result["reactions"] = value
        elif metric_type == "comments":
            result["comments"] = value
        elif metric_type == "impressions":
            result["impressions"] = value
        elif metric_type == "reach":
            result["reach"] = value
        elif metric_type == "engagementrate":
            result["engagement_rate"] = value

    return result


def write_csv(posts: list[dict], output_path: str) -> None:
    """Write posts to CSV file with UTF-8 BOM for emoji support."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "post_id",
            "sent_at",
            "text",
            "first_comment",
            "post_link",
            "reactions",
            "comments",
            "impressions",
            "reach",
            "engagement_rate",
            "metrics_updated_at",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for post in posts:
            metrics = extract_metrics(post.get("metrics", []))
            metadata = post.get("metadata") or {}
            first_comment = metadata.get("firstComment") or ""
            post_link = post.get("externalLink") or ""

            row = {
                "post_id": post.get("id", ""),
                "sent_at": post.get("sentAt", ""),
                "text": post.get("text", ""),
                "first_comment": first_comment,
                "post_link": post_link,
                "reactions": metrics["reactions"],
                "comments": metrics["comments"],
                "impressions": metrics["impressions"],
                "reach": metrics["reach"],
                "engagement_rate": metrics["engagement_rate"],
                "metrics_updated_at": post.get("metricsUpdatedAt", ""),
            }

            writer.writerow(row)

    logger.info(f"CSV written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download published LinkedIn posts from Buffer API"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/linkedin_posts.csv",
        help="Output CSV file path (default: output/linkedin_posts.csv)",
    )

    args = parser.parse_args()

    try:
        channel_id = get_linkedin_channel_id()
        org_id = os.environ.get("BUFFER_ORG_ID")
        if not org_id:
            raise RuntimeError(
                "BUFFER_ORG_ID not set in .env. "
                "Find it in your Buffer dashboard under Settings → Organization"
            )
        posts = fetch_all_sent_posts(org_id, channel_id)
        write_csv(posts, args.output)
        logger.info("Done!")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
