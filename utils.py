import math
from colorama import Fore, Style

def calcular_distancia(p1, p2):
    # Distância Euclidiana básica
    return round(math.dist(p1, p2), 2)

def consumo_bateria(distancia, fator_consumo=0.8):
    # Consumo estimado de bateria
    return int(distancia * fator_consumo)

def log_agente(nome, msg, cor="azul"):
    # Formatação de cores no terminal de acordo com o papel do agente
    cores = {
        "azul": Fore.CYAN, 
        "verde": Fore.GREEN, 
        "amarelo": Fore.YELLOW,
        "vermelho": Fore.RED, 
        "roxo": Fore.MAGENTA, 
        "branco": Fore.WHITE,
        "cinza": Fore.LIGHTBLACK_EX
    }
    cor_final = cores.get(cor, Fore.WHITE)
    print(f"{cor_final}[{nome}] {msg}{Style.RESET_ALL}")

class Monitoramento:
    def __init__(self):
        self.tarefas_total = 0
        self.tarefas_concluidas = 0
        self.custos = []
        self.energia_final = []
        self.propostas_enviadas = 0
        self.inicio_execucao = None
        self.fim_execucao = None

    def registrar_tarefa(self, custo=None):
        self.tarefas_concluidas += 1
        if custo is not None:
            self.custos.append(custo)

    def registrar_total(self, total):
        self.tarefas_total = total

    def registrar_energia(self, bateria_restante):
        self.energia_final.append(bateria_restante)

    def resumo(self):
        print("\n" + "-" * 40)
        print(" MÉTRICAS DO MONITOR")
        print("-" * 40)
        print(f"Entregas efetuadas: {self.tarefas_concluidas}/{self.tarefas_total}")
        
        if self.custos:
            media_custo = sum(self.custos) / len(self.custos)
            print(f"Custo médio proposto: {media_custo:.2f}")
            
        if self.energia_final:
            media_bat = sum(self.energia_final) / len(self.energia_final)
            print(f"Bateria média restante: {media_bat:.1f}%")
        print("-" * 40 + "\n")