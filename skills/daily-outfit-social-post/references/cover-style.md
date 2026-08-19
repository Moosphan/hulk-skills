# Outfit Cover Style

Use this reference before writing prompts for daily outfit social-post images.

## Shared Style

- Overall mood: mainstream Xiaohongshu/Douyin daily outfit photography, clean but lived-in, bright natural daylight, soft neutral interiors or simple street scenes, high trust and low staging.
- Photographic realism is mandatory: DSLR or high-end phone camera feel, accurate lens perspective, natural depth of field, realistic shadows, no illustration, no CGI, no plastic skin, no waxy fabric.
- Continuity is mandatory: all images in one work must look like the same person, the same outfit, and the same scene family. Do not let the model, outfit, bag, shoes, jewelry, or background drift even slightly between images.
- Before writing prompts, freeze a continuity lock that names the exact hairstyle, hair part, hair color, complexion, age read, body type, height impression, top, bottom, shoes, bag, accessories, scene palette, and light direction. Copy that lock verbatim into every prompt.
- When using the established OOTD creator persona, read `persona-lock.md` and copy its Persistent Persona Lock into every person-containing prompt before the look-specific continuity lock. Use `../assets/model-identity/fullbody-anchor.png` and `../assets/model-identity/portrait-anchor.png` as the first references for the full-body anchor image whenever the provider supports references.
- Age-read consistency is part of identity consistency. Keep the model fresh, soft, and young-adult across the whole set; avoid one image becoming older, sharper, more formal, tired, or heavily made up.
- Skin realism matters: ask for gentle highlight rolloff on cheeks, collarbones, shins, ankles, and toes; a natural healthy complexion; clean but not airbrushed skin texture; soft gloss rather than shiny grease; and believable toenails and fingernails.
- Lighting matters: use soft window light, diffused daylight, open shade, or gently bounced indoor light. Avoid direct sun in face, harsh overhead light, blown highlights, flashlight glare, and sweaty specular hotspots.
- Material texture must be explicit in every prompt. Name the exact visible textures: lace scalloped edges, ribbed knit channels, soft cotton wrinkles, light-wash denim twill, frayed hem threads, linen slubs, satin sheen, leather grain, suede nap, metal buckle highlights, stitching, seams, buttons, and zipper teeth.
- Keep garment fit plausible: fabric follows gravity, folds at joints, waistbands sit correctly, straps connect to garments, hems and seams align, shoes fit both feet, bags hang with weight.
- Use stable color relationships: name each garment color and make colors consistent across all images in one work.
- Keep photos social-ready: vertical 3:4, crisp outfit visibility, uncluttered background, natural styling, no over-processed beauty filter, no fake magazine-gloss skin.
- Do not include visible text, labels, caption stickers, watermarks, QR codes, account names, or platform UI by default. Outfit photos should look like real camera photos, with title and caption supplied outside the image.
- Use tasteful, non-sexualized posing. The outfit may be feminine, fitted, or summer-light, but the prompt should frame it as everyday styling, not lingerie or boudoir content.
- In one outfit work, every person-containing image should have a planned pose difference. The cover/full-body and detail/atmosphere images must not repeat the same front-facing standing pose; vary at least two of body angle, head direction, hand placement, bag position, walking/standing action, camera distance, or shooting angle.
- Avoid visible brand logos unless the user supplies them. Never invent watermarks, account names, QR codes, platform UI, price tags, promotional labels, or decorative text.
- Avoid dark nightclub, runway, fantasy editorial, anime, plastic mannequin, ecommerce cutout, catalog-white void, or overly staged studio mood unless requested.

## 搭配平铺图

Purpose: show the full outfit inventory before wearing.

Prompt requirements:

- Vertical 3:4, top-down or slightly angled flat lay.
- Show every item in the outfit fact sheet: top, bottom or one-piece, shoes, bag, jewelry, hair accessory, sunglasses, belt, socks, or outerwear if included.
- Use a bed sheet, pale rug, light wood table, or warm ivory cloth with natural wrinkles and soft daylight.
- Keep the environment palette and props aligned with the other images in the set so the flat lay still feels like the same work.
- Arrange items with real scale and spacing. Clothing should have believable folds, seams, hems, closures, and fabric thickness.
- Accessories should not float or merge into clothing. Shoes should appear as a matched pair, correctly oriented.
- No human body parts unless intentionally styling a hand placing one item; if hands appear, keep them natural and secondary.

## 上身全身图

Purpose: prove the outfit works when worn.

Prompt requirements:

- Vertical 3:4 full-body image, head-to-toe framing with shoes visible.
- Use a realistic adult model, mirror selfie, apartment hallway, fitting-room mirror, elevator lobby, cafe exterior, sidewalk, or clean bedroom depending on the style.
- Prefer the full-body image as the anchor image for continuity. After it is generated, lock its observed identity details and reuse them for the other images.
- The same outfit components from the flat lay must appear. Keep garment color, material, fit, neckline, hem length, shoes, and accessories consistent.
- Use natural body proportions and a plausible pose: standing, slight leg bend, hand in pocket, holding phone, walking step, or relaxed lean.
- If mirror selfie, include realistic mirror edge, phone partially covering the face when appropriate, correct reflection geometry, and no duplicate bodies or impossible room reflections.
- Avoid malformed hands, extra fingers, crossed reflections, warped feet, missing shoes, impossible legs, floating accessories, and clothing that clips through the body.

## 封面

Purpose: provide the single strongest publishable cover for the work.

Prompt requirements:

- Default to a vertical 3:4 full-body or nearly full-body OOTD photo unless the user asks for a square cover.
- Show face, hairstyle, outfit silhouette, shoes, bag, and the key mood within the first glance.
- The cover can be the approved full-body anchor image, or a separate cover generated from the approved full-body anchor.
- Leave clean margins around head, shoes, and bag for platform cropping.
- Do not add visible title text, stickers, account names, QR codes, platform UI, or watermarks unless explicitly requested.
- If the cover is generated separately, it must keep the same person, outfit, scene family, light direction, and age read as the full-body anchor.

## 细节氛围图

Purpose: make the post feel richer and reveal material quality.

Prompt requirements:

- Vertical 3:4 with the model kept coherent in frame. Prefer a full-body or nearly full-body pose that emphasizes detail; do not crop off the head, feet, or major garment parts unless the user explicitly asks for a crop. Leave comfortable margins around the head, hands, shoes, and bag so no toes, sandals, hair, or accessories touch the image edge.
- Highlight 2-4 specific details from the outfit fact sheet: lace trim, denim frayed hem, knit rib texture, sandal straps, buckle, pendant, ring, shoulder bag leather grain, sleeve cuff, layered waistband, or hair accessory.
- Keep the crop connected to the same outfit and scene; do not introduce a new look.
- Keep the same hairstyle, face shape, skin tone, body proportions, and scene palette as the anchor image. This image may emphasize detail, but it is not allowed to become a different person or a different outfit.
- Keep the same youthful age read as the anchor image. Do not make the detail image look older or more mature because of makeup, lighting, pose, or outfit styling.
- Make the pose visibly different from the cover/full-body image while preserving identity and outfit. Prefer a side step, gentle turn, seated edge pose, walking motion, looking down at fabric, adjusting a cuff, holding the bag across the body, or a slightly lower/higher camera angle. Avoid producing a near-duplicate of the cover pose.
- Include tactile realism: visible woven fibers, seam stitching, soft creases, worn leather grain, natural skin texture, believable toe shape, and believable contact shadows.

## Prompt Checklist

Each prompt should state:

- exact image type: 搭配平铺图, 上身全身图, or 细节氛围图
- outfit title and platform context
- every visible clothing item, color, material, silhouette, fit, and accessory
- the chosen location, lighting, camera feel, and composition
- lighting should be soft, comfortable, and not glaring
- vertical 3:4 orientation
- material micro-texture and garment construction details
- consistency with the same outfit across the set
- pose plan and explicit pose difference from other person-containing images in the same set
- verbatim continuity lock copied into every prompt
- negative constraints against watermark, QR code, logo, platform UI, visible text, unreadable text, harsh glare, blown highlights, direct sun in face, older-looking face, tired expression, sharp mature makeup, heavy contour, cropped head, cropped toes, shoes touching the image edge, distorted hands, extra limbs, warped feet, incorrect reflections, duplicate bodies, plastic fabric, melted seams, painterly style, CGI, cartoon, over-smoothed skin, blurry textile details, and inconsistent garment colors
