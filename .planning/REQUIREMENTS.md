# REQUIREMENTS.md — LabVariab v0.6

## User Personas
* **Pesquisador Principal**: Precisa das medidas exatas, com incerteza rigorosamente quantificada (DIMCI/INMETRO), para tomar decisões científicas. Sem tempo para reconfigurar código.
* **Sistema (24/7)**: Precisa rodar sozinho, gerenciar viradas de dia de arquivos de log, lidar com falhas de conexão GPIB sem travar e não sobrecarregar as rotinas UI.

## Functional Requirements
* **REQ-1 (GPIB Robustness)**: O logger `34970A_5.py` deve tratar erros de parse de notação científica mal formatada.
* **REQ-2 (File Parsing Retry)**: A leitura falha de XML do Visualizer deve sempre garantir parse da versão mais *live* do XML dentro do loop de retry, e não carregar um cache stale. 
* **REQ-3 (Forecast 30min)**: Exibir projeção estatística de T e UR (ARIMA default, 30 minutos a frente) e salvá-la de forma rastreável.
* **REQ-4 (GUM 95% CI)**: Plotter deve mostrar não só o valor pontual (y_linha), mas a área esfumaçada correspondente à banda 95% de confiança GUM (k=2).
* **REQ-5 (Configs Externos)**: GPIB e constantes (endereço, timer, portas, canais) localizadas num `config.ini` legível.
* **REQ-6 (Exportação Histórica)**: A janela de visualização do Tkinter `VarAmb...` deve incluir capacidade de exportar forecast + CI bands gerados ao lado dos valores reais.

## Non-Functional Requirements
* **NFR-1 (Thread Safety)**: O Forecast / Model refitting deve ocorrer *fora* da render loop e do file writer (usar o SensorV2 thread com next_tick_callbacks via partial).
* **NFR-2 (No Database Config)**: Manter integração e armazenamento via FS local e XML.
* **NFR-3 (Reprodutibilidade)**: Exportação de pacotes conda do `freq` em yaml / requirement.txt.

## Out of Scope
* Mudança de protocolo de hardware.
* Painéis web hospedados (nuvem).
* Markov Models (como validado pelo Stat2Science, focaremos no ARIMA/AR para as séries temporais métricas).
