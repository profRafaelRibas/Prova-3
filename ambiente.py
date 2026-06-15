from maspy import *
from random import randint, choice


class Armazem(Environment):

    def __init__(self, env_name="Armazem"):
        super().__init__(env_name)

        # Grade física 10x10 (coordenadas de 0 a 9)
        self.linhas, self.colunas = (10, 10)
        self.num_tarefas = 5
        self.pacotes = []

        # Gerar as tarefas/pacotes da simulação
        for i in range(1, self.num_tarefas + 1):
            origem = (randint(0, self.linhas - 1), randint(0, self.colunas - 1))
            while True:
                destino = (randint(0, self.linhas - 1), randint(0, self.colunas - 1))
                if destino != origem:
                    break

            pacote = {
                "id": i,
                "origem": origem,
                "destino": destino,
                "status": "pendente"
            }

            self.pacotes.append(pacote)
            
            # Cria a percepção pública no MASPY para o Gestor poder ler
            self.create(Percept("tarefa", pacote))

        self.print(f"Armazém '{env_name}' iniciado com {self.num_tarefas} tarefas.")

    # Função auxiliar de movimentação (limitada ao grid)
    def movimentar(self, posicao_atual, direcao):
        x, y = posicao_atual
        if direcao == "up": 
            x = max(0, x - 1)
        elif direcao == "down": 
            x = min(self.linhas - 1, x + 1)
        elif direcao == "left": 
            y = max(0, y - 1)
        elif direcao == "right": 
            y = min(self.colunas - 1, y + 1)
        return x, y

    # Listar as tarefas que ainda estão disponíveis para negociação
    def listar_tarefas_pendentes(self):
        return [p for p in self.pacotes if p["status"] in ("pendente", "em_negociacao")]

    # Modificar o estado do pacote no sistema
    def marcar_em_negociacao(self, id_tarefa):
        for p in self.pacotes:
            if p["id"] == id_tarefa and p["status"] == "pendente":
                p["status"] = "em_negociacao"
                return True
        return False

    def marcar_entregue(self, id_tarefa):
        for p in self.pacotes:
            if p["id"] == id_tarefa:
                p["status"] = "entregue"
                return True
        return False

    # Ação de coleta de pacotes pelo Robô
    def coletar_pacote(self, agt, id_pacote):
        for p in self.pacotes:
            if p["id"] == id_pacote and p["status"] in ("pendente", "em_negociacao"):
                p["status"] = "em_transporte"
                self.print(f"{agt} coletou pacote {id_pacote} na posição {p['origem']}.")
                self.change(Percept("tarefa", Any), p)
                return True
        self.print(f"{agt} tentou coletar o pacote {id_pacote}, mas ele não estava disponível.")
        return False

    # Ação de entrega de pacotes pelo Robô
    def entregar_pacote(self, agt, id_pacote):
        for p in self.pacotes:
            if p["id"] == id_pacote and p["status"] == "em_transporte":
                p["status"] = "entregue"
                self.print(f"{agt} entregou o pacote {id_pacote} em {p['destino']}.")
                self.change(Percept("tarefa", Any), p)
                return True
        self.print(f"{agt} tentou entregar o pacote {id_pacote}, mas o robô não o carregava.")
        return False