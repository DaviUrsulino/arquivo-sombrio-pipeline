"""Master style lock atualizado em 2026-09-08 — validado visualmente via
Cloudflare Workers AI (ver runs/ e conversa com o Davi) contra referências
reais do canal "Contos Urbanos" (TikTok) e uma imagem de teste do irmão
do Davi. Texto baseado no prompt que o irmão dele já usa e comprovou
funcionar bem nesse estilo específico ("dark semi-realistic 2D cartoon").

Substituiu o estilo anterior ("2D horror animation, early 2000s") que era
mais flat/simples — este é mais denso (~150 palavras) de propósito, o
Cloudflare segue prompt longo e detalhado bem melhor que o fallback FLUX
(Modal/HF), que tende a perder elementos com prompt muito longo.

Não mexer no texto do estilo sem revalidar visualmente primeiro — qualquer
mudança pode quebrar a consistência de personagem entre cenas.
"""

MASTER_STYLE_LOCK = (
    "Dark semi-realistic 2D cartoon comic-book illustration, mature cinematic horror "
    "storytelling style. Strong bold hand-drawn black ink outlines, rough but controlled "
    "linework, slightly irregular contours, expressive facial features, subtly exaggerated "
    "anatomy. Characters look mature and believable, never childish or cute. Highly expressive "
    "faces with intense fear, anxiety, paranoia or tension. Large expressive eyes with clearly "
    "visible white sclera all around small dark pupils, strong eyebrows. Dark cinematic "
    "atmosphere, deep shadows, strong contrast, dramatic directional lighting. Predominantly "
    "dark muted color palette: deep navy blue, dark green, charcoal gray, muted brown, black — "
    "warm orange/yellow/red lighting only where naturally appropriate. Detailed, meaningful "
    "background with realistic objects and architecture, strong sense of depth (foreground/"
    "middle/background). Subtle vintage analog and printed-comic texture, slight film grain, "
    "subtle chromatic aberration. Detailed hand-painted 2D textures, rich shadows, textured "
    "clothing and skin, no glossy digital appearance. "
)

RESTRICOES = (
    "No gore, no blood, not photorealistic, not 3D, not anime, no text, no logos, no watermark."
)
