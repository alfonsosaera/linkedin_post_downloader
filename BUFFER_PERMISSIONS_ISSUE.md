# Buffer API Permissions Issue (June 20-24, 2026)

## Problem

On **Saturday June 20, 2026**, your Buffer API key could query `account { channels { id name service } }` successfully. On **Wednesday June 24, 2026**, the same query returns `FORBIDDEN` even though the key has `account:read` permission.

This is not a code bug — it's a Buffer API authorization policy change that happened silently (no changelog entry, no announcement).

## What Works

- `account { id }` — works, returns your account ID
- `posts` query with `organizationId` — requires organization ID from posts API (different from account ID)
- `posts:read` scope — active

## What Broke

- `account { channels }` field — now requires permissions your token doesn't have
- `account { currentOrganization }` field — also FORBIDDEN

## Impact on This Script

The script cannot:
1. Auto-discover your LinkedIn channel ID from the Buffer API
2. Use that channel ID to fetch sent posts

## Workaround (Temporary)

### For Now: Manually Provide Channel ID

1. Go to **buffer.com → Settings → Channels → LinkedIn**
2. Note your LinkedIn channel ID
3. Add to `.env`:
   ```
   BUFFER_CHANNEL_ID=<your-id-here>
   ```

### To Get Your Channel ID

The channel ID is visible in:
- Buffer dashboard Channels list (may require inspection via browser dev tools)
- Buffer's API documentation if you're an admin (may be on organization settings page)

## Permanent Solution

Contact **Buffer support** to either:
1. Restore `account:read` permission to include `channels` field
2. Provide documentation on how to obtain channel IDs without API access
3. Clarify the new scope/permission model for accessing channels

Email: **developersupport@buffer.com**

Mention:
- Date of change: June 20-23, 2026
- Affected field: `account { channels }`
- Error code: FORBIDDEN (code: "FORBIDDEN")
- Your affected scopes: `account:read, account:write, posts:read, posts:write`

## Technical Details

Buffer was actively restructuring channel-level permissions on June 16-23, 2026 (per their API changelog). The `account.channels` authorization enforcement appears to have been tightened as part of this work, without a corresponding public announcement or schema change (the field still exists, it's just now blocked at the authorization layer).

This is a breaking change for any integration that relied on auto-discovering channel IDs via the API.
