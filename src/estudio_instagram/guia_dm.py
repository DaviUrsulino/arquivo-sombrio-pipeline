"""Mini-guia que o bot manda no direct quando alguém comenta a palavra do vídeo.

Antes a pessoa recebia só o link. Agora recebe o que a ferramenta resolve, como começar em 3 passos (tirados do
README de verdade) e um jeito pronto de usar. É o "produto" que o seguidor ganha por comentar, então precisa valer
a pena sozinho. Sem emoji (pedido do Davi). O direct do Instagram aceita até 1000 caracteres.
"""

from .github_dados import DadosRepo
from .llm import LLMIndisponivel, gerar_json

LIMITE = 950

SISTEMA = """Você escreve a mensagem de direct que um criador de conteúdo de IA manda pra quem comentou no Reels dele.
Recebe os dados e o começo do README de um repositório do GitHub. Devolve só JSON:
{"resolve": "1 frase: o problema que a ferramenta resolve pra pessoa, em linguagem simples",
 "passos": ["passo 1", "passo 2", "passo 3"],
 "dica": "1 frase: um uso prático e concreto pra testar hoje (pode ser um prompt ou comando curto)"}
REGRAS: português do Brasil, frases curtas, sem emoji, sem hashtag. Os passos e comandos precisam existir no README
(não invente comando, flag ou nome de pacote). Se o README não mostrar instalação, o passo 1 é abrir o link e seguir o README."""


def _usuario(dados: DadosRepo, readme: str) -> str:
    return (f"Repositório: {dados.repo}\nDescrição: {dados.descricao}\nEstrelas: {dados.estrelas}\n"
            f"Licença: {dados.licenca}\n\nREADME (começo):\n{readme[:6000]}")


def montar(dados: DadosRepo, resposta: dict) -> str:
    nome = dados.repo.split("/", 1)[1]
    passos = "\n".join(f"{i}. {p.strip()}" for i, p in enumerate(resposta["passos"][:3], 1))
    texto = (f"Oi! Aqui está o {nome}.\n\n{resposta['resolve'].strip()}\n\nComo começar:\n{passos}\n\n"
             f"Pra testar hoje: {resposta['dica'].strip()}\n\nLink: {dados.url}\n\n"
             f"Toda semana eu posto uma ferramenta assim. Segue o @ursulino.ia pra não perder.")
    return texto if len(texto) <= LIMITE else simples(dados)


def simples(dados: DadosRepo) -> str:
    return (f"Oi! Aqui está o repositório {dados.repo.split('/', 1)[1]}: {dados.url}\n"
            f"Se curtir, segue o @ursulino.ia pra mais ferramentas de IA.")


def gerar(dados: DadosRepo, readme: str, llm=gerar_json) -> str:
    """Mensagem com guia; se o LLM falhar ou devolver algo fora do formato, cai no link simples."""
    try:
        resposta = llm(SISTEMA, _usuario(dados, readme))
        if not (isinstance(resposta.get("passos"), list) and len(resposta["passos"]) >= 2 and resposta.get("resolve") and resposta.get("dica")):
            return simples(dados)
        return montar(dados, resposta)
    except (LLMIndisponivel, KeyError, TypeError, AttributeError):
        return simples(dados)
