# Approval manifests

External release actions are blocked unless a matching approval file exists.

Example:

```json
{
  "approved": true,
  "slug": "day-001-messy-notes-to-action-draft",
  "allow": ["git-push", "x-post", "linkedin-post"],
  "approved_by": "Anas",
  "notes": "Reviewed locally; okay to publish."
}
```

Check an action with:

```bash
python3 scripts/check_approval.py day-001-messy-notes-to-action-draft x-post
```
