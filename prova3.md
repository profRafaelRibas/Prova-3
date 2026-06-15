# Descrição Técnica do Trabalho: Armazém Autônomo e Protocolo Contract-Net no MASPY

## 1. Descrição do Cenário
O projeto simula um **Armazém Autônomo** composto por uma grade física bidimensional de $10 \times 10$ posições (coordenadas de $0$ a $9$). No início do dia, o ambiente (`Armazem`) gera um conjunto de tarefas pendentes. Cada tarefa representa um pacote que possui um identificador único, uma coordenada geográfica de origem (onde o pacote está localizado) e uma coordenada geográfica de destino (onde ele deve ser entregue). 

Para otimizar o fluxo de trabalho e poupar energia, o armazém não distribui as tarefas de forma aleatória. Em vez disso, o sistema utiliza o protocolo de negociação **Contract-Net** para que os robôs disponíveis disputem a execução de cada pacote, garantindo que o robô mais adequado (com base na proximidade física e saúde da bateria) seja o escolhido.

---

## 2. Os Agentes do Sistema e seu Funcionamento

O sistema é composto por duas classes principais de agentes BDI, que atuam de forma coordenada e independente:

### A) Gestor de Tarefas (`GestorTarefas`)
É o agente centralizador e coordenador (leiloeiro) do armazém. Suas principais atribuições são:
*   **Monitoramento do Ambiente:** Ele lê as percepções do armazém para listar pacotes com o status `"pendente"`.
*   **Coordenação do Leilão (Contract-Net):** Ele inicia a negociação de cada tarefa enviando uma Chamada de Proposta (CFP) para os robôs disponíveis.
*   **Avaliação de Propostas:** Coleta as propostas de custo enviadas pelos robôs concorrentes, seleciona o robô de menor custo, confirma a vitória para o vencedor (`tarefa_aceita`) e notifica os perdedores (`proposta_recusada`).
*   **Gestão de Ocupação:** Ele marca localmente os robôs como ocupados assim que eles ganham um contrato, o que impede problemas de concorrência ou conflitos de atribuição antes de a mensagem assíncrona ser processada.
*   **Geração de Relatório:** Ao final, quando todas as tarefas são concluídas com sucesso, ele imprime uma planilha detalhada com o tempo total, a bateria residual de cada robô e a taxa de sucesso.

### B) Robô Entregador (`RoboEntregador`)
São os agentes executores. Cada instância é um robô situado na grade com localização e bateria próprias. Suas atribuições são:
*   **Cálculo de Proposta:** Ao receber um pedido de proposta, ele avalia se está ocupado. Se estiver livre, calcula um custo de proposta baseado na **Distância de Manhattan** até o pacote somada a uma penalidade caso sua bateria esteja baixa. Em seguida, envia esse valor ao Gestor.
*   **Raciocínio BDI de Execução:** Ao receber a confirmação de que ganhou o leilão, ele adota o objetivo interno de `"executar_tarefa"`.
*   **Movimentação Determinística:** O robô se desloca passo a passo pela grade em direção às coordenadas desejadas (primeiro até a origem do pacote e, depois de coletá-lo, até o destino). A cada passo, sua bateria é reduzida em $1\%$.
*   **Notificação de Sucesso:** Após efetuar a entrega física no ambiente, ele informa o Gestor (`tarefa_concluida`) e altera seu estado para livre, ficando pronto para o próximo leilão.

---

## 3. Funcionamento do Protocolo Contract-Net na Prática
O ciclo completo de negociação ocorre de forma contínua através dos seguintes passos:

1.  **CFP (Call for Proposal):** O `Gestor` identifica um pacote pendente e envia uma meta do tipo `Goal("pedido_proposta", tarefa)` aos robôs livres.
2.  **Propose (Proposta):** Os robôs recebem a meta, calculam o custo interno e respondem com uma crença `Belief("proposta", resposta)` para o `Gestor`.
3.  **Accept / Reject (Aceite ou Recusa):** O `Gestor` avalia as propostas recebidas. O robô que ofereceu o menor custo recebe o aviso `Belief("tarefa_aceita", tarefa)` e os outros recebem `Belief("proposta_recusada")`.
4.  **Execution (Execução):** O robô vencedor adota o plano de ação, coleta o pacote na grade, transporta até o destino e realiza a entrega.
5.  **Inform (Informação de Conclusão):** O robô envia `Belief("tarefa_concluida")` ao Gestor. O Gestor atualiza a fila de execuções e dispara um novo ciclo de leilão para os pacotes restantes.

---

## 4. Justificativa de Atendimento aos Critérios da Atividade

A implementação atende aos critérios descritos nos requisitos da **Avaliação 3**:

*   **Cenário Autônomo e Original (Não idêntico aos exemplos do MASPY):** 
    O cenário de logística em grade bidimensional, onde robôs competem por tarefas de transporte com base em distância de Manhattan e desgaste de bateria, é uma criação personalizada. Ele difere dos exemplos simples disponibilizados oficialmente na documentação do MASPY (como cruzamento de trânsito ou estacionamento básico).
*   **2 ou mais tipos de agentes:** 
    O sistema possui exatamente dois tipos de agentes bem definidos e programados de forma separada: a classe `GestorTarefas` e a classe `RoboEntregador` [2].
*   **1 ou mais agentes de cada tipo executados ao mesmo tempo:** 
    A simulação instancia e executa simultaneamente 1 agente do tipo `GestorTarefas` (`Gestor`) e 3 agentes do tipo `RoboEntregador` (`Robo_1`, `Robo_2` e `Robo_3`), que cooperam e competem concorrentemente no mesmo ambiente [2].
*   **Troca de mensagens entre os agentes:** 
    Há uma comunicação ativa entre os agentes através da função de envio de mensagens do MASPY (`self.send`). Os agentes se comunicam utilizando performativas adequadas de BDI, tais como pedidos de metas (`achieve` com `Goal`) e envios de informações/propostas (`tell` com `Belief`) [2, 62].
*   **Negociação seguindo o protocolo Contract-Net:** 
    O processo de distribuição de tarefas segue rigidamente a estrutura do Contract-Net (Chamada de Proposta $\rightarrow$ Envio de Proposta de Custo $\rightarrow$ Seleção do Menor Custo $\rightarrow$ Confirmação/Recusa $\rightarrow$ Execução da Tarefa $\rightarrow$ Informação de Conclusão) [2].
*   **Ausência de interferência humana (Autonomia e Proatividade):** 
    O sistema é completamente autônomo. Uma vez iniciado no arquivo `main.py`, os robôs se posicionam, os pacotes são gerados e toda a negociação, locomoção e tomada de decisão ocorrem proativamente através dos ciclos de raciocínio BDI internos dos agentes, sem qualquer input do usuário pelo teclado ou tela [2].