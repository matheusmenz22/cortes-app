# Spec: experimento A/B de título (LLM vs cru)

ESCOPO: metodologia agnóstica de nicho pra responder UMA pergunta: "título
gerado por LLM (grounded no vídeo) rende mais views que o título cru da
plataforma? O ganho paga a key?". Desenhado e rodando no Tibia (jul/2026).

## Por que testar em vez de assumir

Título-LIXO derruba ~4x (medido) — isso já se sabe. Mas "LLM > título cru
DECENTE" é hipótese: o cru da Twitch foi escrito por um humano que viu o
momento. LLM custa key + quota + ponto de falha; só fica se ganhar CLARO.

## Sorteio do braço: hash determinístico com SALT PRÓPRIO

Braço = `hash("ab:" + clip_id) % 2` → metade "llm", metade "cru".

- **Determinístico** (nada de random): o mesmo clip cai SEMPRE no mesmo braço
  — re-render/retry não troca o braço e não precisa de estado extra.
- **Salt próprio ("ab:")** — o detalhe que importa: se outro sorteio do
  pipeline usa o mesmo `hash(clip_id) % 2` (ex.: posição da webcam), os dois
  sorteios correlacionam 100% e viram UMA variável só — todo clip do braço
  LLM sairia com a webcam no mesmo canto e você não sabe o que mediu.
  Qualquer sorteio novo no pipeline = salt novo.
- Gravar o braço no banco por clip (ex.: coluna `ab_arm`) na hora do render —
  o relatório lê de lá, nunca re-deriva.

## Anti-contaminação (onde experimento morre em silêncio)

1. **LLM caiu (quota/erro) → o clip VIRA braço cru, não adia.** Adiar só num
   braço enviesa: o braço LLM perderia exatamente os horários/dias em que a
   cota estoura, e as amostras deixam de ser comparáveis. Regravar `ab_arm`
   como cru e seguir.
2. **Curador/QA automáticos DESLIGADOS nos dois braços.** Título é a ÚNICA
   variável. Se o curador derruba clip fraco só no braço LLM (ou o QA avalia
   o título junto), a comparação quebra. O gate humano da esteira continua —
   ele é igual pros dois braços.
3. **Flag global antiga que mexe em título tem que respeitar o experimento.**
   Foi o bug real (06/07): uma flag "título cru" antiga sobrescrevia o título
   DEPOIS da geração, em OUTRO módulo — braço "llm" saía com título cru, zero
   erro no log, semanas medindo nada. Lição: flag nova com precedência
   precisa ser aplicada em TODOS os pontos que a flag antiga toca.

## Medição

- **Métrica: views/DIA** (views ÷ dias no ar) — normaliza idade; sem isso o
  clip mais velho "ganha" só por ter acumulado mais tempo.
- Descartar clip com <1 dia no ar (views/dia ainda é ruído) e vídeo
  sumido/privado.
- **Mediana por braço, não média**: canal de corte vive de hit — 1 outlier de
  100k views num braço destrói a média e não representa o clip típico.
- **Custo de medir ~zero**: API pública de stats em lote (1 unit por 50
  vídeos) — não compete com a quota de upload.
- **n ≥ 50 por braço**: distribuição de views tem cauda pesada; abaixo disso
  a mediana ainda dança. Com n menor, NÃO decidir.
- **Janela ~14 dias**: hit de Short morre em ~3 dias; 14 cobre o ciclo de
  vida dos primeiros clips e dá tempo de acumular o n.

## Critério de decisão PRÉ-COMBINADO

Decidir o critério ANTES de olhar qualquer número — depois de ver o dado,
todo threshold vira racionalização. O combinado (06/07):

- `ratio = mediana(llm) / mediana(cru)`
- **ratio < 1.5x → título cru fica, LLM morre no título.** Empate ou ganho
  marginal não paga key + quota + mais um ponto de falha no pipeline.
- **ratio ≥ 1.5x → LLM definitivo + key paga.**

O relatório imprime o veredito sozinho quando `n ≥ 50` nos dois braços; antes
disso, marca "amostra pequena, não decidir".

## Checklist antes de deixar rodando

1. Validar 1 amostra REAL de CADA braço: abrir o clip publicado e conferir
   que o braço "llm" tem título de LLM e o "cru" tem o cru (teria pego o bug
   da flag no dia 1, não em semanas).
2. Conferir que `ab_arm` está sendo gravado no banco.
3. Conferir que nenhum sorteio novo do pipeline reusou o salt.
