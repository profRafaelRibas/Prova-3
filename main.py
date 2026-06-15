from maspy import *
from time import sleep
import os

from ambiente import Armazem
from robo import RoboEntregador
from gestor import GestorTarefas
from utils import Monitoramento


def main():
    # Limpa o console para facilitar a visualização da execução
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "="*60)
    print("      SIMULAÇÃO DO ARMAZÉM AUTÔNOMO — PROTOCOLO CONTRACT-NET")
    print("="*60 + "\n")

    # Inicializa o monitor de métricas
    monitor = Monitoramento()

    # Cria o ambiente físico único (sem necessidade do ambiente de treino RL)
    ambiente_real = Armazem("Armazem")
    
    # Registra o total de tarefas criadas no ambiente
    monitor.registrar_total(len(ambiente_real.pacotes))

    # Instancia os robôs entregadores (utilizando 3 robôs para um leilão ágil)
    NUM_ROBOS = 3
    robos = [
        RoboEntregador(f"Robo_{i}", ambiente_real, monitor)
        for i in range(1, NUM_ROBOS + 1)
    ]

    # Instancia o Gestor de Tarefas que coordenará as negociações
    gestor = GestorTarefas("Gestor", ambiente_real, robos, monitor)

    # Conecta os agentes e o ambiente ao administrador do MASPY
    admin = Admin()
    admin.connect_to(
        [gestor] + robos,
        [ambiente_real]
    )

    # Define o objetivo inicial do Gestor para disparar o leilão
    gestor.add(Goal("gerenciar_tarefas"))

    sleep(1)

    # Inicia a execução do Sistema Multiagente MASPY de forma autônoma
    Admin().start_system()


if __name__ == "__main__":
    main()