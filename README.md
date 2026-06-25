# LinkedIn Published Posts Downloader

Download all your published LinkedIn posts from Buffer API, including reactions, comments, impressions, and first comments.

**⚠️ Known Issue (June 24, 2026)**: Buffer silently changed authorization policies on `account.channels` field. The script currently requires your LinkedIn channel ID to be manually provided via `BUFFER_CHANNEL_ID` env var since the API can't return it. See [BUFFER_PERMISSIONS_ISSUE.md](BUFFER_PERMISSIONS_ISSUE.md) for details.

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Create `.env` file

Copy your Buffer API key from the template project (`/Users/alfonsosaeravila/Documents/linkedin_posts`):

```bash
BUFFER_API_KEY=your_buffer_api_key_here
```

Create a `.env` file in this directory with:

```
BUFFER_API_KEY=<your-key>
```

## Usage

### Download all posts to CSV

```bash
uv run python src/post_downloader.py
```

This will:
1. Discover your organization ID and LinkedIn channel from Buffer
2. Fetch all published posts (paginated, 50 per page)
3. Extract metrics: reactions, comments, impressions, reach, engagement rate
4. Write results to `output/linkedin_posts.csv`

### Specify custom output path

```bash
uv run python src/post_downloader.py --output my_posts.csv
```

## Output Format

The CSV contains these columns:

| Column | Description |
|--------|-------------|
| `post_id` | Buffer post ID |
| `sent_at` | ISO 8601 timestamp when post was published |
| `text` | Full post text |
| `first_comment` | First comment (links block) attached to post |
| `reactions` | Number of LinkedIn reactions (likes) |
| `comments` | Number of comments |
| `impressions` | Number of impressions |
| `reach` | Number of unique users who saw the post |
| `engagement_rate` | Engagement rate as percentage |
| `metrics_updated_at` | When metrics were last synced from LinkedIn |

The CSV is encoded with UTF-8 BOM to safely handle emojis and special characters.

## Notes

- **LinkedIn post URL**: Buffer's API does not expose the native LinkedIn post URL (e.g., `linkedin.com/feed/update/...`). To get the URL, you would need to:
  - Use LinkedIn's own Creator Post Analytics API (requires LinkedIn API access)
  - Manually construct URLs using the `post_id` if there's a known pattern
  - Fetch directly from LinkedIn's API (separate OAuth setup required)

- **Metrics availability**: Metrics are only available for published posts. The `metrics_updated_at` field tells you when Buffer last synced data from LinkedIn's backend.

- **Pagination**: The script handles automatic pagination — it will fetch all 50 posts per page until all posts are retrieved.
