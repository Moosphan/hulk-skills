---
name: daily-recipe-social-post
description: Use when the user wants a 每日菜谱推荐, 小红书 or 抖音 food post, single-dish or multi-dish meal idea, 菜品封面, 菜谱图, 摆盘预览图, or a short Chinese cooking workflow caption for social publishing.
---

# Daily Recipe Social Post

## Overview

Create one social-ready daily recipe recommendation for Xiaohongshu or Douyin. Each work includes a title, cover images, and a cooking-process body within 500 Chinese characters. Default to a single-dish work unless the user asks for a specific dish count or multiple dishes.

**REQUIRED SUB-SKILL:** Use `baoyu-imagine` when generating cover images.

## Workflow

1. Parse the user request for platform, meal occasion, dietary limits, cuisine preference, cooking difficulty, number of dishes, specific dish names, and output directory.
2. Build a recipe fact sheet for every dish before drafting captions or image prompts. It must list every ingredient, seasoning, garnish, marinade component, cooking liquid, and finishing oil, with its exact preparation form and amount when known.
3. Choose dishes from the parsed request:
   - If no dish count or dish names are specified, choose 1 visually strong home-style dish.
   - If the user specifies a dish count in natural language, generate that many dishes.
   - If the user gives dish names, use those dishes; if the user gives one dish and asks for multiple dishes, choose complementary dishes for the rest.
   - For 2+ dishes, pair dishes by color, texture, and effort. Prefer seasonal, easy-to-cook combinations.
4. Produce the work in this order:
   1. 标题
   2. 封面图
   3. 制作流程正文
5. For the covers, create prompt files and run `baoyu-imagine` batch generation unless the user only asks for copywriting.
6. Verify generated image files exist, are valid PNG/JPG files, match the requested orientation, and pass the Recipe Integrity Checklist below.

## Output Contract

### 1. 标题

Write 1 concise Chinese title suitable for Xiaohongshu and Douyin. Make it specific, appetizing, and natural, such as:

`今天晚餐就吃这两道：下饭不费劲`

Avoid clickbait, exaggerated health claims, and awkward keyword stuffing.

For visible dish names on covers, use the dish naming rules below.

### 2. 封面图

Cover count depends on the dish count:

- Single-dish work (default): exactly 2 cover images.
  1. `菜品预览摆盘图`: one finished dish plated as a publishable promotional meal image.
  2. `菜谱详情图`: recipe poster for that dish with finished dish, ingredients, steps, tips, and calories.
- Multi-dish work: exactly `dish_count + 1` cover images.
  1. `菜品预览摆盘图`: all dishes plated together as one meal set.
  2. One `菜谱详情图` per dish, ordered by the dish list.

Before writing cover prompts, read `references/cover-style.md`. The covers must use 明亮浅色 and a cute, rounded Chinese handwritten typeface for every visible Chinese text element. 不要使用暗色系.

Recommended filenames:

- `outputs/<slug>-plating-preview.png`
- `outputs/<slug>-<dish-slug>-recipe.png`

Use 3:4 for the plating preview and 3:4 for recipe posters unless the user requests another ratio.

Every recipe poster must include a visible calories badge or strip, such as `约320 kcal/份`. Treat calories as a practical estimate, not a health claim.

### 3. 制作流程正文

Write the post body in Chinese, 500字以内. Include:

- a warm opening sentence
- ingredients summary for every dish
- short cooking sequence for every dish
- one practical tip
- optional hashtags for Xiaohongshu or Douyin

Keep the body publishable as-is. Do not include image-generation prompt text in the final social caption.

## Dish Recommendation Rules

- Pair dishes by color, texture, and effort: avoid two dishes that are both saucy, both fried-heavy, or visually similar.
- Prefer common ingredients and family-kitchen methods: stir-fry, braise, steam, simple pan-fry.
- For weekday recommendations, keep total active cooking time under 40 minutes unless the user asks for a bigger meal.
- Default to 1 dish when the user does not specify dish count.
- If the user gives one dish and asks for a 1-dish work, do not add a second dish.
- If the user gives one dish and asks for 2+ dishes, choose additional dishes that balance it.
- If the user gives multiple dishes, use the first two unless they ask for more.

## Dish Naming Rules

Apply these rules to dish names shown on cover images, especially handwritten labels and recipe-poster titles:

- Use standardized dish-style names that sound like real menu items, usually `flavor or cooking method + main ingredient`, such as `蒜香鸡腿排`, `黑椒牛肉炒彩椒`, `柠檬香草煎鳕鱼`, `番茄虾仁滑蛋`, `青椒肉丝`.
- Do not make the visible dish name end with serving-container or meal-format words such as `碗`, `盘`, `餐盒`, `便当`, `套餐`, `拼盘`, or `组合`, unless the user explicitly provides an established dish name that naturally ends that way.
- If the work is a bowl, plate, lunch box, or meal set, describe that format in the social title, body, or prompt scene, but keep the cover dish name itself as a proper dish name. For example, use `蒜香鸡腿排` on the cover instead of `蒜香鸡腿排南瓜糙米碗`.
- Use the same standardized dish name consistently across the social title, cover prompts, handwritten cover labels, recipe-poster title, recipe steps, filenames, and final checklist.

## Image Realism Rules

### Existing-Design Regeneration Lock

- When regenerating or correcting an existing recipe poster, treat the supplied poster as a hard visual-layout reference. Preserve its canvas ratio, palette, paper/card treatment, border, typography character, section order, panel count, spacing, and visual hierarchy. Do not convert it into a new scrapbook, editorial, full-bleed, dark, or alternate design style unless the user explicitly requests a redesign.
- Make the smallest visual change that fixes the reported food defect. Keep all non-food graphic elements, labels, decorative marks, and section geometry stable; do not replace a cute handwritten recipe-card style with brush calligraphy or a different type system.
- Use a dish identity sheet as the cross-image source of truth: exact protein cut, pepper variety, cut direction, stem/tip morphology, cooked color, garnish, vessel, and serving arrangement. Reuse this identity sheet in every cover, ingredient page, process page, and final plating panel.
- The final plated panel in a process poster must match the hero plated image in the same work: same dish, ingredient varieties, cut sizes, relative color proportions, garnish, bowl or plate, serving direction, and sauce/oil appearance. Do not introduce new herbs, alternate pepper shapes, different meat slices, or a different vessel at the last step.
- For local correction, preserve correct existing food details as well as the design. Repair only malformed edges, duplicate stems, melted or blurry ingredients, impossible cut states, and cross-panel mismatches; do not restyle or recompose the whole poster.

- Keep ingredients visually faithful to the dish name and recipe. If the dish says `大虾`, `整虾`, `带头虾`, or relies on shrimp head oil, show whole shrimp with heads and shells where appropriate. Use peeled shrimp only when the dish says `虾仁`.
- Make step panels match the recipe sequence and the final dish. Do not invent fake ingredients, impossible textures, or decorative substitutes.
- State the exact ingredient form in prompts: whole shrimp vs peeled shrimp, bone-in ribs vs boneless meat, sliced fish vs cubes, raw vs cooked stage.
- Ask for realistic home-kitchen food photography in every prompt: natural textures, correct scale, plausible cookware, no plastic-looking food, no duplicated or malformed ingredients.

## Ingredient-Step Consistency

Treat the recipe fact sheet as the source of truth for both the written recipe and the image prompt.

- Every ingredient, seasoning, garnish, and cooking liquid used in a visible step or its instruction must be listed in `食材准备`. Ingredient cards may combine related items only when their label names every component in the group; never omit an active ingredient merely because the layout is compact. Marinade components are included in that requirement too.
- Specify the preparation state of every ingredient in both the instruction and the corresponding panel: whole, deboned, sliced, minced, julienned, washed, marinated, blanched, fried, simmered, or plated. An image panel must depict only the exact state required by its step.
- No whole, intact ingredient may appear in a step that calls for a cut, deboned, separated, cooked, or leftover part. Likewise, do not show a finished ingredient before it has been prepared in the sequence. This applies generally, not only to fish.
- When a recipe uses a by-product, list it explicitly and prompt it precisely. For example, if broth uses fish head and bones after filleting, the ingredient section must include `鱼头鱼骨`, and that panel must show only the head and clean fish skeleton, never an intact whole fish or raw fillets.
- Use concrete food-identifying details for easily confused ingredients. For example, bean sprouts are pale ivory stems with small yellow heads and should never resemble shredded cheese, noodles, or generic strips; minced garlic must look like small off-white irregular pieces, not grains or a cream sauce.
- A step panel must show the correct tools, vessel, quantity, and cause-and-effect for the action: blanching uses boiling water and a drained result, pan-frying uses a shallow pan and browned contact edges, simmering uses a pot of broth, and pouring hot oil shows only the finished topping being sizzled.
- Do not compress a complex recipe into fewer panels if that would hide a transformation essential to taste, food safety, or visual plausibility. Use 4-6 panels by default and add panels when needed, while keeping all panels visible and readable.
- Recipe poster step panels must use consecutive step numbers with no missing or skipped numbers. If there are 6 panels, labels must be `1-6`; if there are 7 panels, labels must be `1-7`. Do not duplicate, omit, or jump numbers.
- Any time-sensitive cooking step must show a specific duration in the visible step note. This applies to steaming, roasting, baking, air-frying, simmering, braising, boiling, blanching, pan-frying to doneness, resting, marinating, and reducing sauce. Write concrete times such as `蒸8分钟`, `焖12分钟`, `烤18分钟`, `小火炖45分钟`, or `腌10分钟`; do not write vague notes like `蒸熟`, `煮熟`, `烤至熟`, `焖一会儿`, or `适量时间`.

## Typography Rules

- Every visible text element, including the title, section headers, ingredient-card labels, step titles, step notes, tip strip, and calories badge, must use one consistent cute, rounded Chinese handwritten typeface. It should feel like a warm hand-written recipe notebook: soft strokes, lively but legible, never a printed serif, sans-serif, brush-calligraphy display face, or mixed-font collage.
- State this typography requirement directly in every image prompt. Require simplified Chinese, high legibility, stable line spacing, and no gibberish, distorted characters, or unexpected Latin text except `kcal` in the calorie badge.
- For recipe posters, keep visible text short and spacious enough to read. Use compact ingredient labels and one-sentence step notes; do not shrink text into cramped, distorted, or garbled micro-writing to fit extra content. If the recipe needs more explanation, add another step panel or simplify the visible note while keeping the full recipe fact sheet accurate.

## Cooked Food Realism Rules

Apply these rules to all finished-dish cover prompts and recipe-poster step panels:

- Covers must express `色香味俱全`: balanced appetizing color contrast, visible steam or aroma cues, natural glossy sauce or oil sheen, clearly tender/juicy textures, and a composed serving scene that makes the dish look freshly cooked and desirable.
- Promotional plating covers must show appetizing color-aroma-flavor depth: layered natural color contrast, light steam, sauce cling, oil gloss, moist cut surfaces, crisp/tender cues, and a clean table scene that makes the dish look freshly cooked, fragrant, and publishable.
- Cooked staple foods must look naturally cooked, moist, and edible. For steamed white rice, brown rice, quinoa, noodles, porridge, or rice bowls, describe the exact cooked texture instead of only naming the ingredient.
- Rice realism is critical: cooked rice should show soft, slightly translucent grains with subtle clumping from starch and moisture, varied grain sizes, and gentle surface shine. Do not make rice look like oversized hard pellets, plastic beads, corn kernels, gravel, dry cereal, or perfectly separated decorative dots.
- Brown rice and mixed grains may show more texture than white rice, but they still need cooked softness, light moisture, and natural clumps; avoid exaggerated coarse particle texture.
- Cooked meats, fish, eggs, tofu, and vegetables must show plausible doneness cues: seared edges, steam, sauce cling, juicy cut surfaces, softened vegetables, glossy cooked egg curds, tender fish flakes, or browned tofu edges as appropriate.
- For thin-sliced pork and other sliced meats, preserve the real cut and cooking behavior: pieces vary naturally in length, width, thickness, curl, and fat-to-lean pattern; rendered fat is lightly translucent and glossy, lean is plump and tender, and a few edges may gently wave or curl. Do not depict dry, shrunken, uniformly cut rectangles, identical meat tiles, thick cubes, rigid slices, or brittle-looking lean meat. State these cut, moisture, and fat-rendering details directly in every relevant prompt and inspect them during visual QA.
- When a recipe names a pepper variety, specify its specimen-level morphology, cut and cooked state instead of prompting a generic pepper. For example, 螺丝椒 is a slender, unevenly twisted deep-green chili with clear longitudinal wrinkles, thin walls and a tapered tip; after stir-frying it becomes glossy and lightly blistered while retaining irregular folded segments. 小米椒 is a small, narrow, pointed bright-red chili, not a thick red bell pepper or chunky generic ring. Do not substitute smooth generic green peppers, jalapenos, bell peppers, uniform plastic tubes, or a different chili variety; use the same named pepper in ingredient cards, preparation panels and finished dishes.
- Finished dishes should feel freshly cooked and appetizing: visible heat, light steam, natural oil or sauce sheen, realistic scale, and home-kitchen cooking marks. Avoid over-sharpened texture, raw-looking cooked food, waxy surfaces, rubbery meat, plastic vegetables, and artificial food-model gloss.
- Ingredient close-ups in recipe posters must distinguish raw and cooked stages clearly. Raw-stage panels may show raw rice, raw meat, or raw vegetables; finished-dish and plated panels must show cooked texture.
- For ingredient cards, use recognizably real food specimens in a small bowl or on a prep plate, with natural variation in size, moisture, color, and cut shape. Do not use abstract ingredient icons or generic substitute shapes.

## Texture Artifact Control

- All key food surfaces must be smooth, polished, and free of jagged speckled artifacts. This applies especially to eggplant skins and flesh, diced or sliced meat, peanuts, mushrooms, tofu, rice, sauce surfaces, and small garnish pieces.
- Prompt against AI-looking texture failures: jagged saw-tooth edges, pixelated boundaries, gritty speckles, random black or white spots, pitted or diseased-looking surfaces, repetitive seed-like dots, lumpy plastic blobs, melted wax texture, over-sharpened crunchy noise, and broken geometry.
- Describe expected micro-texture for fragile ingredients: eggplant should have smooth glossy purple skin and soft creamy cooked flesh; diced chicken should have rounded browned edges and juicy coated surfaces; braised beef should show tender fibers and rounded softened edges; peanuts should be oval, whole, lightly wrinkled, and evenly roasted without bumps or spots; shiitake mushrooms should have smooth brown caps and pale gills.
- Plating covers and recipe posters must include this artifact-control requirement in every prompt, not only in the skill reference. If visual QA finds jagged spots, gritty speckling, unnatural pitting, weak appetizing presentation, or cramped/gibberish text, regenerate the affected image with stronger texture, sensory, or typography constraints.

## Visual QA and Regeneration

- Inspect generated covers before delivery. If an ingredient is visually confused with another food, a step panel shows the wrong preparation state, required ingredients are omitted, or text falls back to printed/mixed fonts, revise the prompt and regenerate the affected image instead of accepting it.
- For visually fragile ingredients, add specimen-level details in the prompt. For example, soybean sprouts should appear as separate whole sprouts with slender ivory stems and attached round yellow bean heads; minced garlic should appear as uneven tiny off-white chopped pieces with sharp cut edges.

## 输出清单

Before final response, confirm:

- 标题 exists.
- Required covers exist: 菜品预览摆盘图 plus one 菜谱详情图 per dish.
- 制作流程正文 is 500字以内.
- Cover style is 明亮浅色, 中文手写体, and not dark.
- 菜品预览摆盘图 and all 菜谱详情图 use 3:4 unless the user requested another ratio.
- Every recipe poster prompt includes calories.
- Cover-visible dish names are standardized dish names and do not end with container or meal-format words like `碗`, `盘`, `餐盒`, `便当`, `套餐`, `拼盘`, or `组合`, unless explicitly requested.
- Prompts preserve ingredient realism and exact ingredient form.
- Prompts specify cooked-food realism, especially realistic cooked rice texture when rice appears: soft moist grains, subtle starch clumping, natural grain scale, not hard pellets or plastic beads.
- Every visible text element uses a consistent cute, rounded Chinese handwritten typeface, including small ingredient and step labels.
- Recipe-poster text is legible, spacious, simplified Chinese, and not cramped, distorted, or garbled.
- Step-panel numbers are consecutive with no missing or skipped numbers.
- Every time-sensitive cooking step includes a specific duration, especially steaming fish, steaming ribs, roasting, baking, simmering, braising, boiling, blanching, marinating, or resting steps.
- Recipe poster ingredient cards account for every ingredient, seasoning, garnish, marinade component, cooking liquid, and finishing oil referenced by its step text.
- Every step panel is state-accurate and causal: it shows only the ingredient form, cookware, and result appropriate to that point in the recipe, without whole-vs-cut, raw-vs-cooked, or earlier-vs-later stage contradictions.
- Key food surfaces are smooth, polished, and free of jagged speckled artifacts; covers show appetizing color, aroma cues, and glossy fresh-cooked texture.
- Generated files were verified on disk when image generation was requested.
