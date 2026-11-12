"""pipeline_completo --video-pronto (11/11): os dois canais do YouTube publicam o vídeo animado da fila, nunca foto."""
import json
import os
import sys
import types


def _importar():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
    for m in ["google", "google.genai", "gerar_roteiro", "gerar_imagens_cloudflare", "montar_video_local", "canais", "canais.tendencias"]:
        sys.modules.setdefault(m, types.ModuleType(m))
    sys.modules["gerar_roteiro"].__dict__.update(MIN_PALAVRAS_ROTEIRO=1, MODELOS_FALLBACK=[], _chaves_api=lambda: [], gerar_roteiro=None)
    sys.modules["gerar_imagens_cloudflare"].gerar_imagens_do_roteiro = None
    sys.modules["montar_video_local"].montar_video = None
    sys.modules["canais"].carregar_canal = None
    sys.modules["canais"].tendencias = sys.modules["canais.tendencias"]
    import pipeline_completo
    return pipeline_completo


def test_mesmo_video_sai_nos_dois_canais_uma_vez_cada(tmp_path, monkeypatch):
    pc = _importar()
    (tmp_path / "a.json").write_text(json.dumps({"titulo": "t", "video_pronto_url": "http://x/v.mp4", "molde": "e-se",
                                                 "publicado": {"arquivo_sombrio": {"url": "u"}}}), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps({"titulo": "t2", "video_pronto_url": "http://x/w.mp4", "publicado": {}}), encoding="utf-8")
    assert pc.proxima_pronta("arquivo_sombrio", str(tmp_path)).endswith("b.json")  # o a já saiu nesta conta
    assert pc.proxima_pronta("tendencias", str(tmp_path)).endswith("a.json")       # mais antigo que ainda não saiu
    monkeypatch.chdir(tmp_path)
    r = pc.publicar_pronta("tendencias", publicar=False, baixar=lambda u, v: open(v, "w").close(), pasta=str(tmp_path))
    assert r["publicado"] is False and r["pauta"].endswith("a.json") and r["molde"] == "e-se"


def test_fila_vazia_nao_cai_na_foto(tmp_path):
    pc = _importar()
    r = pc.publicar_pronta("arquivo_sombrio", publicar=True, pasta=str(tmp_path))
    assert r == {"aprovado": True, "publicado": False, "motivo": "fila vazia"}
