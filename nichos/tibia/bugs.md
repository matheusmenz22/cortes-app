# Tibia — bugs & soluções (anti-regressão)

Consultar ANTES de debugar. Formato: sintoma → causa → solução. Datas 2026.

## Short mudo (intermitente, ~1/3 dos clips)
**Sintoma:** vídeo sobe sem som; stream aac existe no container.
**Causa:** Twitch muta o trecho NA ORIGEM (Audible Magic, música protegida na
live). Re-download dá -91dB de novo.
**Solução:** gate de áudio pré-render: `mean_volume` do TRECHO usado < -50dB →
descarta ou salva com música CC0 em volume cheio. Threshold -50 validado
(mudos: -91/-80/-52; com som: -26/-28). (jun/2026)

## Detector de webcam falso-positivando
**Sintoma:** "webcam" detectada em cima de gameplay.
**Causa:** Haar cascade acha rosto em pixel-art de Tibia.
**Solução:** DNN res10 com confiança ≥0.45 + prior de canto. (jun/2026)

## Título/descrição sem relação com o vídeo
**Sintoma:** metadado gerado por LLM confabulado (título de live ≠ conteúdo).
**Causa:** gerar caption só com o TÍTULO do clip (pista fraca) — LLM inventa.
**Solução:** grounding multimodal: frames + áudio do TRECHO que vai ao ar,
prompt com regra de honestidade + proibição de copiar texto de UI. (12/06)

## Clip novo preto no browser (áudio ok)
**Causa:** Twitch passou a servir clip 1440p em HEVC; browser não decodifica.
**Solução:** proxy h264 720p só pra preview; render usa o source. (06/07)

## Pipeline para do nada, todos os downloads falham
**Causa:** yt-dlp velho (>3 meses) + Twitch mudou schema → `KeyError('data')`.
**Solução:** `pip install -U yt-dlp`. 1º suspeito quando render do dia = 0. (19/06)

## ffmpeg sem drawtext/x264 (Linux RHEL/Rocky)
**Causa:** `ffmpeg-free` da distro é build LGPL capado.
**Solução:** build BtbN gpl em /usr/local/bin; checar capacidade real
(`ffmpeg -filters | grep drawtext`), não só existência. (jun/2026)

## A/B de título medindo nada
**Sintoma:** braço "gemini" saía com título cru; nenhum erro no log.
**Causa:** flag global `title_raw` sobrescrevia o título gerado DEPOIS do
generate — override morava em outro arquivo (caption), não onde o A/B foi
escrito (run).
**Lição:** flag nova com precedência precisa ser aplicada em TODOS os pontos
que a flag antiga toca; validar A/B com 1 amostra real de CADA braço antes de
deixar rodando. (06/07)
