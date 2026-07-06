"""Smoke test do pacote (garante import + versão exposta).

Mantém a suíte não-vazia até os módulos com testes próprios entrarem na main.
"""

import cortes_app


def test_version_exposed():
    assert isinstance(cortes_app.__version__, str)
    assert cortes_app.__version__
