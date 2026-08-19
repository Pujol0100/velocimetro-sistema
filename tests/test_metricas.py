import pytest

from velocimetro.metricas import PISO_TETO_MBPS, LeitorDeMetricas

UM_MB = 1024 * 1024


class FonteFalsa:
    """Fonte de sistema controlada, para o teste nao depender da maquina real."""

    def __init__(self, cpu=10.0, memoria=20.0, bytes_disco=0, agora=0.0):
        self.valor_cpu = cpu
        self.valor_memoria = memoria
        self.valor_bytes_disco = bytes_disco
        self.valor_agora = agora
        self.erro_cpu = None
        self.erro_disco = None

    def cpu(self):
        if self.erro_cpu:
            raise self.erro_cpu
        return self.valor_cpu

    def memoria(self):
        return self.valor_memoria

    def bytes_disco(self):
        if self.erro_disco:
            raise self.erro_disco
        return self.valor_bytes_disco

    def agora(self):
        return self.valor_agora

    def avancar(self, segundos, bytes_transferidos=0):
        self.valor_agora += segundos
        self.valor_bytes_disco += bytes_transferidos


class TestLeituraDeCpuEMemoria:
    def test_repassa_cpu_e_memoria_da_fonte(self):
        leitura = LeitorDeMetricas(FonteFalsa(cpu=37.5, memoria=64.25)).ler()
        assert leitura.cpu == pytest.approx(37.5)
        assert leitura.memoria == pytest.approx(64.25)

    def test_valores_acima_de_cem_sao_limitados(self):
        leitura = LeitorDeMetricas(FonteFalsa(cpu=137.0, memoria=104.0)).ler()
        assert leitura.cpu == pytest.approx(100.0)
        assert leitura.memoria == pytest.approx(100.0)

    def test_valores_negativos_sao_limitados(self):
        leitura = LeitorDeMetricas(FonteFalsa(cpu=-3.0, memoria=-1.0)).ler()
        assert leitura.cpu == pytest.approx(0.0)
        assert leitura.memoria == pytest.approx(0.0)


class TestAtividadeDeDisco:
    def test_primeira_leitura_de_disco_e_zero(self):
        leitura = LeitorDeMetricas(FonteFalsa(bytes_disco=5_000_000)).ler()
        assert leitura.disco == pytest.approx(0.0)
        assert leitura.disco_mbps == pytest.approx(0.0)

    def test_calcula_vazao_em_megabytes_por_segundo(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.avancar(2.0, bytes_transferidos=100 * UM_MB)
        assert leitor.ler().disco_mbps == pytest.approx(50.0)

    def test_percentual_de_disco_usa_o_teto_como_fundo_de_escala(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.avancar(1.0, bytes_transferidos=int(PISO_TETO_MBPS / 2) * UM_MB)
        assert leitor.ler().disco == pytest.approx(50.0, abs=0.5)

    def test_teto_comeca_no_piso(self):
        assert LeitorDeMetricas(FonteFalsa()).teto_mbps == pytest.approx(PISO_TETO_MBPS)

    def test_teto_sobe_quando_a_vazao_o_excede(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.avancar(1.0, bytes_transferidos=int(PISO_TETO_MBPS * 3) * UM_MB)
        leitura = leitor.ler()
        assert leitor.teto_mbps > PISO_TETO_MBPS * 2.9
        assert leitura.disco == pytest.approx(100.0, abs=0.5)

    def test_teto_decai_de_volta_com_o_tempo(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.avancar(1.0, bytes_transferidos=int(PISO_TETO_MBPS * 4) * UM_MB)
        leitor.ler()
        teto_no_pico = leitor.teto_mbps
        for _ in range(200):
            fonte.avancar(1.0)
            leitor.ler()
        assert leitor.teto_mbps < teto_no_pico

    def test_teto_nunca_cai_abaixo_do_piso(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        for _ in range(5000):
            fonte.avancar(1.0)
            leitor.ler()
        assert leitor.teto_mbps >= PISO_TETO_MBPS

    def test_teto_aprendido_pode_ser_restaurado(self):
        leitor = LeitorDeMetricas(FonteFalsa(), teto_inicial_mbps=1200.0)
        assert leitor.teto_mbps == pytest.approx(1200.0)

    def test_teto_restaurado_abaixo_do_piso_e_elevado_ao_piso(self):
        leitor = LeitorDeMetricas(FonteFalsa(), teto_inicial_mbps=5.0)
        assert leitor.teto_mbps == pytest.approx(PISO_TETO_MBPS)

    def test_relogio_parado_nao_divide_por_zero(self):
        fonte = FonteFalsa()
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.avancar(0.0, bytes_transferidos=50 * UM_MB)
        assert leitor.ler().disco_mbps == pytest.approx(0.0)

    def test_contador_reiniciado_nao_gera_valor_negativo(self):
        fonte = FonteFalsa(bytes_disco=900 * UM_MB)
        leitor = LeitorDeMetricas(fonte)
        leitor.ler()
        fonte.valor_bytes_disco = 0
        fonte.valor_agora += 1.0
        leitura = leitor.ler()
        assert leitura.disco_mbps == pytest.approx(0.0)
        assert leitura.disco == pytest.approx(0.0)


class TestFalhaNaFonte:
    def test_falha_de_cpu_devolve_none_sem_estourar(self):
        fonte = FonteFalsa()
        fonte.erro_cpu = OSError("contador indisponivel")
        assert LeitorDeMetricas(fonte).ler().cpu is None

    def test_falha_de_cpu_nao_contamina_as_outras_metricas(self):
        fonte = FonteFalsa(memoria=55.0)
        fonte.erro_cpu = OSError("contador indisponivel")
        assert LeitorDeMetricas(fonte).ler().memoria == pytest.approx(55.0)

    def test_falha_de_disco_devolve_none(self):
        fonte = FonteFalsa()
        fonte.erro_disco = OSError("sem contador de disco")
        leitura = LeitorDeMetricas(fonte).ler()
        assert leitura.disco is None
        assert leitura.disco_mbps is None
