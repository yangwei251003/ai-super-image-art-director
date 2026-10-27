# Data contract

The scripts use UTF-8 JSON. They do not call an image model. Codex creates a brief, uses the scripts for deterministic retrieval and validation, and calls the built-in image tool.

## CreativeBrief

```json
{
  "subject": "four-arm FPV quadcopter training",
  "environment": "real university engineering lab",
  "industry": "education",
  "use_case": "education",
  "goal_tags": ["recruitment", "education"],
  "audience_tags": ["students"],
  "emotion_tags": ["innovative", "trustworthy"],
  "platform_tags": ["poster", "social"],
  "width": 1024,
  "height": 1536,
  "exact_text": ["无人机社团招新"],
  "brand_constraints": [],
  "must_have": ["four arms", "four motors", "camera mounted on the forward frame"],
  "avoid_terms": ["cyberpunk"],
  "avoid_style_ids": [],
  "avoid_families": [],
  "reference_images": []
}
```

Use IDs from the catalog. Keep unknown factual fields absent or empty. The `use_case` field uses one of the 12 visual categories in the style library. An application profile in `knowledge/use_cases.json` may supply additional campaign guidance; it does not override user facts. `exact_text` accepts a string or a list of verbatim strings. `reference_images` entries may include a path and a specific role. Do not include an invented logo or contact detail.

## Script interfaces

```powershell
python "<skill-root>/scripts/match_styles.py" --brief brief.json --top-k 3
python "<skill-root>/scripts/build_prompt.py" --brief brief.json --style-id documentary_motion
python "<skill-root>/scripts/qa_state.py" --report qa.json
python "<skill-root>/scripts/export_image.py" --input input.png --output final.png --width 1024 --height 1536
python "<skill-root>/scripts/validate_catalog.py"
```

`match_styles.py` returns ranked candidates with scores, matched fields, and a family-diverse selected list. `build_prompt.py` returns the labeled prompt fields and a single compiled prompt for the built-in tool. Both print JSON to stdout; `--output` can save the same JSON. `qa_state.py` prints the next action and unresolved issues.

## QAReport

```json
{
  "direction_id": "documentary_motion",
  "attempt": 0,
  "issue_scope": "local",
  "hard_checks": [
    {"id": "brief_alignment", "status": "pass", "severity": "critical", "evidence": "The requested subject and setting are visible.", "repair": ""},
    {"id": "human_anatomy", "status": "not_applicable", "severity": "major", "evidence": "No person appears.", "repair": ""},
    {"id": "spatial", "status": "pass", "severity": "major", "evidence": "Perspective and contacts are consistent.", "repair": ""},
    {"id": "lighting", "status": "pass", "severity": "major", "evidence": "Light and shadows agree.", "repair": ""},
    {"id": "object_integrity", "status": "pass", "severity": "major", "evidence": "Parts connect correctly.", "repair": ""},
    {"id": "text", "status": "pass", "severity": "critical", "evidence": "Every requested character is readable and exact.", "repair": ""},
    {"id": "count", "status": "pass", "severity": "critical", "evidence": "Requested counts match.", "repair": ""},
    {"id": "scene_logic", "status": "pass", "severity": "major", "evidence": "The scene is plausible for the brief.", "repair": ""},
    {"id": "domain", "status": "pass", "severity": "critical", "evidence": "The applicable device topology matches the brief.", "repair": ""}
  ],
  "soft_scores": {
    "communication": 2,
    "hierarchy_composition": 2,
    "style_brand_fit": 2,
    "lighting_material": 1,
    "legibility_export": 2
  }
}
```

Hard statuses are `pass`, `fail`, `uncertain`, or `not_applicable`. Severity is `critical`, `major`, or `minor`. `attempt=0` is the initial image; 1 and 2 are corrected images. A non-applicable domain check needs evidence explaining why it does not apply. The QA state machine does not inspect pixels: the agent must actually inspect the image and record grounded evidence.
