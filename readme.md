Aqui está um modelo de arquivo **`README.md`** técnico e estruturado para o seu projeto, contendo a explicação do cenário, os agentes envolvidos e as instruções necessárias de instalação e execução.

---

### Código para o arquivo `README.md`

```markdown
# Armazém Autônomo com Protocolo Contract-Net (MASPY)

Este projeto implementa um Sistema Multiagente (SMA) utilizando a biblioteca **MASPY** (Multi-Agent System for Python) para simular o gerenciamento inteligente e autônomo de entregas em um armazém. A distribuição de tarefas é baseada no protocolo de negociação **Contract-Net**, onde agentes robôs competem por contratos de entrega de pacotes de acordo com suas condições físicas (distância e bateria).

O projeto é totalmente autônomo, proativo e livre de qualquer interferência humana durante a simulação.

---

## 🛠️ Arquitetura do Sistema

O sistema é modelado seguindo o paradigma de programação orientada a agentes BDI (*Belief-Desire-Intention*) e é estruturado em duas classes de agentes e um ambiente físico:

### 1. Ambiente (`Armazem`)
*   Modelado em uma grade física bidimensional de $10 \times 10$ posições.
*   Gera dinamicamente tarefas pendentes no início da execução. Cada tarefa possui uma coordenada de origem (onde o pacote está) e uma coordenada de destino (onde deve ser entregue).
*   Gerencia as percepções públicas de status de cada pacote (`pendente`, `em_negociacao`, `em_transporte`, `entregue`).

### 2. Agente Coordenador (`GestorTarefas`)
*   Atua como o leiloeiro do protocolo Contract-Net.
*   Busca pacotes com o status `pendente` e inicia a negociação enviando uma chamada de proposta (CFP) para os robôs livres.
*   Avalia as propostas recebidas, seleciona a de menor custo, confirma o contrato ao vencedor (`tarefa_aceita`) e rejeita os demais.
*   Controla localmente o estado de ocupação dos robôs para evitar deadlocks de concorrência assíncrona.
*   Gera um relatório estatístico de desempenho ao final do dia.

### 3. Agentes Executores (`RoboEntregador`)
*   Robôs situados na grade física com localização e bateria próprias.
*   Ao receberem um pedido de proposta, calculam um custo com base na **Distância de Manhattan** até o pacote somada a uma penalidade proporcional ao desgaste atual de sua bateria.
*   Caso vençam a disputa, adotam a intenção de buscar o pacote e transportá-lo até o destino.
*   Fazem uso de movimentação passo a passo determinística e notificam o Gestor assim que a entrega física é efetuada.

---

## 📂 Estrutura de Arquivos

*   `main.py`: Ponto de entrada do sistema. Instancia o ambiente, os robôs e o gestor, define o objetivo inicial e inicia o MASPY.
*   `ambiente.py`: Define a classe `Armazem` herdada de `Environment` e gerencia as ações e percepções físicas da grade.
*   `robo.py`: Contém a classe `RoboEntregador` com seus respectivos planos de negociação, movimentação e coleta de pacotes.
*   `gestor.py`: Contém a classe `GestorTarefas`, responsável por gerenciar a fila de leilões do Contract-Net e compilar os dados finais da operação.
*   `utils.py`: Fornece classes de apoio para o terminal colorido e a classe `Monitoramento` responsável pelas métricas estatísticas.

---

## 🚀 Instruções de Instalação e Execução

### Pré-requisitos
*   **Python 3.12 ou superior** (exigido pelas versões mais recentes do MASPY).

### Passo 1: Clonar ou Baixar o Projeto
Certifique-se de que todos os arquivos (`main.py`, `ambiente.py`, `robo.py`, `gestor.py`, `utils.py`) estejam localizados na mesma pasta de execução.

### Passo 2: Instalar as Dependências
Abra o seu terminal na pasta do projeto e instale as bibliotecas necessárias utilizando o gerenciador de pacotes `pip`:

```bash
pip install maspy-ml colorama
```

### Passo 3: Executar a Simulação
Para iniciar o sistema de armazém autônomo, execute o arquivo principal:

```bash
python main.py
```

---

## 📈 Exemplo de Fluxo da Simulação no Terminal

Ao executar o sistema, o terminal exibirá logs coloridos detalhados mostrando as etapas em tempo real:
1.  **Inicialização:** O ambiente é gerado e as tarefas são espalhadas pela grade.
2.  **Leilão:** O Gestor anuncia um pacote e os robôs retornam suas propostas calculadas.
3.  **Delegação:** O Gestor anuncia o vencedor (menor custo) e os perdedores da rodada.
4.  **Movimentação:** O robô vencedor se desloca passo a passo até a origem, coleta o pacote, se desloca ao destino e faz a entrega.
5.  **Finalização:** Ao concluir todos os pacotes gerados, o Gestor encerra o ciclo de processamento do MASPY e imprime um relatório final com as métricas do dia.
```