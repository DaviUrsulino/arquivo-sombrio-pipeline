"""Frente Zack (11/11): molde do Zack D. Films para o YouTube e, nos temas de tecnologia, para o Instagram."""
import json
from datetime import datetime, timedelta, timezone

from src.estudio_instagram import estilo_formato, zack

BOM = {"titulo": "E se você ficasse 11 dias sem dormir?", "texto_tela": "11 DIAS SEM DORMIR",
       "corpo": ["No terceiro dia sem dormir, o seu cérebro começa a apagar por segundos.",
                 "Isso se chama microssono e dura de 1 a 10 segundos.",
                 "No dia 5 você começa a ver coisas que não existem.",
                 "O recorde é de 11 dias, 264 horas acordado.",
                 "Mas o corpo não aguenta esse ritmo sem cobrar.",
                 "A memória falha, a fala embola e o coração acelera.",
                 "No dia 11 ele dormiu 14 horas e acordou normal."],
       "legenda": "O que acontece com o seu corpo a cada dia sem dormir.", "direcao": "dentro do cérebro"}


def test_molde_aprova_roteiro_no_padrao_zack():
    assert zack.problemas(BOM) == []


def test_molde_reprova_introducao_pedido_e_falta_de_numero():
    r = json.loads(json.dumps(BOM))
    r["corpo"][0] = "Você sabia que dá pra ficar dias sem dormir?"
    r["corpo"][-1] = "Comenta DORMIR que eu te mando o resto."
    r["corpo"] = [f.replace("1", "").replace("5", "").replace("264", "muitas").replace("4", "").replace("11", "") for f in r["corpo"]]
    erros = " ".join(zack.problemas(r))
    assert "introdução" in erros and "pedido" in erros and "número" in erros


def test_molde_exige_virada_e_segunda_pessoa():
    r = json.loads(json.dumps(BOM))
    r["corpo"] = [f.replace("Mas ", "E ").replace("você", "a pessoa").replace("seu ", "o ") for f in r["corpo"]]
    erros = " ".join(zack.problemas(r))
    assert "Mas" in erros and "segunda pessoa" in erros


def test_escrever_monta_historia_sem_pedido_e_com_formato_zack():
    chamadas = []

    def llm(sistema, pedido):
        chamadas.append(sistema)
        return {"nota": 8.5, "problema": ""} if "nota" in sistema.lower() or len(chamadas) % 2 == 0 else BOM

    h = zack.escrever("onze-dias", "Randy Gardner", "e-se", "ângulo", "youtube", llm=llm, ler=lambda t: "x" * 2000)
    assert h["formato"] == "zack" and h["plataforma"] == "youtube" and h["molde"] == "e-se"
    assert h["roteiro"]["cta"] == "" and h["roteiro"]["ganchos"] == [BOM["corpo"][0]]
    assert h["roteiro"]["corpo"] == BOM["corpo"][1:] and h["titulo"] == BOM["titulo"]
    assert zack.PERSONAGEM in h["direcao"]


def test_instagram_so_pega_tema_com_pe_em_tecnologia():
    tema = zack.proximo_tema({}, "instagram")
    assert tema is not None and tema[4] is True
    assert zack.proximo_tema({}, "youtube") == zack.TEMAS[0]


def test_intervalo_e_por_plataforma():
    agora = datetime(2026, 11, 12, 3, 0, tzinfo=timezone.utc)
    estado = {"zack:a": {"quando": (agora - timedelta(hours=7)).isoformat(timespec="minutes"), "plataforma": "youtube"}}
    assert zack.precisa(estado, "youtube", agora) is True
    assert zack.precisa(estado, "instagram", agora) is True  # a do Instagram nunca saiu
    estado["zack:b"] = {"quando": (agora - timedelta(hours=1)).isoformat(timespec="minutes"), "plataforma": "youtube"}
    assert zack.precisa(estado, "youtube", agora) is False


def test_formato_zack_sem_hud_e_com_estilos_de_corte():
    assert estilo_formato.hud("zack") == {"tipo": "nenhum"}
    assert "teardown" in estilo_formato.recomendados("zack")


def test_numeros_extrai_trechos_com_unidade():
    achados = zack.numeros("The cable is 1.2 million km long. It was laid in 1858. Fibers carry 100 Tbps over 7,000 km.")
    assert any("1.2 million" in a for a in achados) and any("7,000 km" in a for a in achados)


def test_um_tema_ruim_nao_trava_a_rodada(monkeypatch):
    chamados = []

    def falso(slug, titulo, molde, angulo, plataforma, **k):
        chamados.append(slug)
        if len(chamados) < 3:
            raise ValueError("fora do molde")
        return {"slug": slug, "formato": "zack", "plataforma": plataforma}

    monkeypatch.setattr(zack, "escrever", falso)
    monkeypatch.setattr(zack.series, "_ler", lambda a: {})
    monkeypatch.setattr(zack.series, "registrar", lambda *a, **k: None)
    monkeypatch.setattr(zack, "ROTEIROS_YOUTUBE", __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
    destino = zack.gerar_se_preciso("youtube")
    assert destino is not None and len(chamados) == 3
