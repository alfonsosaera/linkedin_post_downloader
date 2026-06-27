# Buffer GraphQL API Reference

## What's Available for Published Posts

### Core Post Data
The current script fetches:
- **post_id**: Buffer's internal post ID
- **sent_at**: ISO 8601 timestamp when the post was published
- **text**: Full post text/content
- **first_comment**: Custom first comment attached to the post (from `LinkedInPostMetadata.firstComment`, optional)
- **post_link**: Native LinkedIn post URL (from `Post.externalLink`, always present for sent posts)
- **metrics_updated_at**: When metrics were last synced from LinkedIn

### Metrics (Normalized across all platforms)
Buffer exposes these metrics for **sent posts only** (via the Preview `metrics` field, available since June 9, 2026):

| Metric Type | Field Name | Description |
|---|---|---|
| `reactions` | reactions | LinkedIn likes/reactions count |
| `comments` | comments | Number of comments |
| `impressions` | impressions | Number of times the post was shown |
| `reach` | reach | Number of unique users who saw the post |
| `engagementRate` | engagement_rate | Engagement rate as a percentage |
| `shares` | (not fetched) | Number of shares (available but not in current CSV) |
| `reposts` | (not fetched) | Number of reposts (available but not in current CSV) |

### LinkedIn-Specific Metadata
The `metadata` field on Post is a GraphQL union type. To access LinkedIn-specific fields, use an **inline fragment**:

```graphql
metadata {
  ... on LinkedInPostMetadata {
    firstComment          # Custom first comment text (String, optional)
    linkAttachment {      # External link you optionally attached when scheduling
      url                 # Link URL (e.g., paper, GitHub, tool)
      expandedUrl         # Expanded version of URL (String)
      text                # Link text (String)
      title               # Link title (String)
      thumbnail           # Single thumbnail URL (String)
      thumbnails          # Array of thumbnail options
    }
  }
}
```

**What's included in the CSV:**
- `firstComment` from `LinkedInPostMetadata` → CSV `first_comment` column
- `externalLink` from top-level Post → CSV `post_link` column (the native LinkedIn post URL)
- `linkAttachment` is NOT included in current CSV (it's an external URL you optionally attach, different from the LinkedIn post URL)

## What's NOT Available from Buffer

- **LinkedIn Post ID/URN**: The `LinkedInPostMetadata` type does not expose the LinkedIn `urn:li:ugcPost:...` ID format directly
  - The `externalLink` field contains the full LinkedIn post URL, but not the URN/ID separately

- **External link attachments in CSV**: Posts can have optional external links attached (via `linkAttachment`), but these are not included in the current CSV
  - Would require extending `QUERY_SENT_POSTS` to fetch `linkAttachment { url title ... }` and `write_csv()` to export them

## PostMetadata Union Types

The `metadata` field is a union that can be one of these types depending on the channel:
- `LinkedInPostMetadata` — for LinkedIn posts
- `FacebookPostMetadata` — for Facebook posts
- `TwitterPostMetadata` — for Twitter/X posts
- `InstagramPostMetadata` — for Instagram posts
- And 6 others (Pinterest, YouTube, TikTok, Bluesky, Threads, Mastodon, Google Business)

Each type has platform-specific fields. Query with inline fragments:
```graphql
metadata {
  ... on LinkedInPostMetadata { firstComment linkAttachment { url } }
  ... on TwitterPostMetadata { /* Twitter-specific fields */ }
  # etc.
}
```

## How to Extend the Script

### Add more LinkedIn-specific fields
Edit `QUERY_SENT_POSTS` in `src/post_downloader.py`:

```graphql
metadata {
  ... on LinkedInPostMetadata {
    firstComment
    linkAttachment {
      url
      title                # Add these
      expandedUrl          # fields if
      thumbnail            # needed
    }
  }
}
```

Then extract in `write_csv()`:
```python
metadata = post.get("metadata") or {}
link_att = metadata.get("linkAttachment") or {}
link_title = link_att.get("title") or ""
# Add to row dict
```

### Add more metrics to CSV
Edit `src/post_downloader.py`:

1. Add the metric type to `extract_metrics()`:
   ```python
   elif metric_type == "shares":
       result["shares"] = value
   elif metric_type == "reposts":
       result["reposts"] = value
   ```

2. Add columns to CSV fieldnames in `write_csv()`:
   ```python
   fieldnames = [
       ...,
       "shares",
       "reposts",
   ]
   ```

3. Update the row dictionary:
   ```python
   row = {
       ...,
       "shares": metrics["shares"],
       "reposts": metrics["reposts"],
   }
   ```

### Filter by date range
The `QUERY_SENT_POSTS` GraphQL query supports `startDate` and `endDate` filters. To add this:

1. Extend the argument parser:
   ```python
   parser.add_argument("--start-date", type=str, help="Filter by start date (ISO 8601)")
   parser.add_argument("--end-date", type=str, help="Filter by end date (ISO 8601)")
   ```

2. Pass to `fetch_all_sent_posts()` and include in variables:
   ```python
   variables = {
       "orgId": org_id,
       "channelId": channel_id,
       "after": after_cursor,
       "startDate": args.start_date,
       "endDate": args.end_date,
   }
   ```

3. Update query to use variables:
   ```graphql
   input: {
     organizationId: $orgId
     filter: {
       status: [sent]
       channelIds: [$channelId]
       startDate: $startDate
       endDate: $endDate
     }
   }
   ```

### Add external link attachments to CSV
If you want to include the optional external links users attach when scheduling posts:

1. Extend `QUERY_SENT_POSTS` in `src/post_downloader.py`:
   ```graphql
   metadata {
     ... on LinkedInPostMetadata {
       firstComment
       linkAttachment {
         url
         title
         expandedUrl
       }
     }
   }
   ```

2. Extract in `write_csv()`:
   ```python
   metadata = post.get("metadata") or {}
   link_att = metadata.get("linkAttachment") or {}
   external_url = link_att.get("url") or ""
   ```

3. Add to CSV fieldnames and row dict

## Buffer GraphQL Pagination Details

- **Cursor-based pagination only** (no offset-based)
- `first: N` → fetch up to N items (current script uses 50)
- `after: cursor` → continue from previous cursor
- `hasNextPage` → check if more items exist
- `endCursor` → pass to next `after` parameter
- No backward pagination (`before`, `last` not supported)

## Rate Limiting

Buffer's GraphQL API may have rate limits. The current script doesn't implement retry logic, but adding `tenacity` or `backoff` decorators would be straightforward if needed.
