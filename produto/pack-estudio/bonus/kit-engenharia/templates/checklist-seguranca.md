# Checklist de segurança (marque ou escreva "N/A")

- [ ] Nenhum segredo no código, log ou histórico do git; `.env` ignorado
- [ ] Senhas com hash forte; sessão expira; limite de tentativas de login
- [ ] Toda rota com dado confere dono/permissão no servidor (teste A × B existe)
- [ ] Toda entrada externa validada (tipo, tamanho, formato, faixa)
- [ ] SQL parametrizado; saída escapada (XSS); sem `eval` em entrada
- [ ] Upload: limite, tipo conferido, nome gerado, fora da pasta pública
- [ ] Webhook: assinatura conferida; valor conferido contra preço real
- [ ] Sem dado pessoal real em repositório público, log ou teste
- [ ] `npm audit` / `pip-audit` sem alto ou crítico
- [ ] Produção: debug off, CORS restrito, HTTPS, limite de requisições
- [ ] IA: texto externo tratado como dado; saída do LLM validada; escopo mínimo; teto de gasto e de passos
