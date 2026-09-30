# LinkedIn Published Posts Downloader

Download all your published LinkedIn posts from Buffer API, including reactions, comments, impressions, and first comments.

**⚠️ Known Issue (June 24, 2026)**: Buffer silently changed authorization policies on `account.channels` field. The script currently requires your LinkedIn channel ID to be manually provided via `BUFFER_CHANNEL_ID` env var since the API can't return it. See [BUFFER_PERMISSIONS_ISSUE.md](BUFFER_PERMISSIONS_ISSUE.md) for details.

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Create `.env` file

Create a `.env` file in this directory with three required keys:

```
BUFFER_API_KEY=<your-buffer-api-key>
BUFFER_CHANNEL_ID=<your-linkedin-channel-id>
BUFFER_ORG_ID=<your-org-id>
```

**Where to find each value:**
- **BUFFER_API_KEY**: Buffer dashboard → Settings → API
- **BUFFER_CHANNEL_ID**: Buffer dashboard → Settings → Channels → LinkedIn (in the channel URL)
- **BUFFER_ORG_ID**: Buffer dashboard → Settings → Organization

## Usage

### Download all posts to CSV

```bash
uv run python src/post_downloader.py
```

This will:
1. Read your organization ID and LinkedIn channel from `.env`
2. Fetch all published posts (paginated, 50 per page)
3. Extract metrics: reactions, comments, impressions, reach, engagement rate
4. Write results to `output/linkedin_posts.csv`

### Specify custom output path

```bash
uv run python src/post_downloader.py --output my_posts.csv
```

### Filter posts by date

Use `--since` to only include posts sent on or after a given date (`YYYY-MM-DD`, UTC). Since posts come back newest-first, the script also stops paginating as soon as it passes the cutoff, so this is faster than downloading full history.

```bash
uv run python src/post_downloader.py --since 2026-01-01
```

### Combine options

```bash
uv run python src/post_downloader.py --since 2026-01-01 --output output/2026_posts.csv
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--output` | Output CSV file path | `output/linkedin_posts.csv` |
| `--since` | Only include posts sent on or after this date (`YYYY-MM-DD`, UTC) | none (all posts) |

## Output Format

The CSV contains these columns:

| Column | Description |
|--------|-------------|
| `post_id` | Buffer post ID |
| `sent_at` | ISO 8601 timestamp when post was published |
| `text` | Full post text |
| `first_comment` | Custom first comment attached to the post (when present) |
| `post_link` | Native LinkedIn post URL (e.g., `linkedin.com/feed/update/urn:li:ugcPost:...`) |
| `reactions` | Number of LinkedIn reactions (likes) |
| `comments` | Number of comments |
| `impressions` | Number of impressions |
| `reach` | Number of unique users who saw the post |
| `engagement_rate` | Engagement rate as percentage |
| `metrics_updated_at` | When metrics were last synced from LinkedIn |

The CSV is encoded with UTF-8 BOM to safely handle emojis and special characters.

## Notes

- **LinkedIn post URL**: The `post_link` column contains the native LinkedIn post URL via Buffer's `externalLink` field. This is always populated for published posts.

- **First comment vs. external link attachment**: 
  - `first_comment` = custom comment text you optionally set when scheduling the post
  - External links attached to posts (e.g., paper URLs, GitHub repos) are in Buffer's `linkAttachment` field but are **not** included in the current CSV (they're rare; add if needed via BUFFER_API_NOTES.md)

- **Metrics availability**: Metrics are only available for published posts. The `metrics_updated_at` field tells you when Buffer last synced data from LinkedIn's backend. Some metrics may be `null` if insufficient access.

- **Pagination**: The script handles automatic pagination — it will fetch all 50 posts per page until all posts are retrieved (or until `--since` cuts it off early).
