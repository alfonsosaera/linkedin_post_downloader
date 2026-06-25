# Buffer GraphQL API Reference

## What's Available for Published Posts

### Core Post Data
The current script fetches:
- **post_id**: Buffer's internal post ID
- **sent_at**: ISO 8601 timestamp when the post was published
- **text**: Full post text/content
- **first_comment**: Custom first comment attached to the post (LinkedIn feature)
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

## What's NOT Available from Buffer

- **LinkedIn Post URL**: Buffer doesn't expose the native LinkedIn post URL (e.g., `linkedin.com/feed/update/urn:li:activity:...`)
  - Workaround: Use LinkedIn's own API (requires separate OAuth)
  - Alternative: Manually construct if you know the LinkedIn `serviceUpdateId` / post URN

- **LinkedIn Native Post ID/URN**: The `LinkedInPostMetadata` type does not include the LinkedIn post's native URN or ID

- **serviceUpdateId**: Not exposed by Buffer's GraphQL API

## How to Extend the Script

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

### Get LinkedIn post URLs (requires LinkedIn API)
Buffer does not provide this. To get native LinkedIn URLs, you'd need:

1. **LinkedIn Creator Post Analytics API** (2025+):
   - Requires LinkedIn OAuth with `r_member_social` scope
   - Partner approval needed for third-party apps
   - Returns analytics + post URNs
   - Separate integration needed (not covered by Buffer)

2. **Buffer + LinkedIn integration**:
   - Use LinkedIn's Graph API directly after getting the post's `serviceUpdateId` from elsewhere
   - Construct URL manually if you know the pattern

## Buffer GraphQL Pagination Details

- **Cursor-based pagination only** (no offset-based)
- `first: N` → fetch up to N items (current script uses 50)
- `after: cursor` → continue from previous cursor
- `hasNextPage` → check if more items exist
- `endCursor` → pass to next `after` parameter
- No backward pagination (`before`, `last` not supported)

## Rate Limiting

Buffer's GraphQL API may have rate limits. The current script doesn't implement retry logic, but adding `tenacity` or `backoff` decorators would be straightforward if needed.
