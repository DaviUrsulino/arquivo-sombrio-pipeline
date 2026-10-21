from src.estudio_instagram import analista


def _r(hora, views, legenda="vídeo com claude", salvos=0, envios=0, alcance=None, tempo_ms=5000):
    return {"id": hora, "hora": hora, "legenda": legenda, "views": views, "saved": salvos, "shares": envios,
            "reach": alcance if alcance is not None else views, "ig_reels_avg_watch_time": tempo_ms}


def test_faixa_horaria_converte_utc_para_brasilia():
    assert analista.faixa_horaria("2026-10-20T12:00:00+0000") == "manhã (6-10h)"  # 09:00 em Brasília
    assert analista.faixa_horaria("2026-10-20T22:00:00+0000") == "noite (18-22h)"  # 19:00 em Brasília


def test_temas_por_palavra_da_legenda_com_fallback():
    assert "vídeo com IA" in analista.temas_de("Crie um vídeo com HTML")
    assert "assistente (Jarvis)" in analista.temas_de("O Jarvis ouve você")
    assert analista.temas_de("bom dia") == ["outros"]


def test_resumo_usa_mediana_para_nao_se_enganar_com_um_estouro():
    reels = [_r("2026-10-20T12:00:00+0000", v) for v in (100, 120, 30000)]
    assert analista.resumo(reels)["views_medianas"] == 120


def test_taxas_por_100_de_alcance_e_tempo_em_segundos():
    reels = [_r("2026-10-20T12:00:00+0000", 1000, salvos=50, envios=20, alcance=1000, tempo_ms=8000)]
    r = analista.resumo(reels)
    assert r["salvos_por_100_alcance"] == 5.0 and r["envios_por_100_alcance"] == 2.0 and r["tempo_medio_s"] == 8.0


def test_recomendacao_exige_amostra_minima():
    reels = [_r("2026-10-20T12:00:00+0000", 30000), _r("2026-10-20T12:30:00+0000", 20000)]
    assert analista.analisar(reels)["melhor_faixa"] is None  # só 2 Reels: não recomenda


def test_relatorio_menciona_retencao_e_melhores_posts():
    reels = [_r(f"2026-10-20T1{i}:00:00+0000", 100 * (i + 1)) for i in range(4)]
    texto = analista.relatorio(analista.analisar(reels), 165, "2026-10-20 21:00")
    assert "Retenção" in texto and "Melhores posts" in texto and "165" in texto


def test_formato_curto_e_separado_pela_data_do_experimento():
    assert analista.formato_de("2026-10-20T12:00:00+0000").startswith("longo")
    assert analista.formato_de("2026-10-21T13:00:00+0000").startswith("curto")
    por = analista.analisar([_r("2026-10-20T12:00:00+0000", 100), _r("2026-10-21T13:00:00+0000", 300)])["por_formato"]
    assert por["curto (20-35 s)"]["n"] == 1 and por["longo (45-60 s)"]["n"] == 1
