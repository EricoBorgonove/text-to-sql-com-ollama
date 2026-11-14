"""Memoria em RAM, somente das interacoes concluidas com sucesso."""
from collections import deque
import json

MAX_INTERACOES = 5
MAX_LINHAS_MEMORIA = 10
MAX_CARACTERES_RESPOSTA = 800
MAX_CARACTERES_CAMPO = 180


class MemoriaConversa:
    def __init__(self, limite=MAX_INTERACOES):
        self._interacoes = deque(maxlen=limite)

    def registrar(self, pergunta, sql, linhas, resposta):
        # Nenhuma credencial ou contexto de conexao e armazenado.
        amostra = []
        for linha in linhas[:MAX_LINHAS_MEMORIA]:
            amostra.append({str(k): str(v)[:MAX_CARACTERES_CAMPO]
                            for k, v in linha.items()})
        self._interacoes.append({
            "pergunta": pergunta[:400],
            "sql": sql[:2000],
            "linhas": amostra,
            "resposta": resposta[:MAX_CARACTERES_RESPOSTA],
            "amostra_limitada": len(linhas) > MAX_LINHAS_MEMORIA,
        })

    def contexto(self):
        if not self._interacoes:
            return "Nenhuma interacao anterior nesta sessao."
        return json.dumps(list(self._interacoes), ensure_ascii=False, indent=2)

    def limpar(self):
        self._interacoes.clear()

    def __len__(self):
        return len(self._interacoes)
