from maspy import *
from utils import log_agente, calcular_distancia
import random
from time import sleep


class RoboEntregador(Agent):

    def __init__(self, nome, ambiente, monitor):
        super().__init__(nome)

        self.env = ambiente
        self.monitor = monitor

        self.posicao = (random.randint(0, ambiente.linhas - 1), 
                        random.randint(0, ambiente.colunas - 1))
        
        self.bateria = 100
        self.ocupado = False
        self.tarefas_realizadas = 0
        self.tarefa_atual = None

        log_agente(self.my_name,
                   f"Robô iniciado em {self.posicao} (bateria={self.bateria}%)",
                   cor="azul")

    # =====================================================================
    # [Contract-Net] Receber pedido de proposta do Gestor
    # =====================================================================
    @pl(gain, Goal("pedido_proposta", Any))
    def receber_pedido_proposta(self, src, dados_tarefa):
        if self.ocupado:
            return

        custo = self.calcular_custo_proposta(dados_tarefa)
        
        resposta = {
            "robo": self.my_name,
            "custo": custo,
            "tarefa": dados_tarefa
        }

        self.send(src, tell, Belief("proposta", resposta))
        log_agente(self.my_name, f"Proposta enviada p/ tarefa {dados_tarefa['id']} (custo={custo:.2f})")

    # =====================================================================
    # Cálculo de custo (distância física + desgaste de bateria)
    # =====================================================================
    def calcular_custo_proposta(self, tarefa):
        (tx, ty) = tarefa["origem"]
        (x, y) = self.posicao
        distancia = abs(tx - x) + abs(ty - y)
        return distancia * 1.0 + (100 - self.bateria) * 0.1

    # =====================================================================
    # [Contract-Net] Receber a confirmação de vitória na negociação
    # =====================================================================
    @pl(gain, Belief("tarefa_aceita", Any))
    def tratar_tarefa_aceita(self, src, tarefa):
        self.ocupado = True
        log_agente(self.my_name, f"Ganhei o leilão para a tarefa {tarefa['id']}! Agendando execução...", cor="verde")
        self.add(Goal("executar_tarefa", tarefa))

    # =====================================================================
    # [Contract-Net] Receber a notificação de derrota na negociação
    # =====================================================================
    @pl(gain, Belief("proposta_recusada", Any))
    def tratar_proposta_recusada(self, src, tarefa_id):
        log_agente(self.my_name, f"Perdi a concorrência pela tarefa {tarefa_id}.", cor="branco")

    # =====================================================================
    # Plano BDI principal: Executar a entrega
    # =====================================================================
    @pl(gain, Goal("executar_tarefa", Any))
    def executar_tarefa(self, src, tarefa):
        self.tarefa_atual = tarefa

        origem = tarefa["origem"]
        destino = tarefa["destino"]

        # 1. Mover até a origem para coletar
        log_agente(self.my_name, f"Iniciando tarefa {tarefa['id']}. Indo até a origem {origem}...", cor="azul")
        self.mover_ate(origem)
        self.coletar_pacote(tarefa["id"])

        # 2. Mover até o destino para entregar
        log_agente(self.my_name, f"Indo até o destino de entrega {destino}...", cor="azul")
        self.mover_ate(destino)
        self.entregar_pacote(tarefa["id"])

        # 3. Finalização local
        self.tarefas_realizadas += 1
        self.ocupado = False
        self.tarefa_atual = None

        log_agente(self.my_name,
                   f"Tarefa {tarefa['id']} concluída com sucesso! Bateria={self.bateria}%",
                   cor="verde")

        # 4. Envia notificação de conclusão ao Gestor
        self.send("Gestor", tell, Belief("tarefa_concluida", tarefa["id"]))
        
        # O MASPY remove o Goal "executar_tarefa" automaticamente após o fim deste plano.
        # Linha self.rm(...) removida para evitar KeyError decorrente de mutação de dados da tarefa.

    # =====================================================================
    # Movimentação passo a passo
    # =====================================================================
    def mover_ate(self, destino):
        while self.posicao != destino and self.bateria > 0:
            x, y = self.posicao
            tx, ty = destino

            if x != tx:
                direcao = "down" if tx > x else "up"
            elif y != ty:
                direcao = "right" if ty > y else "left"
            else:
                break

            nova_posicao = self.env.movimentar(self.posicao, direcao)
            
            if nova_posicao == self.posicao:
                break

            self.posicao = nova_posicao
            self.bateria = max(0, self.bateria - 1)
            
            sleep(0.3)
            log_agente(self.my_name, f"Movendo-se ({direcao}) → {self.posicao} | Bat={self.bateria}%", cor="branco")

    # =====================================================================
    # Coleta e entrega físicas no ambiente
    # =====================================================================
    def coletar_pacote(self, tarefa_id):
        log_agente(self.my_name, f"Efetuando coleta do pacote {tarefa_id}...", cor="amarelo")
        sucesso = self.env.coletar_pacote(self.my_name, tarefa_id)
        if sucesso:
            self.bateria = max(0, self.bateria - 2)
            sleep(0.5)

    def entregar_pacote(self, tarefa_id):
        log_agente(self.my_name, f"Efetuando entrega do pacote {tarefa_id}...", cor="amarelo")
        sucesso = self.env.entregar_pacote(self.my_name, tarefa_id)
        if sucesso:
            self.bateria = max(0, self.bateria - 2)
            if self.monitor:
                self.monitor.registrar_energia(self.bateria)
            sleep(0.5)