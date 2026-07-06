# Skill: identidade visual do corte — borda neon + logo do canal

ESCOPO: qualquer Short/corte vertical. Objetivo: o vídeo ser reconhecível como
SEU no feed (borda na cor do canal) sem roubar atenção do conteúdo.
Em produção nos canais de LoL desde 06/07/2026.

## Princípio (pago com views)

**Bordas sim, centro NUNCA.** Watermark/branding no centro do frame cobre a
ação e derruba retenção (medido: watermark central foi removida por isso).
Tudo de identidade mora nas bordas: moldura, logo pequeno no topo, atribuição
no rodapé.

## Sistema de cor por canal

1 cor por canal, usada em TUDO: borda do vídeo, identidade do painel interno,
thumb/avatar. Ex: canal PT azul `3B82F6`, canal EN roxo `A855F7`, canal Tibia
verde. A cor vira assinatura — espectador reconhece o canal antes de ler o nome.

## Borda neon ("plasma" estático) — receita ffmpeg

Duas `drawbox` empilhadas = traço firme + halo que esmaece pra dentro.
Custo de render ~zero (sem animação; plasma animado custa CPU e não agrega em
tela de celular).

```
drawbox=x=0:y=0:w=iw:h=ih:color=0x{COR}@0.4:t=32,
drawbox=x=0:y=0:w=iw:h=ih:color=0x{COR}@1:t=14
```

- Em 1080x1920: 14px sólido + 32px de halo ≈ 1,3% da largura por lado —
  visível no feed, invisível pro conteúdo. Testado: 7px é tímido demais.
- Aplicar como ÚLTIMO estágio do filtro de vídeo (por cima de tudo, antes só
  do logo).
- Cor via config/env (`BORDER_COLOR=3B82F6`) — trocar canal = trocar 1 valor.

## Logo do canal (topo-centro, pequeno)

PNG do avatar sobreposto no topo-centro, MORDENDO a borda (metade no halo,
metade no conteúdo) — vira crachá:

```
[LOGO:v]scale=96:-1[lgo];[video][lgo]overlay=x=(W-w)/2:y=18
```

- 96px em 1080 de largura. Não maior: em layout com webcam no topo o logo
  invade a testa do streamer.
- Aplicar DEPOIS da borda (logo por cima do halo).
- Gotcha ffmpeg: logo é um INPUT a mais — se a música/CTA também são inputs,
  recalcular os índices `[N:v]`/`[N:a]` (bug clássico de filtro que "funcionava
  antes do input novo").

## Retrofit: aplicar em vídeo JÁ renderizado (fila pendente)

Não precisa re-renderizar do source — pós-processo direto no mp4 final:

```
ffmpeg -i final.mp4 -vf "<drawbox...>[,overlay do logo]" \
  -c:v libx264 -preset veryfast -crf 18 -c:a copy -movflags +faststart tmp.mp4
mv tmp.mp4 final.mp4   # troca atômica
```

`-c:a copy` = áudio intacto; crf 18 = perda de geração desprezível. Validado:
32 clips em lote, zero falha. SÓ para vídeo ainda não publicado.

## Relacionado

- CLAUDE.md raiz → "Qualidade" (por que o centro é sagrado).
- `skills/ducking-musica-voz.md` (o outro pedaço do padrão de produção).
