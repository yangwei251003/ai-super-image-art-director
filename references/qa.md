# Visual quality review

Review the user's brief and the actual generated image at readable resolution. Use an atomic question for each expected fact: “Are there four distinct motors?” is more reliable than “Is this a good drone?” Record only visible evidence. If a feature is hidden, ambiguous, or too small, mark it uncertain. Aesthetic scores are informed judgments, not proof of physical or textual correctness. Automatic image-text metrics have known limitations; the pass gate is deliberately conservative.

## Required hard-check categories

| ID | Check when applicable | Repair direction |
|---|---|---|
| `brief_alignment` | Required subject, audience context, brand limits, required elements | Regenerate if missing or contradictory |
| `human_anatomy` | Hands, face, body proportions, pose, object interaction | Edit a localized defect; regenerate if widespread |
| `spatial` | Perspective, scale, support/contact, occlusion | Regenerate structural errors |
| `lighting` | Light-source direction, cast shadows, reflections, transparency | Edit if isolated; otherwise regenerate |
| `object_integrity` | Parts, material, assembly, realistic function | Edit local part error; otherwise regenerate |
| `text` | Transcribe every required string and compare character by character; hierarchy and readability | Edit exact text; fail if still wrong or unreadable |
| `count` | Explicit numbers, limbs, repeated parts, symmetry | Regenerate unless a local edit can preserve all other counts |
| `scene_logic` | Time, geography, interaction, gravity, credible context | Regenerate; allow deliberate fantasy specified by user |
| `domain` | Only rules activated by the subject and verified reference or profile | Regenerate technical structure errors |

For a four-arm quadrotor, count four distinct arms and motors if the view permits. For FPV, check camera orientation and plausible placement of frame, battery, and propulsion only if the brief specifies that topology and trustworthy references are available. A cinewhoop or other drone configuration is not automatically wrong. Do not infer invisible components.

## Five quality axes, 0–2 each

- **Communication:** 0 = message or requested action is missing; 1 = understandable; 2 = immediate and persuasive for the audience.
- **Hierarchy and composition:** 0 = competing focus or unusable layout; 1 = readable structure; 2 = strong first, second, and supporting levels.
- **Style and brand fit:** 0 = conflicts with brief or brand; 1 = suitable; 2 = distinctive and well matched.
- **Lighting and material:** 0 = distracting inconsistency or plastic-looking material; 1 = credible/intentional; 2 = coherent, refined treatment.
- **Legibility and export suitability:** 0 = required content unreadable or clipped; 1 = usable; 2 = clear at target platform size with safe margins.

A pass requires at least 8/10, no axis at 0, and no `fail` or `uncertain` on any applicable hard check. Severity guides repair priority, not permission to pass an unresolved defect. Do not use the numeric score to overrule a hard failure.

## Repair

Classify the dominant defect, then change only what addresses it. Preserve the original brief, exact text, source-reference roles, and previously correct details. Use image-tool edit for a localized fault. Regenerate for overall layout, count, topology, spatial, scene, or message failure. Inspect again after either operation. There are at most two corrections after the initial image per direction.

If no image passes, return the strongest preview with a clear “未通过审核” status, remaining concrete defects, and actual attempt count. Do not silently hide a failed requested variant or claim perfect real-world accuracy.

After resizing, padding, or an approved crop, inspect the exported PNG separately. Text or subjects clipped by export fail even when the pre-export image passed.
