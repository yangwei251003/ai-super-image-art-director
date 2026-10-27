---
name: ai-super-image-art-director
description: 视觉艺术总监与生图工作流：为招聘海报、企业宣传、产品广告、品牌视觉、校园活动和无人机宣传等需求分析受众与目标，推荐不同设计风格，生成图片并审查文字、人物和产品结构，按需修正。适用于用户要求多版本、不同风格、完整海报设计或广告创意；简单的单张素材生成可直接使用普通生图工具。 Art-direct and generate campaign images with distinct directions, visual critique, and bounded revisions.
---

# AI Super Image Art Director

Turn a visual brief into intentional images: understand the communication goal, propose fitting directions, generate with the built-in image tool, inspect every result, repair bounded failures, and deliver the images with an honest quality record. This is a Codex orchestration skill, not an API client or a promise of flawless output.

Resolve `<skill-root>` to the directory containing this `SKILL.md`. Run scripts by their full path from that root; keep project briefs, generated images, and QA reports in the user's workspace unless they specify another destination.

## Start with the brief

1. Extract a `CreativeBrief` using [the data contract](references/data-contract.md): subject, industry, audience, goal, emotion, platform, intended size, brand constraints, exact text, reference-image roles, must-have facts, and exclusions. Preserve literal text and user-specified image count. Mark absent facts as unknown; do not invent a company, date, product specification, contact detail, logo, or performance claim.
2. Read only the relevant entries in `knowledge/industry_profiles.json`, `knowledge/use_cases.json`, and `knowledge/domain_validators.json`. For a generic request, infer a sensible audience and goal from the wording; ask only if a missing fact changes the identity or truth of a publishable asset. Without publishable facts, make a clearly labeled visual concept.
3. Classify a request for “multiple versions” or “different styles” without a number as **three images**. Honor an explicit image count. A single-image request gets one image. Recommend 3–6 design directions in either case; select different visual families for the first three where feasible.

## Choose a direction

Run `python "<skill-root>/scripts/match_styles.py" --brief <brief.json> --top-k <3-6>`. It hard-excludes named forbidden styles/families, then ranks by goal, industry, audience, emotion, platform, and use case. Read the returned style cards from `style_library/styles.json` and `style_library/gallery_additions.json`, and, when relevant, source cards in `knowledge/case_studies.json`, `knowledge/trends.json`, or `knowledge/gallery_patterns.json`. State a concise reason tied to the brief for each direction. The script is candidate retrieval; if a critical brand or factual constraint justifies a different final order, document the reason.

Style cards describe transferable design mechanisms. Translate named brand references into general visual principles. Do not reproduce a brand's logo, signature composition, protected image, or unsupported product claim. Case cards separate source-stated facts from design observations and effectiveness inferences.

## Build and generate

For each selected direction, run `python "<skill-root>/scripts/build_prompt.py" --brief <brief.json> --style-id <id>` and retain the returned `PromptPackage`: Positive, Negative, Composition, Lighting, Material, camera/viewpoint, and compiled prompt. Non-photographic work uses viewpoint rather than a fictional camera lens. The built-in image tool accepts one prompt, so negative constraints are written as plain-language “avoid” clauses in the compiled prompt, not passed as an invented API parameter.

Use the built-in `image_gen` tool once per distinct image direction. It needs no `OPENAI_API_KEY`. For edits, include the generated image via the tool's supported recent-image or local-reference mechanism and preserve all constraints not under repair. Do not silently switch to a CLI or paid API when the built-in tool is unavailable. Give every supplied image a role: subject reference, brand asset, composition reference, or edit target.

The user chose direct model-rendered poster text for V1. Quote exact copy in the prompt. Check the rendered characters afterward; never claim exact text is correct because it was in the prompt.

## Critique and repair

Actually inspect the generated image, including at a close enough view for text, hands, counts, and product structure. Follow [the QA procedure](references/qa.md). Create a `QAReport` with evidence for each of the eight categories plus brief alignment, five 0–2 quality scores, issue scope, and revision count. Run `python "<skill-root>/scripts/qa_state.py" --report <report.json>` to get pass/edit/regenerate/failed-preview.

A pass requires every applicable hard check to pass, no quality axis scored 0, and a quality sum of at least 8/10. Treat “not visible clearly” as uncertain, not passed. Severity guides repair priority; even a minor unresolved failure remains a preview. Make at most **two** correction attempts after the initial image per direction. Use image-tool editing for genuinely local errors; regenerate for structural, count, scene, or brief mismatch. Recheck the entire image after every repair. If no candidate passes after the limit, deliver the best preview with its failed or uncertain checks plainly identified, not as a publication-ready final.

Domain checks are conditional. Enforce four visible motors and four arms only when the brief specifies a four-arm quadrotor; apply FPV component checks only when FPV is specified and reference views support them. Other drone topologies must not fail a four-arm rule.

## Export and deliver

If exact pixel dimensions were requested, export the selected image with `python "<skill-root>/scripts/export_image.py" --input <image> --output <png> --width <px> --height <px>`. This exporter requires Pillow from `requirements.txt`. The default is proportional fit plus edge-color padding, preserving all text and subjects. Cropping requires an inspected safe area and the explicit `--crop-approved` flag. Inspect the **exported** PNG again; dimensions alone do not establish quality.

Save project-bound final images to the user's chosen folder or current workspace; otherwise show them inline with their actual paths. Deliver the images, 3–6 recommended directions with short reasons, the final prompts, actual dimensions, and QA status/retries. Do not present a failed preview as a finished design.

## Maintain the knowledge base

Run `python "<skill-root>/scripts/validate_catalog.py"` after changes. Current case and trend cards are curated evidence, not instructions to copy examples. The reviewed [GPT-Image2 gallery](https://gpt-image2.canghe.ai/) patterns have stable source-case links in `knowledge/gallery_patterns.json`; they describe prompt mechanisms, not independently verified success rates. Five original adaptations requested by the user are in `style_library/gallery_additions.json`. For any later trend, use current primary sources, write a proposed card with source facts separated from inference, and request human review before adding it to the installed library. Do not update the library during an ordinary image request.

## References

- [Data contract and command examples](references/data-contract.md)
- [Visual QA rubric and repair rules](references/qa.md)
- `style_library/*.json`: visual grammar and prompt templates, including five original cards informed by the reviewed community gallery
- `knowledge/*.json`: industry, application, domain, case, trend, and gallery evidence
