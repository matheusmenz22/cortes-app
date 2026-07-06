# Spec — Render 9:16 (layout, trim, overlays, encode)

**ESCOPO:** comportamento do render vertical do pipeline CLIPES (em produção, Tibia) para replicação no cortes-app (Matheus, LoL). Cobre: detecção de webcam, detecção de ação/trim, escolha de layout, overlays, gate de áudio e encode — com valores calibrados e o porquê. NÃO cobre: discovery, caption/IA, upload, esteira de aprovação, infra. Ducking de música: ver `skills/ducking-musica-voz.md`. Borda neon + logo: ver `skills/borda-neon-logo.md`.

## 1. Detecção de webcam (decide o layout)

Detector: OpenCV DNN **res10 SSD (Caffe)** — `readNetFromCaffe(deploy.prototxt, res10.caffemodel)`.
**NÃO usar Haar:** falso-positiva em textura/pixel art (sprite de Tibia virava "rosto" → split quebrado). Risco existe em qualquer jogo com arte estilizada.
**Pin `opencv-python-headless>=4.9,<5`:** OpenCV 5.x removeu `readNetFromCaffe` — venv novo morre no import (bug pago 06/07). Migração futura: res10 em ONNX + `readNetFromONNX`.

Amostra **24 frames** espaçados no clip. Aceita webcam se TODOS os critérios passam:
- **Confiança >= 0.45.** 0.6 perdia webcam REAL (rosto pequeno/mal iluminado no canto: 3/24 frames detectados @0.6 vs 17/24 @0.45 → caía em gameplay-only com crop quebrado). O 0.45 só é seguro por causa da trava de canto abaixo.
- **Altura do rosto >= 7% da altura do frame** (MIN_FACE_FRAC 0.07): webcam tem rosto grande; sprite é minúsculo. Mata falso-positivo residual.
- **Estabilidade >= 0.6** dos frames amostrados (rosto presente em >=60% deles). Caixa final = mediana das caixas (robusto a outlier).
- **Trava de canto:** centro do rosto (mediana) precisa estar perto de uma borda — `x_frac < 0.34` ou `> 0.66`, OU `y_frac < 0.30` ou `> 0.70`. Webcam senta em borda/canto; "rosto" no centro do frame é efeito/sprite do jogo → trata como sem webcam.

Caixa da webcam = rosto expandido **2.4x em largura, 2.6x em altura** (rosto → moldura da cam com ombros/fundo), clampada no frame. Sem webcam válida → layout B (gameplay-only).

## 2. Detecção de ação (movimento) → crop + trim

Uma passada low-res no clip inteiro: reescala p/ 256px de largura, grayscale, ~20 amostras/s, `absdiff` entre frames **consecutivos** amostrados (amostragem esparsa demais pega troca de cena e "ilumina" o frame todo). O mesmo sinal responde ONDE (espaço) e QUANDO (tempo).

**Espacial (onde croppar):** acumula os diffs num mapa, blur gaussiano (sigma 4), e usa o **extent do movimento forte**: nos perfis de coluna/linha, threshold em `0.25 * max`; centro = ponto médio entre a 1ª e a última posição acima do threshold. POR QUE extent e não centroide-de-massa: centroide é puxado por sangue/spell assimétrico; center-crop cego erra porque o mundo do jogo não fica no centro (Tibia: mundo à esquerda, UI à direita — verificar onde o LoL concentra ação vs HUD). O 0.25 deixa a UI lateral (movimento fraco) fora do extent.

**Temporal (trim):** sinal de movimento por amostra, suavizado com média móvel de ~0.5s. Dois limiares sobre o pico:
- **Início: `action_thr = 0.35` do pico** — onde a ação COMEÇA de verdade (pula intro morta: streamer se posicionando). Começa `action_lead = 0.4s` antes (cold open com um respiro mínimo, sem devolver a intro).
- **Fim: 0.12 do pico** (fixo, baixo de propósito) — clip de Twitch é retroativo: o payoff (kill/loot) fica perto do FIM e pode ser mais quieto que o auge do combate. Limiar alto no fim cortaria o payoff. Fecha `action_tail = 1.2s` depois (payoff assenta; corta cauda AFK/menu).

**Teto: `clip_max = 14s`, cortando da FRENTE** (preserva o fim = payoff). Dado (analytics 28d, n=72, confound de título controlado): clips <=14s = mediana 1165 views / 55% retenção vs >=20s = 970 / 46%. **AVISO: medido em Tibia** (mundo anima constante → janela quase nunca cai sozinha; 37/72 batiam no cap antigo de 25s). Validar o teto no nicho antes de assumir — LoL tem picos mais discretos (teamfight vs lane). Piso: `dur_min = 8s` (Short curto demais não segura). Sem movimento nenhum → clip inteiro, sem trim.

## 3. Layouts

Saída sempre **1080x1920**. Escala com `force_original_aspect_ratio=increase` + crop final (preenche o painel sem barra) e `flags=lanczos`.

**A) SPLIT (webcam detectada):** vstack de dois painéis.
- Painel webcam: **768px de altura (40%)** — cam é contexto/reação, gameplay é o conteúdo (60% = 1152px). Crop da CamBox → scale increase → crop no painel.
- Painel gameplay: crop no source com aspect `1080/1152` (~0.94, quase quadrado) centrado no centro da ação, com **`split_zoom = 1.6`**: o painel largo geraria corte largo demais e a ação ficaria "longe"; zoom 1.6 corta menos área = imagem mais perto.
- **`cam_pos = vary`:** alterna cam topo/base ~50/50, **determinístico por hash do clip_id** — estável por clip (re-render dá o mesmo layout) e o sorteio não correlaciona com outros sorteios do pipeline (usar salt próprio). Por que: 100% das cams no topo deixa o feed monótono.
- Risco conhecido (bug aberto no CLIPES): o painel de gameplay é crop geométrico cego — overlay grande do streamer (QR code, alertas) ENTRE cam e jogo entra no painel e inutiliza o corte. Mitigação barata: medir movimento só dentro do retângulo de gameplay previsto; painel estático → cair pra gameplay-only.

**B) GAMEPLAY-ONLY (sem webcam):** crop 9:16 (`1080/1920 = 0.5625`) no source, centrado no centro da ação — nunca center-crop cego. Scale increase + crop p/ 1080x1920.

**Override manual:** ambos aceitam `crop_box` (px do source) desenhado por humano na esteira — caixa de gameplay com aspect travado no painel de destino; caixa de webcam livre (o render preenche o painel). O crop manual sempre vence o automático.

## 4. Overlays (posições calibradas em 1080x1920)

- **Watermark:** texto pequeno, canto **superior-esquerdo** (x=28, y=28), fontsize 34, alpha ~0.22 + sombra. **NUNCA central:** branding no centro tapava o combate (centro do viewport) e sangrou retenção — em canal pequeno, retenção > branding.
- **Atribuição `@streamer` (Twitch):** rodapé centrado, y = `h-72`, fontsize 34, branco com borda preta. Obrigatório (é repost).
- **Botão INSCREVA-SE:** PNG estilizado (pílula vermelha + badge play), centrado horizontal, y com bounce senoidal leve (`+-10px`, período 1.1s). **Só nos ÚLTIMOS segundos:** janela de ~3.8s terminando 0.6s antes do fim (`cta_end = dur - 0.6`, `cta_start = cta_end - 3.8`). Por que: pedir sub durante o pico de retenção rouba atenção do momento; depois do clímax o espectador já decidiu se gostou.
- **Frase editorial queimada: DESLIGADA** (default off desde 18/06). A frase afirma algo ("Escapou por um triz!") que o público contesta → briga no comentário, não retenção — e o dado mostrou que retenção quase não move views (corr 0.19). Título/descrição continuam existindo como metadata; só o burn-in sai.
- Textos via `drawtext` com `textfile=` (não `text=` — escapar título com aspas/`:`/emoji no filtro é loteria). Fonte bold do sistema (Arial no Windows, DejaVu Bold no Linux).
- **Build do ffmpeg importa:** `ffmpeg-free` (RHEL/Rocky) e o static johnvansickle NÃO têm `drawtext` (e o free nem libx264). Validar capacidade real no setup: `ffmpeg -filters | grep drawtext`. Build BtbN gpl resolve.

## 5. Gate de áudio (antes de renderizar)

Twitch muta clip na ORIGEM (Audible Magic sobre música protegida): ~1/3 dos clips de Tibia chegam com stream aac presente mas silêncio digital. Sem gate, sobe Short mudo.

- Medir `mean_volume` **do TRECHO trimado** (não do clip inteiro — o mute pode ser parcial): `ffmpeg -ss START -t DUR -i clip -af volumedetect -f null -`.
- **Mudo se `mean_volume < -50 dB`.** Threshold validado com gap largo: mudos medem -91/-80/-52; com som, -26/-28. Sem stream de áudio, ou volumedetect sem retorno → tratar como mudo.
- Clip mudo NÃO é descartado às cegas: pode ser salvo com **música em volume cheio como trilha** (`music_full` — a música VIRA o áudio, ignorando o silêncio digital do clip). Clip com som usa música duckada por baixo da voz/SFX — receita completa em `skills/ducking-musica-voz.md`. Trilha: só faixa CC0/royalty-free local; rotacionar por hash do clip_id p/ variar entre Shorts; pasta vazia = roda sem música, sem erro.

## 6. Encode

```
ffmpeg -y [-ss START] [-t DUR] -i clip [PNGs...] [-stream_loop -1 -t DUR -i musica] \
  -filter_complex "<layout+overlays>[outv];<audio>[aout]" \
  -map "[outv]" -map "[aout]" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart out.mp4
```

- **Trim como opção de INPUT (`-ss`/`-t` ANTES do `-i` do clip):** seek preciso E o timeline zera → `enable='between(t,a,b)'` dos overlays (CTA) bate com a duração nova. Trim de output quebraria os timestamps dos enable. PNGs e música entram DEPOIS, não são cortados; música é o ÚLTIMO input (`-stream_loop -1` + `-t DUR` casa com o clip; `-shortest` é frágil com loop infinito).
- **`-crf 18 -preset slow`:** master pro YouTube — CRF menor = mais qualidade (YouTube recomprime; mandar master bom); preset lento = melhor compressão no mesmo CRF. **Draft/preview: `ultrafast` CRF 28`** (iteração rápida na esteira).
- **`yuv420p`** obrigatório (compatibilidade de player).
- **SEM `-r` fixo:** preserva o fps da fonte — clip 60fps sai 60fps (fluidez é parte do apelo de gameplay). Forçar 30 joga qualidade fora.
- **`loudnorm=I=-14:TP=-1:LRA=11`** no fim da cadeia de áudio (alvo do YouTube; nivela clips de origem díspar).
- **`+faststart`** (moov no início).
- Preview em browser: fonte da Twitch pode vir **HEVC 1440p** — `<video>` não decodifica sem licença (frame preto, áudio ok) embora o ffmpeg renderize normal. Se `vcodec != h264`, gerar proxy h264 720p só pro preview; o render usa sempre o source original.

## 7. Identidade visual

Borda neon na cor do canal + logo topo-centro: ver `skills/borda-neon-logo.md`. Regra que se repete em tudo: **o centro do frame é sagrado** — branding só em borda/canto.
