# Canal @robo.estagiario (Instagram) — requisitos e desenho

> Status: em construção (branch `feat/estudio-automatico`). Decisões: ADR-0003, ADR-0004 e ADR-0005.

## 1. Requisitos

### Negócio (por quê)
- Ter um perfil próprio no Instagram ensinando ferramentas de IA, que traga seguidores e
  venda produtos baratos (~R$ 20).
- Custo operacional baixo (só o ElevenLabs, quando passar do plano grátis).
- Operar sem o Davi editar ou gravar nada.

### Usuário (o quê)
- O Davi não escolhe pauta: o sistema acha o que está dando comentário no nicho.
- O Davi não edita: cada pauta vira 1 Reels e 1 carrossel prontos para postar.
- A publicação acontece sozinha, com registro do que foi postado.

### Produto

**Funcionais**
- **RF-01** Coletar os posts públicos dos concorrentes (Apify, com limite de itens) e
  ordenar por comentários.
- **RF-02** Montar a pauta com dados reais e verificáveis (ex.: API do GitHub: estrelas,
  licença, descrição, cartão do repositório).
- **RF-03** Gerar o roteiro em JSON com vocabulário fechado de elementos visuais.
- **RF-04** Validar o roteiro no código antes de gastar crédito de voz: schema, âncoras que
  existem na narração, ícones existentes, tamanho de texto.
- **RF-05** Gerar a narração com tempo por palavra (ElevenLabs), com cache.
- **RF-06** Renderizar o Reels (MP4 1080x1920, com legenda) e o carrossel (PNG 1080x1350).
- **RF-07** Publicar Reels e carrossel pela Instagram Graph API.
- **RF-08** Registrar cada execução (pauta, fontes, arquivos, link publicado).

**Não funcionais**
- **RNF-01** Testes automatizados no CI; APIs externas substituídas por dublês nos testes.
- **RNF-02** Segredos só em `.env` (local) e GitHub Secrets (CI). Chaves com permissão
  mínima e teto de uso.
- **RNF-03** Render local com limite de memória, para não derrubar o PC.
- **RNF-04** Rodar de novo não refaz o que já foi feito (cache de voz por hash).

**Regras de negócio**
- **RN-1** Todo número e fato do post vem de uma fonte coletada; o link vai na legenda.
- **RN-2** Nada de voz, rosto ou marca de pessoa real imitada.
- **RN-3** Dado de rede social: só público, sem guardar dado pessoal de terceiros (LGPD).

### Prioridade (MoSCoW)
- **Must:** RF-02 a RF-07, RNF-01, RNF-02.
- **Should:** RF-01 automático semanal, RF-08, resposta automática do "comenta PALAVRA".
- **Could:** nota de viralidade do gancho (Higgsfield), música de fundo.
- **Won't (agora):** avatar, voz clonada, outros idiomas.

## 2. Desenho

### Classes

```mermaid
classDiagram
    class Pauta {
      titulo: str
      palavra_chave: str
      itens: list~ItemPauta~
      fontes() list~str~
    }
    class ItemPauta {
      nome: str
      repo: str
      estrelas: int
      licenca: str
      descricao: str
    }
    class Roteiro {
      titulo: str
      voz: str
      cenas: list~Cena~
    }
    class Cena {
      id: str
      cor: str
      narracao: str
      elementos: list~dict~
    }
    class Narracao {
      audio_pcm: bytes
      palavras: list~PalavraNoTempo~
      duracao() float
    }
    class PalavraNoTempo {
      t: float
      palavra: str
    }
    class ProvedorDeVoz {
      <<interface>>
      sintetizar(texto) Narracao
    }
    class ElevenLabs
    class Carrossel {
      slides: list~Path~
    }
    class Reels {
      video: Path
    }
    Pauta *-- ItemPauta : contém
    Roteiro *-- Cena : contém
    Narracao *-- PalavraNoTempo : contém
    ProvedorDeVoz <|.. ElevenLabs : implementa
    Roteiro ..> Pauta : usa
    Reels ..> Roteiro : usa
    Reels ..> Narracao : usa
    Carrossel ..> Pauta : usa
```

- **Composição** (`*--`): uma `Cena` não existe sem o `Roteiro`; uma `PalavraNoTempo` não
  existe sem a `Narracao`; um `ItemPauta` não existe sem a `Pauta`.
- **Realização** (`<|..`): `ElevenLabs` implementa `ProvedorDeVoz`. Trocar de provedor (ou
  usar um dublê no teste) não muda o resto do código.
- **Dependência** (`..>`): Reels e Carrossel só leem a pauta e o roteiro durante o render.

### Sequência de uma execução

```mermaid
sequenceDiagram
    participant Cron as GitHub Actions (cron)
    participant P as pipeline.py
    participant GH as API do GitHub
    participant V as ElevenLabs
    participant HF as Hyperframes
    participant IG as Instagram Graph API
    Cron->>P: roda
    P->>GH: dados dos repositórios da pauta
    GH-->>P: estrelas, licença, descrição, cartão
    P->>P: monta e valida o roteiro (RF-03, RF-04)
    P->>V: narração por cena (with-timestamps)
    V-->>P: áudio + tempo por caractere
    P->>HF: render do Reels e snapshot do carrossel
    HF-->>P: MP4 + PNGs
    P->>IG: publica Reels e carrossel
    IG-->>P: ids publicados
    P->>P: registra a execução (RF-08)
```
