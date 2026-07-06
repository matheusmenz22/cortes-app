# cortes-app

Gerador automático de **cortes verticais (Shorts)** a partir de conteúdo da **Twitch**,
com foco inicial em **League of Legends**.

O app capta os melhores momentos, gera um corte vertical 9:16 e enfileira o
resultado para **aprovação/reprovação** manual antes de publicar.

## Princípios

- **TDD de verdade**: a lógica de domínio é pura e coberta por testes antes da integração.
- **Arquitetura em camadas**, sem gambiarra:
  - `domain/`   — regras puras, sem I/O (testável isoladamente).
  - `sources/`  — adapters de captação (Twitch Clips API, VODs no futuro) atrás de uma interface.
  - `editing/`  — render 9:16/legendas (ffmpeg).
  - `review/`   — fila + UI de aprovação.
- **Colaboração via Git**: toda mudança entra por branch + Pull Request no repositório
  principal (`main` protegida). Ver [Fluxo de trabalho](#fluxo-de-trabalho).

## Requisitos

- Python 3.11+
- ffmpeg no PATH
- Credenciais da Twitch API (crie um app em https://dev.twitch.tv/console/apps)

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env            # preencha as credenciais
```

## Testes

```bash
pytest                # roda a suíte
ruff check .          # lint
mypy                  # tipos
```

## Estratégia de corte (por que engaja)

Baseado em pesquisa de retenção de Shorts + conteúdo de LoL:

1. **Gancho nos 2-3s** — começar pelo clímax (pentakill, 1v5, roubo de Baron), não pela construção.
2. **Batida visual a cada 1-2s** — priorizar teamfight, nunca lane/farm parado.
3. **Detecção do melhor momento** — killfeed/multikill, voz do narrador ("Pentakill"),
   pico de mensagens no chat, pico de volume do áudio.
4. **9:16, gameplay centralizada, legendas grandes**, 15-40s, postagem consistente.

## Fluxo de trabalho

```bash
git switch -c feat/minha-mudanca
# ... código + testes ...
pytest && ruff check .
git commit -m "feat: descrição"
git push -u origin feat/minha-mudanca
# abrir Pull Request para main
```

`main` só recebe código com testes passando.

## Roadmap

- [x] Esqueleto + arquitetura em camadas (TDD)
- [ ] Adapter Twitch Clips API (melhores momentos por jogo)
- [ ] Render 9:16 + legendas (ffmpeg)
- [ ] Fila + UI de aprovação/reprovação
- [ ] (fase 2) Detecção de melhor momento em VODs (chat + áudio + killfeed)
