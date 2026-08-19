import json

from velocimetro.config import Config, carregar, salvar


class TestPadroes:
    def test_arquivo_ausente_devolve_padroes(self, tmp_path):
        assert carregar(tmp_path / "nao-existe.json") == Config()

    def test_padrao_tem_opacidade_cheia(self):
        assert Config().opacidade == 1.0

    def test_padrao_nao_tem_posicao_gravada(self):
        assert Config().posicao is None


class TestIdaEVolta:
    def test_salvar_e_carregar_preserva_os_campos(self, tmp_path):
        caminho = tmp_path / "config.json"
        original = Config(
            posicao=(120, 340), escala=1.4, opacidade=0.65, teto_disco_mbps=880.5
        )
        salvar(original, caminho)
        assert carregar(caminho) == original

    def test_salvar_cria_a_pasta_se_faltar(self, tmp_path):
        caminho = tmp_path / "sub" / "pasta" / "config.json"
        salvar(Config(escala=1.1), caminho)
        assert caminho.exists()

    def test_arquivo_gravado_e_json_legivel(self, tmp_path):
        caminho = tmp_path / "config.json"
        salvar(Config(opacidade=0.5), caminho)
        assert json.loads(caminho.read_text(encoding="utf-8"))["opacidade"] == 0.5


class TestArquivoRuim:
    def test_json_corrompido_devolve_padroes(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text("{isso nao e json", encoding="utf-8")
        assert carregar(caminho) == Config()

    def test_arquivo_vazio_devolve_padroes(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text("", encoding="utf-8")
        assert carregar(caminho) == Config()

    def test_json_que_nao_e_objeto_devolve_padroes(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text("[1, 2, 3]", encoding="utf-8")
        assert carregar(caminho) == Config()

    def test_campo_desconhecido_e_ignorado(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps({"opacidade": 0.8, "campo_inventado": "xyz"}), encoding="utf-8"
        )
        assert carregar(caminho).opacidade == 0.8

    def test_tipo_errado_num_campo_devolve_o_padrao_daquele_campo(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(json.dumps({"opacidade": "muito"}), encoding="utf-8")
        assert carregar(caminho).opacidade == Config().opacidade

    def test_opacidade_fora_da_faixa_e_limitada(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(json.dumps({"opacidade": 9.0}), encoding="utf-8")
        assert carregar(caminho).opacidade == 1.0
