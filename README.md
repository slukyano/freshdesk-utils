# Freshdesk utilities

Productivity scripts for freshdesk.com.

## Prerequisites

- Python 3 (tested on 3.6)
- `pip install requests`
- `pip install python3-wget`
- Freshdesk API key (can be found in "Profile settings")

## `get_attachments.py`

Downloads all attachments of a ticket, sorts them by post, extracts ZIP and TAR acrhives. All will be placed in a directory called `attachments` in the current working directory.

Usage:

    get_attachments.py --apikey <api_key> --ticket <ticket_number>
