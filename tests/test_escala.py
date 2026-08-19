import pytest

from velocimetro.escala import Faixa, Suavizador, faixa, percentual_para_angulo


class TestPercentualParaAngulo:
    def test_zero_por_cento_aponta_para_baixo_a_esquerda(self):
        assert percentual_para_angulo(0) == pytest.approx(210.0)

    def test_cem_por_cento_aponta_para_baixo_a_direita(self):
        assert percentual_para_angulo(100) == pytest.approx(-30.0)

    def test_metade_aponta_para_cima(self):
        assert percentual_para_angulo(50) == pytest.approx(90.0)

    def test_varredura_total_e_de_240_graus(self):
        varredura = percentual_para_angulo(0) - percentual_para_angulo(100)
        assert varredura == pytest.approx(240.0)

    def test_percentual_negativo_fica_preso_no_inicio(self):
        assert percentual_para_angulo(-30) == pytest.approx(210.0)

    def test_percentual_acima_de_cem_fica_preso_no_fim(self):
        assert percentual_para_angulo(160) == pytest.approx(-30.0)

    def test_angulo_diminui_conforme_percentual_sobe(self):
        angulos = [percentual_para_angulo(p) for p in range(0, 101, 10)]
        assert angulos == sorted(angulos, reverse=True)


class TestFaixa:
    def test_valor_baixo_e_normal(self):
        assert faixa(0) is Faixa.NORMAL
        assert faixa(59.9) is Faixa.NORMAL

    def test_a_partir_de_sessenta_e_atencao(self):
        assert faixa(60) is Faixa.ATENCAO
        assert faixa(84.9) is Faixa.ATENCAO

    def test_a_partir_de_oitenta_e_cinco_e_perigo(self):
        assert faixa(85) is Faixa.PERIGO
        assert faixa(100) is Faixa.PERIGO


class TestSuavizador:
    def test_comeca_no_valor_inicial(self):
        s = Suavizador(inicial=42.0)
        assert s.atual == pytest.approx(42.0)

    def test_um_passo_move_na_direcao_do_alvo(self):
        s = Suavizador(inicial=0.0)
        s.alvo = 100.0
        s.passo(0.033)
        assert 0.0 < s.atual < 100.0

    def test_converge_no_alvo_depois_de_muitos_passos(self):
        s = Suavizador(inicial=0.0)
        s.alvo = 73.0
        for _ in range(300):
            s.passo(0.033)
        assert s.atual == pytest.approx(73.0, abs=0.1)

    def test_ultrapassagem_limitada_a_oito_por_cento_do_salto(self):
        s = Suavizador(inicial=0.0)
        s.alvo = 100.0
        maximo = 0.0
        for _ in range(300):
            s.passo(0.033)
            maximo = max(maximo, s.atual)
        assert 100.0 < maximo <= 108.0

    def test_para_de_se_mover_ao_chegar_no_alvo(self):
        s = Suavizador(inicial=50.0)
        s.alvo = 50.0
        for _ in range(50):
            s.passo(0.033)
        assert s.em_repouso is True

    def test_nao_esta_em_repouso_enquanto_persegue(self):
        s = Suavizador(inicial=0.0)
        s.alvo = 90.0
        s.passo(0.033)
        assert s.em_repouso is False

    def test_passo_com_tempo_zero_nao_move(self):
        s = Suavizador(inicial=10.0)
        s.alvo = 90.0
        s.passo(0.0)
        assert s.atual == pytest.approx(10.0)

    def test_passo_longo_nao_explode(self):
        s = Suavizador(inicial=0.0)
        s.alvo = 100.0
        s.passo(5.0)
        assert 0.0 <= s.atual <= 108.0
