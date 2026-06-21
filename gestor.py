from maspy import *
from utils import log_agente, Monitoramento
from time import time


class GestorTarefas(Agent):

    def __init__(self, nome, ambiente, robos, monitor=None):
        super().__init__(nome)

        self.env = ambiente
        self.robos = robos
        self.monitor = monitor or Monitoramento()

        # Dicionário para evitar concorrência entre tarefas
        self.propostas_por_tarefa = {}
        
        self.tarefas_em_execucao = []
        self.negociacao_ativa = False
        self.simulacao_encerrada = False
        self.executando_ciclo = False  # Trava de concorrência

        # Conjunto local para rastreamento de metas ativas (evita KeyError no MASPY)
        self.metas_ativas = set()

        self.total_esperado = 0
        self.tarefa_atual = None

        if self.monitor.inicio_execucao is None:
            self.monitor.inicio_execucao = time()

        log_agente(self.my_name,
                   f"Gestor iniciado com {len(robos)} robôs conectados.",
                   cor="amarelo")

    # =====================================================================
    # Método Utilitário: Agendar gerenciamento sem duplicar objetivos
    # =====================================================================
    def agendar_gerenciamento(self):
        # Impede de forma absoluta a criação de metas idênticas e concorrentes
        if "gerenciar_tarefas" not in self.metas_ativas:
            self.metas_ativas.add("gerenciar_tarefas")
            self.add(Goal("gerenciar_tarefas"))

    # =====================================================================
    # Objetivo Principal: Gerenciar e coordenar as tarefas do dia
    # =====================================================================
    @pl(gain, Goal("gerenciar_tarefas"))
    def iniciar_negociacao(self, src):
        # Evita execuções concorrentes do mesmo ciclo
        if self.executando_ciclo:
            return
        self.executando_ciclo = True

        tarefas_pendentes = self.env.listar_tarefas_pendentes()
        tarefas_pendentes = [
            t for t in tarefas_pendentes 
            if t["status"] == "pendente"
        ]

        # -----------------------------------------------------------------
        # Caso 1: Sem tarefas pendentes para negociar
        # -----------------------------------------------------------------
        if not tarefas_pendentes:
            concluidas = sum(1 for p in self.env.pacotes if p["status"] == "entregue")
            total = len(self.env.pacotes)

            # Se ainda houver robôs na rua fazendo entregas, espera a conclusão
            if self.tarefas_em_execucao:
                self.executando_ciclo = False
                self.metas_ativas.discard("gerenciar_tarefas") # Libera rastreamento
                self.wait(1)
                self.agendar_gerenciamento()
                return

            # Se todos os pacotes foram entregues com sucesso, encerra o sistema
            if concluidas == total:
                log_agente(self.my_name, 
                           "Todas as tarefas do dia concluídas. Finalizando sistema...", 
                           cor="roxo")
                self.simulacao_encerrada = True
                self.monitor.fim_execucao = time()
                
                self.relatorio_final()
                self.monitor.resumo()
                
                self.wait(2)
                Admin().stop_system()
                return

            log_agente(self.my_name, "Nenhuma tarefa pendente. Aguardando...", cor="amarelo")
            self.executando_ciclo = False
            self.metas_ativas.discard("gerenciar_tarefas") # Libera rastreamento
            self.wait(2)
            self.agendar_gerenciamento()
            return

        # -----------------------------------------------------------------
        # Caso 2: Abrir negociação para a primeira tarefa da fila
        # -----------------------------------------------------------------
        if not self.negociacao_ativa:
            tarefa = tarefas_pendentes[0]
            tarefa["status"] = "em_negociacao"
            self.env.change(Percept("tarefa", Any), tarefa)

            log_agente(self.my_name, f"Iniciando negociação da tarefa {tarefa['id']}", cor="amarelo")
            self.enviar_pedido_proposta(tarefa)
        else:
            log_agente(self.my_name, "Negociação em andamento...", cor="amarelo")

        self.executando_ciclo = False
        self.metas_ativas.discard("gerenciar_tarefas") # Libera rastreamento

    # =====================================================================
    # Enviar pedido de proposta (CFP - Call For Proposal)
    # =====================================================================
    def enviar_pedido_proposta(self, tarefa):
        # Inicializa a lista de propostas especificamente para esta tarefa no dicionário
        self.propostas_por_tarefa[tarefa["id"]] = []

        robos_disponiveis = [r for r in self.robos if not r.ocupado]

        if not robos_disponiveis:
            log_agente(self.my_name, "Nenhum robô disponível no momento. Aguardando liberação...", cor="amarelo")
            tarefa["status"] = "pendente"
            self.env.change(Percept("tarefa", Any), tarefa)
            
            self.executando_ciclo = False
            self.metas_ativas.discard("gerenciar_tarefas") # Libera rastreamento
            self.wait(2)
            self.agendar_gerenciamento()
            return

        self.total_esperado = len(robos_disponiveis)
        self.negociacao_ativa = True
        self.tarefa_atual = tarefa["id"]

        for robo in robos_disponiveis:
            self.send(robo.my_name, achieve, Goal("pedido_proposta", tarefa))
            log_agente(self.my_name, f"Pedido de proposta enviado para {robo.my_name}", cor="roxo")
            self.wait(0.1)

        log_agente(self.my_name, f"Aguardando {self.total_esperado} propostas...", cor="amarelo")

    # =====================================================================
    # Receber as propostas calculadas pelos robôs
    # =====================================================================
    @pl(gain, Belief("proposta", Any))
    def receber_proposta(self, src, proposta):
        if not self.negociacao_ativa:
            return

        tarefa_id = proposta["tarefa"]["id"]
        # Garante que a proposta recebida é do leilão em andamento
        if tarefa_id != self.tarefa_atual:
            return

        if tarefa_id not in self.propostas_por_tarefa:
            self.propostas_por_tarefa[tarefa_id] = []

        # Evita registrar propostas duplicadas do mesmo robô na mesma tarefa
        if any(p["robo"] == proposta["robo"] for p in self.propostas_por_tarefa[tarefa_id]):
            return

        self.propostas_por_tarefa[tarefa_id].append(proposta)
        log_agente(self.my_name, 
                   f"Proposta de {proposta['robo']} recebida (Custo: {proposta['custo']:.2f})", 
                   cor="branco")

        if len(self.propostas_por_tarefa[tarefa_id]) == self.total_esperado:
            # Trava de segurança para impedir avaliação duplicada concorrente
            if not self.negociacao_ativa:
                return
            self.negociacao_ativa = False

            log_agente(self.my_name, "Todas as propostas recebidas! Avaliando...", cor="amarelo")

            melhor = min(self.propostas_por_tarefa[tarefa_id], key=lambda x: x["custo"])
            log_agente(self.my_name, 
                       f"Vencedor da concorrência: {melhor['robo']} (Custo: {melhor['custo']:.2f})", 
                       cor="verde")

            self.enviar_resultado_negociacao(melhor)

    # =====================================================================
    # Comunicar o resultado da negociação aos robôs concorrentes
    # =====================================================================
    def enviar_resultado_negociacao(self, melhor):
        tarefa = melhor["tarefa"]
        tarefa_id = tarefa["id"]

        self.monitor.custos.append(melhor["custo"])

        self.tarefas_em_execucao.append({
            "tarefa_id": tarefa_id,
            "robo": melhor["robo"]
        })

        # MARCA O ROBÔ COMO OCUPADO IMEDIATAMENTE (Evita deadlock de concorrência assíncrona)
        for r in self.robos:
            if r.my_name == melhor["robo"]:
                r.ocupado = True
                break

        # Notifica o vencedor
        self.send(melhor["robo"], tell, Belief("tarefa_aceita", tarefa))

        # Notifica os perdedores da tarefa correspondente
        for prop in self.propostas_por_tarefa[tarefa_id]:
            if prop["robo"] != melhor["robo"]:
                self.send(prop["robo"], tell, Belief("proposta_recusada", tarefa_id))

        self.wait(0.5)
        self.agendar_gerenciamento()

    # =====================================================================
    # Receber notificação de entrega concluída
    # =====================================================================
    @pl(gain, Belief("tarefa_concluida", Any))
    def confirmar_conclusao(self, src, tarefa_id):
        log_agente(self.my_name, f"Confirmado: {src} concluiu a entrega da tarefa {tarefa_id}.", cor="verde")

        self.tarefas_em_execucao = [
            t for t in self.tarefas_em_execucao 
            if t["tarefa_id"] != tarefa_id
        ]

        self.monitor.registrar_tarefa()
        self.agendar_gerenciamento()

    # =====================================================================
    # Geração do Relatório Final para Apresentação
    # =====================================================================
    def relatorio_final(self):
        print("\n" + "="*60)
        print(" " * 10 + "RELATÓRIO FINAL DO ARMAZÉM AUTÔNOMO")
        print("="*60)

        tempo_total = 0
        if self.monitor.fim_execucao:
            tempo_total = self.monitor.fim_execucao - self.monitor.inicio_execucao

        total = self.monitor.tarefas_total
        concluidas = self.monitor.tarefas_concluidas
        progresso = (concluidas / total) * 100 if total > 0 else 0

        print(f"Tempo total de simulação: {tempo_total:.2f} segundos")
        print(f"Taxa de sucesso: {concluidas}/{total} tarefas entregues ({progresso:.1f}%)")
        print(f"Número de robôs ativos: {len(self.robos)}")
        print(f"Custo total estimado da operação: {sum(self.monitor.custos):.2f}")
        
        if self.monitor.custos:
            print(f"Custo médio por entrega: {sum(self.monitor.custos)/len(self.monitor.custos):.2f}")

        print("-"*60)
        print(" STATUS FINAL DOS ROBÔS ")
        print("-"*60)
        for robo in self.robos:
            status = "Livre" if not robo.ocupado else "Ocupado"
            print(f"{robo.my_name:<10} | Entregas Realizadas: {robo.tarefas_realizadas:<2} | "
                  f"Bateria Restante: {robo.bateria:>3}% | Estado: {status}")

        print("-"*60)
        print(" ESTADO FINAL DOS PACOTES DO DIA ")
        print("-"*60)
        for p in self.env.pacotes:
            print(f"Pacote {p['id']:>2} | Origem: {p['origem']} → Destino: {p['destino']} "
                  f"| Status: {p['status']}")
        print("="*60 + "\n")