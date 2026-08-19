---
name: daily-outfit-social-post
description: Use when the user wants a 每日穿搭推荐, 小红书 or 抖音 outfit post, daily lookbook images, outfit flat lay, mirror selfie, OOTD photo set, fashion caption, or photorealistic clothing-material image generation for social publishing.
---

# Daily Outfit Social Post

## Overview

Create one social-ready daily outfit recommendation for Xiaohongshu or Douyin. Each work includes an attention-grabbing all-Chinese title under 20 characters, a cover image, and a short all-Chinese post body under 100 Chinese characters. Generate supporting photorealistic outfit images when useful for the work. Default to one complete outfit look unless the user asks for multiple looks.

**REQUIRED SUB-SKILL:** Use `baoyu-imagine` when generating outfit images.

## Workflow

1. Parse the user request for platform, season, weather, city, occasion, gender expression, body-proportion preferences, color palette, style keywords, budget tier, forbidden items, inspiration images, and output directory.
2. If the request references the established OOTD creator image, same-person continuity, or ongoing account generation, read `references/persona-lock.md` and use its fixed identity references and Persistent Persona Lock.
3. Build an outfit fact sheet before drafting captions or image prompts. It must list each visible item, color, material, texture, silhouette, fit, styling detail, accessories, shoes, bag, hair/makeup mood when relevant, and the intended scene.
4. Build a continuity lock before generating anything. It must freeze the exact model identity, hairstyle, hair color, skin tone, body height impression, body type, pose family, outfit items, item colors, material finish, accessory count, bag shape, shoe model, scene family, lighting direction, and camera distance. Copy this lock verbatim into every image prompt.
   The lock must also include an age read: keep the same youthful/young-adult appearance across every image. Do not let one image read noticeably older, more mature, or more worn than the others.
5. Build a pose plan for every person-containing image in the same outfit work. The cover/full-body image and detail/atmosphere image must use visibly different poses, such as different body angle, head direction, hand placement, walking/standing state, bag position, camera distance, or shooting angle. Keep identity, outfit, scene, and lighting locked while varying pose.
6. Choose the outfit:
   - If no style is specified, choose one everyday, camera-friendly outfit with clear texture contrast and a complete head-to-toe styling logic.
   - If inspiration images are provided, preserve their main mood, garment category, color relationship, pose language, and shooting environment without copying private identity, watermark, or platform-specific marks.
   - If the user asks for multiple looks, create one complete fact sheet per look and produce at least 3 images per look.
7. Produce the final work in this order:
   1. 标题
   2. 封面
   3. 正文
8. Before writing final title/body, read `references/copy-style.md`. The final `标题`, `正文`, and hashtags must be Chinese-only with no Chinese-English mixing.
9. Before writing image prompts, read `references/cover-style.md`.
10. For exact continuity requests, do not batch all images from scratch. Generate the full-body anchor image first, lock its observed identity and scene details, then generate the cover, flat lay, and detail images using the anchor as a reference when the provider supports refs.
11. For images, create prompt files and run `baoyu-imagine`. If inspiration images are provided, pass them as references with `--ref` when the selected provider supports references; otherwise convert them into a concise visual brief.
12. Do not put visible text inside outfit photos by default. Provide the title and caption as post copy unless the user explicitly asks for text overlays.
13. Verify generated image files exist, are valid PNG/JPG files, match the requested orientation, and pass the Visual QA checklist below.

## Output Contract

### 1. 标题

Write 1 attention-grabbing Chinese-only title suitable for Xiaohongshu and Douyin. It must be 20 Chinese characters or fewer, specific, everyday, and natural, such as:

`温柔白裙太出片了`

Avoid English words, Chinese-English mixed terms, exaggerated claims, luxury-name stuffing, body anxiety, fake urgency, or crude clickbait. Follow `references/copy-style.md`.

### 2. 封面

Default final cover count: exactly 1 cover image per outfit work.

- The cover should usually be the strongest full-body or nearly full-body OOTD image.
- It must clearly show the outfit, face, hair, shoes, bag, and styling mood.
- Use vertical 3:4 by default for Xiaohongshu and Douyin unless the user requests another ratio.
- Keep cover photography photorealistic, social-ready, bright but comfortable, and free of visible text unless the user explicitly asks for title overlay.
- Recommended filename: `outputs/<slug>-cover.png`.

### Supporting Images

When the user asks for a full image set, multiple looks, proof of consistency, or detailed OOTD work, generate exactly 3 images per outfit look:

1. `搭配平铺图`: all clothing, shoes, bag, and accessories arranged as a clean flat lay or bed/table layout.
2. `封面/上身全身图`: full-body try-on photo, preferably mirror selfie or natural street/home full-body shot. This is also the default cover.
3. `细节氛围图`: default to a full-body or nearly full-body pose with detail emphasis; keep the head and both feet visible with comfortable margins unless the user explicitly asks for a crop. This image should still show the outfit in context, not an unrelated close-up. Its pose must be visibly different from the cover/full-body image while preserving the same person, outfit, scene family, and lighting.

If the user requests more images, add alternate full-body poses, back/side view, commute/street scene, or detail close-ups while preserving the same outfit.

Recommended filenames:

- `outputs/<slug>-flatlay.png`
- `outputs/<slug>-cover.png`
- `outputs/<slug>-detail.png`

Do not include on-image text, labels, captions, watermarks, or UI elements by default. If the user asks for cover text, keep it short and plan to visually inspect legibility before delivery.

### 3. 正文

Write the post body in Chinese only, 100 Chinese characters or fewer. Include:

- a natural opening sentence
- key outfit items
- one style hook or occasion note
- Chinese-only hashtags suitable for Xiaohongshu or Douyin
- a compact competitor-inspired rhythm: 左滑或上身引导、穿搭公式、✔单品拆解、场景收束

Keep the body publishable as-is. Do not include image-generation prompt text in the final social caption. Do not use English letters, English fashion slang, or Chinese-English mixed wording. Follow `references/copy-style.md`.

## Outfit Recommendation Rules

- A look must be wearable and complete: top, bottom or one-piece, shoes, and at least one accessory unless the user asks for minimal styling.
- If the fixed OOTD creator persona is used, every person-containing generated image must pass `references/persona-lock.md` identity QA.
- For strict continuity, every image in the set must reuse the exact same continuity lock text. Do not paraphrase it between prompts.
- For strict continuity with multiple person-containing images, consistency does not mean repeating the same pose. Reuse the same identity and outfit lock, but make each person-containing image visibly different in pose, angle, or action.
- Prioritize clear material contrast: lace with denim, knit with satin, linen with leather, cotton shirting with metal jewelry, or wool with suede.
- Match season and weather. Do not recommend exposed summer looks for cold weather unless the user explicitly asks.
- Keep proportions practical: explain waistline, leg line, shoulder width, layering thickness, and shoe visual weight when relevant.
- Prefer platform-friendly daily outfits: clean composition, visible outfit logic, concise styling hooks, and real-life scenes.
- Keep the same outfit items, item count, item colors, material type, bag shape, shoe shape, jewelry set, hairstyle, hair color, skin tone, body type, and background palette across every image. Any drift is a failure.
- Keep the same age read across every image. If the face or styling starts reading older, sharper, heavier, or more mature in one image, regenerate it.
- Treat skin, face, hands, and feet as quality-critical: ask for natural skin texture, gentle healthy sheen, soft blush or warm complexion, realistic nail shape, believable toe spacing, clean ankle and foot contours, and no waxy or over-smoothed rendering.
- Treat lighting as quality-critical: prefer soft window light, diffused daylight, open shade, or gently bounced indoor light. Avoid harsh overhead light, blown highlights, hard flash, glare, and eye-squinting sunlight.
- The detail image must preserve the full body or nearly full body unless the user explicitly requests a crop. Never let the head, feet, or major garment parts disappear from the frame by accident; leave visible breathing room around the head, hands, shoes, and bag.
- Avoid medical, body-shaming, deceptive slimming claims, or advice that implies a body type is wrong.
- If brands are not provided, describe item types and materials instead of inventing specific brand names.

## Visual QA Checklist

Before final response, confirm:

- 标题 exists.
- 标题 is 20 Chinese characters or fewer.
- 标题 uses Chinese only, with no English letters or Chinese-English mixed fashion terms.
- 封面 exists and is clearly identified.
- If a supporting image set was requested, each outfit has exactly 3 generated images.
- Images are vertical 3:4 unless the user requested another ratio.
- The same outfit components appear consistently across all images.
- The same person is clearly the same person across all images: same hairstyle, hair part, hair length, hair color, complexion, facial structure, body height impression, and body silhouette.
- The same age read is preserved across all images: youthfulness, softness, makeup density, and facial sharpness must stay aligned.
- The same scene family appears across all images: same room palette, same furniture language, same lighting direction, and same overall spatial feeling.
- Person-containing images in the same outfit work have visibly different poses or camera angles; the detail/atmosphere image must not look like a near-duplicate of the cover/full-body image.
- Fabric textures are clear: lace, denim twill, rib knit, linen weave, silk/satin sheen, leather grain, suede nap, hardware, stitching, and seams are plausible.
- Full-body photos show realistic anatomy, hands, feet, face/phone-mirror occlusion, pose, reflection, scale, garment fit, and natural skin finish.
- Flat lay photos show complete outfit inventory with believable garment shape, folds, shadow, and accessories.
- Detail photos genuinely reveal texture or styling detail while still keeping the model coherent in frame; do not crop away the head or feet by accident, and keep shoes/toes away from the image edge.
- The style is photorealistic, bright, social-platform ready, and free of watermarks, logos, QR codes, garbled text, duplicated limbs, warped garments, plastic fabric, and painterly illustration artifacts.
- 正文 is 100 Chinese characters or fewer, Chinese-only, uses Chinese-only hashtags, and is ready to publish.
