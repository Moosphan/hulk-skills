# Fixed OOTD Creator Persona

Use this reference whenever the user wants ongoing OOTD works based on the established creator image, same-person continuity, or "继续用之前的人物".

## Reference Assets

Always pass these references to the first full-body anchor generation when provider reference images are supported:

- `assets/model-identity/fullbody-anchor.png`: body proportion, height impression, hairstyle length, everyday OOTD camera language.
- `assets/model-identity/portrait-anchor.png`: face shape, youthful age read, complexion, hairline, makeup mood.

Do not use a previously generated off-style, older-looking, heavily retouched, or failed image as the identity source.

## Persistent Persona Lock

Copy this lock into every full-body prompt and every human-containing cover/detail prompt:

Same young adult East Asian woman from the fixed OOTD creator identity references, fresh fair natural skin tone, soft youthful face, gentle clear eyes, natural dark eyebrows, long dark brown softly wavy hair with a center-left part, hair length below chest, slim natural body, about 165 cm height impression, clean feminine daily-fashion style, natural luminous skin with visible texture, soft blush, clear rose or nude lip tint, no heavy contour, no sharp mature makeup, no older age read, no different face shape, no changed hair color, no changed hair length, no changed body type.

## Continuity Method

1. Generate each look's full-body anchor first using both fixed identity references.
2. Inspect the full-body anchor before generating other images. Regenerate if the model looks older, unfamiliar, over-retouched, stiff, plastic, or if the hairstyle/skin/body proportions drift.
3. Use the approved full-body anchor as the reference for the cover, flat lay, and detail images in that same look.
4. For images with the person visible, include both the persistent persona lock and the look-specific outfit continuity lock.
5. For flat lays, reference the approved full-body anchor only to preserve exact clothing colors, materials, bag, shoes, and accessories. Do not ask for human body parts in flat lays.
6. Never mix identity references from a failed look or from a different generated character.

## Identity QA

Reject or regenerate any image if:

- The face reads older, sharper, tired, heavily made up, or celebrity-like.
- Hair becomes black, red, blonde, short, straight-only, curled too tightly, or a different parting.
- Skin tone changes noticeably warmer, darker, paler, waxier, or over-smoothed.
- Body height impression, shoulder width, waist/hip proportion, or leg proportion changes strongly.
- The image introduces a different face, different jawline, different eyes, different nose, or different mouth.
- The image looks like a polished AI beauty render rather than natural OOTD photography.
