---
name: eng-seguranca
description: Revisa e endurece o código contra falhas de segurança comuns em software feito com IA (segredos, autorização, injeção, entrada não validada, dependências, prompt injection). Use em todo diff antes de entregar e ao tocar login, dados de usuário, pagamento, upload ou integração externa.
---

# Segurança como parte do trabalho, não como fase final

Software gerado por IA costuma funcionar e falhar em segurança. Aplique este checklist ao seu próprio diff, sem perguntar.

## Checklist (faça de verdade; marque o que não se aplica)
**1. Segredos**
- Nenhuma chave, senha ou token no código, em log, em exemplo ou em commit. Use variável de ambiente.
- `.env`, `*.pem`, `token*.json`, `client_secret*.json` no `.gitignore`. Se algo já foi commitado, considere vazado: rotacione.
- Busque no histórico: `git log -p | grep -iE "api[_-]?key|secret|token|password"`.

**2. Autenticação**
- Senha com hash forte (bcrypt/argon2), nunca texto puro nem hash rápido.
- Sessão ou token com expiração; logout invalida. Limite de tentativas de login.
- Não invente criptografia nem biblioteca de login própria.

**3. Autorização (o erro mais comum)**
- Toda rota que lê ou altera dado confere **quem é o usuário e se o dado é dele** (previne IDOR: trocar `/pedido/12` por `/pedido/13`).
- Teste automatizado: usuário A tenta acessar dado do usuário B e recebe 403/404.
- Verificar permissão no servidor, nunca só escondendo botão na tela.

**4. Entrada e injeção**
- Valide tipo, tamanho, formato e faixa de **toda** entrada externa (formulário, URL, header, arquivo, webhook).
- SQL sempre parametrizado, nunca concatenado. Escape de saída contra XSS. Nunca `eval`/`exec` em entrada.
- Upload: limite de tamanho, tipo conferido pelo conteúdo, nome gerado por você, fora da pasta pública.
- Webhook (pagamento etc.): confira assinatura e **valor contra o preço real no servidor**.

**5. Dados e privacidade (LGPD)**
- Colete só o necessário. Não registre senha, token, documento ou cartão em log.
- Repositório público não leva dado pessoal real (use dado fictício em exemplos e testes).
- Backup e exclusão: sabe como apagar os dados de uma pessoa?

**6. Dependências e configuração**
- Rode o auditor do gerenciador (`npm audit`, `pip-audit`) e trate o que for alto/crítico.
- Fixe versões. Remova pacote que você não usa. Desconfie de pacote com nome parecido com o famoso (typosquatting).
- Produção: debug desligado, CORS restrito, HTTPS, cabeçalhos de segurança, limite de requisições.

**7. IA no meio do sistema**
- **Prompt injection**: texto vindo de usuário, site ou documento pode conter instruções. Trate como dado, nunca como ordem.
- Valide a saída do LLM no código (formato, tamanho, valores permitidos) antes de usar; nunca execute o que ele devolve.
- Dê ao agente o menor acesso possível (escopo mínimo, conta separada, sem credencial de produção em ambiente de teste).
- Defina teto de gasto e de passos para loop de agente. Erro de loop sem limite vira fatura.

## Como reportar
Liste cada achado como **[CRÍTICO | ALTO | MÉDIO | BAIXO]**, com arquivo e linha, o risco em uma frase e a correção.
Corrija CRÍTICO e ALTO antes de entregar e escreva teste para cada um. O restante vai para `docs/decisoes.md` como dívida.
Referências: OWASP Top 10, Agile Application Security (Bell et al.).
