# Contribuindo com o cortes-app

## Fluxo de trabalho (branch + Pull Request)

A `main` é protegida: **só recebe código via Pull Request com CI verde**. Nunca
commite direto na `main`.

1. Atualize a `main` e crie uma branch:
   ```bash
   git switch main && git pull
   git switch -c feat/twitch-clips-source     # <tipo>/<descrição-curta>
   ```
2. Faça **commits pequenos e atômicos** (um propósito por commit).
3. Rode a checagem local antes do push (`pre-commit` + `pytest`).
4. `git push -u origin <branch>` e abra um **Pull Request** para a `main`.

### Nomes de branch
`feat/…` `fix/…` `chore/…` `docs/…` `test/…` `refactor/…`

## Convenção de commits (Conventional Commits)

Formato:
```
<tipo>(escopo opcional): <descrição no imperativo>
```

**Tipos:** `feat` `fix` `docs` `test` `refactor` `chore` `perf` `ci` `build` `style`

- Assunto ≤ 72 caracteres, no **imperativo** ("adiciona", não "adicionado"), sem ponto final.
- Corpo (opcional) explica o **porquê**, não o "o quê".
- Rodapé para breaking changes (`BREAKING CHANGE: …`) e refs (`Closes #12`).

Exemplos:
```
feat(sources): adiciona adapter da Twitch Clips API
fix(silence): trata clipe de duração zero
test(silence): cobre pausas múltiplas
```

Ative o template de mensagem (uma vez, por clone):
```bash
git config commit.template .gitmessage
```

## Qualidade (obrigatório antes do PR)

```bash
pip install -e ".[dev]"
pre-commit install            # instala os hooks (rodam a cada commit)
pre-commit run --all-files    # roda tudo manualmente
pytest                        # testes
```

Ruff (lint + format), mypy (strict) e pytest também rodam no **CI** a cada PR —
a `main` só integra código com tudo verde.
