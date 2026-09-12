# Course registry and recovery

Persist only routing and checkpoint metadata in `~/.codex/course-preview/registry.json`.

## Canonical course key

Derive and normalize in this order:

1. `{institution}:{course-code}`
2. `{course-code}`
3. `{full-course-name}`

Normalize with Unicode NFC, lowercase comparison, collapsed whitespace, and hyphen separators. Exclude the term so repeat offerings remain in one course file. Store alternative forms as aliases.

## Registry shape

```json
{
  "schemaVersion": 1,
  "planKey": null,
  "courses": {
    "course-key": {
      "displayName": "Course name",
      "institution": null,
      "courseCode": null,
      "figmaFileKey": "...",
      "figmaUrl": "https://www.figma.com/board/...",
      "aliases": [],
      "createdAt": "UTC timestamp",
      "updatedAt": "UTC timestamp",
      "weeks": {
        "W01": {
          "term": "Semester A",
          "fingerprint": "sha256",
          "sectionNodeId": "1:2",
          "pageCount": 90,
          "status": "initialized",
          "lastBatch": 8,
          "createdAt": "UTC timestamp",
          "updatedAt": "UTC timestamp"
        }
      }
    }
  }
}
```

Do not store slide text, notes, extracted terminology, absolute paths, rendered images, user questions, or syllabus content.

## Status and checkpoints

- `initialized`: every original page card exists.
- `in_progress`: at least one module has detailed notes, but weekly review is incomplete.
- `complete`: every module, local note-payload check, Figma read-back audit, glossary, concept map, link check, and screenshot check passed.
- `revision_pending`: the same week key was supplied with a different fingerprint and awaits the user's choice.
- `failed`: an explicitly recorded write failure; keep the last successful batch.

Only advance a checkpoint after its corresponding Figma write and read-back audit succeed. Resume by finding stable node names and starting after `lastBatch`; never blindly recreate earlier batches. A transport failure may leave partial mutations, so inspect the stable names and actual text before an idempotent retry.

## Fingerprint and revision behavior

- Use the source file SHA-256 from `deck_manifest.py`.
- Reuse the week without duplication when week key and fingerprint both match.
- When the week key matches but the fingerprint differs, make no Figma mutation. Ask whether to update the existing week or create `Wxx-R2`, `Wxx-R3`, and so on.
- Record the mismatch with `set-week-status --status revision_pending`; this preserves the active fingerprint and stores the proposed value as `pendingFingerprint`.
- Require `--allow-fingerprint-replace` only after the user explicitly approves updating the existing week. A new revision key does not need this flag.
- Preserve existing notes until an approved revision is successfully written.

## Isolation invariants

- Resolve the course through the registry before every Figma write.
- Reject a supplied FigJam URL whose file key differs from the resolved course record unless the user explicitly rebinds the course.
- Require `upsert-course --allow-rebind` for that explicit rebind; ordinary upserts must reject a changed file key.
- Never copy another course's file key, node IDs, or canvas coordinates into the current course record.
- Commit a new course record only after its FigJam file exists.
