# Quick Start

## 1. Copy your Buffer API Key

Your Buffer API key is already set up in the template project. To reuse it:

```bash
# Copy the .env from the template project
cp /Users/alfonsosaeravila/Documents/linkedin_posts/.env .env
```

This copies your `BUFFER_API_KEY` to the new project.

**Alternatively**, if you prefer to manage it separately:
1. Open `/Users/alfonsosaeravila/Documents/linkedin_posts/.env` in an editor
2. Copy the `BUFFER_API_KEY=...` line
3. Create `.env` in this directory and paste it

**Note — If Buffer API permissions prevent reading channels**: Add your LinkedIn channel ID manually:
1. Find it in your Buffer dashboard: **Settings → Channels → LinkedIn** (note the channel ID)
2. Add to `.env`: `BUFFER_CHANNEL_ID=<your-channel-id>`


## 2. Run the Downloader

Dependencies are synced automatically by `uv run` on first execution:

```bash
uv run python src/post_downloader.py
```

The script will:
1. ✅ Connect to Buffer's API using your key
2. ✅ Discover your organization and LinkedIn channel
3. ✅ Fetch all published posts (automatic pagination, 50 per page)
4. ✅ Download metrics: reactions, comments, impressions, reach, engagement rate
5. ✅ Write `output/linkedin_posts.csv`

Expected output:
```
2026-06-24 17:30:15,123 - post_downloader - INFO - Organization ID: org-xyz123
2026-06-24 17:30:16,456 - post_downloader - INFO - LinkedIn Channel ID: ch-abc789
2026-06-24 17:30:16,789 - post_downloader - INFO - Fetching page 1...
2026-06-24 17:30:17,234 - post_downloader - INFO - Page 1: 50 posts, hasNextPage=true
2026-06-24 17:30:18,567 - post_downloader - INFO - Fetching page 2...
2026-06-24 17:30:19,012 - post_downloader - INFO - Page 2: 32 posts, hasNextPage=false
2026-06-24 17:30:19,345 - post_downloader - INFO - Total posts fetched: 82
2026-06-24 17:30:19,678 - post_downloader - INFO - CSV written to: output/linkedin_posts.csv
2026-06-24 17:30:19,890 - post_downloader - INFO - Done!
```

## 3. Open the CSV

Open `output/linkedin_posts.csv` in Excel, Google Sheets, or your favorite CSV tool.

**Columns**:
- `post_id` — Buffer post ID
- `sent_at` — When published (ISO 8601)
- `text` — Post content
- `first_comment` — Links/comments appended to post
- `reactions` — LinkedIn likes count
- `comments` — Comment count
- `impressions` — Times shown
- `reach` — Unique viewers
- `engagement_rate` — Engagement %
- `metrics_updated_at` — When metrics were last synced

## 4. (Optional) Custom Output Path

```bash
uv run python src/post_downloader.py --output my_linkedin_posts.csv
```

## Troubleshooting

### "BUFFER_API_KEY not found in environment"
- Make sure `.env` file exists in this directory
- Check it has the line: `BUFFER_API_KEY=...`
- The `.env` file is gitignored, so it won't be committed

### "No LinkedIn channels found in Buffer account"
- Your Buffer account doesn't have a LinkedIn channel connected
- Go to buffer.com and add a LinkedIn channel first

### Script hangs or times out
- Check your internet connection
- Buffer's GraphQL API might be slow for large post counts
- No automatic retries are built in yet (see `BUFFER_API_NOTES.md` for how to add them)

## What's Next?

- See `README.md` for detailed documentation
- See `BUFFER_API_NOTES.md` for API details and how to extend the script
- See `src/post_downloader.py` for the implementation

## Notes

- **LinkedIn post URL**: Not available from Buffer's API. You'd need LinkedIn's own API for that.
- **Metrics availability**: Only for posts that have been published for at least a few hours. Very recent posts may not have metrics yet.
- **Max page size**: The script fetches 50 posts per page (Buffer's recommended limit)
