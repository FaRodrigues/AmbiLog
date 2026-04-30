# PROJECT.md — LabVariab v0.6

## What This Is

Sistema de aquisição, monitoramento em tempo real e análise estatística de variáveis ambientais (temperatura e umidade) para laboratório científico, usando o datalogger Agilent 34970A via GPIB. Versão 0.6 consolida a v0.5 (robustez) e adiciona análise estatística avançada: banda de confiança GUM 95%, forecast ARIMA de 30 minutos e projeção de curvas no dashboard Bokeh.

## Core Value

**Confiabilidade científica dos dados**: o sistema deve rodar indefinidamente sem perder medidas, e o dashboard deve comunicar a incerteza real das medições (GUM) com projeção temporal, permitindo decisões rastreáveis e conformes com normas metrológicas (DIMCI/INMETRO).

## Context

- **Laboratório**: LAORT / ambiente científico controlado
- **Instrumento**: Agilent 34970A, GPIB0::5::INSTR, 4 canais (101–104)
- **Sensores**: 2 sensores T+RH (Vaisala, saída 4–20 mA, shunt 268 Ω)
  - Sensor A: Cert. DIMCI 1403/2023 (U_T = 0.20 °C, U_RH = 1.11 %ur, k=2)
  - Sensor B: Cert. DIMCI 1404/2023 (mesmas especificações)
- **Versões anteriores**: v0.4 funcional (referência); v0.5 parcialmente migrada com bugs documentados
- **Base científica**: GUM (Guide to Expression of Uncertainty in Measurement), ARIMA p/ forecast, Stat2Science (NotebookLM — 30 fontes)
- **Ambiente**: Windows 10/11, Conda env `freq`, Python 3.7+
- **Autores**: F. Rodrigues, Marcelo De Cicco (2024–2026)

## Problem Being Solved

A v0.5 introduziu melhorias (barras de erro GUM, retry GPIB, XML diário) mas tem bugs que impedem operação contínua sem supervisão:
1. `NameError: datetime` em `safe_parse_scientific` (path de erro nunca testado)
2. `ntries=+1` (contador nunca incrementa)
3. Árvore XML estática no retry loop (dados novos nunca lidos)
4. `* 10` em `safe_parse_scientific` sem documentação clara (conversão de escala)
5. Sem arquivo de configuração — qualquer mudança exige editar código

E o dashboard ainda não oferece:
- Forecast de 30 minutos (ARIMA/AR)
- Banda de confiança 95% sobre a série histórica
- Rollover configurável (atualmente limitado a 100 pontos ≈ 50 min)

## Requirements

### Validated

- ✓ Leitura GPIB via pyvisa com retry — existing
- ✓ Armazenamento em XML diário com day-rollover — existing
- ✓ Calibração linear M×V+B calculada via sympy — existing
- ✓ Dashboard Bokeh em tempo real (T e RH, dual-sensor) — existing
- ✓ Barras de erro GUM (incerteza expandida U = k×uc) — existing (SensorV2.py)
- ✓ Análise histórica com GUI Tkinter + matplotlib — existing (VarAmbseries0.6.2.py)
- ✓ Aba de estatísticas horárias no Bokeh — existing (Visual_with_stats.py)

### Active

- [ ] **STAB-01**: Corrigir `NameError: datetime` em `safe_parse_scientific`
- [ ] **STAB-02**: Corrigir `ntries += 1` (era `ntries=+1`)
- [ ] **STAB-03**: Re-parsear XML dentro do loop de retry (árvore estática atual)
- [ ] **STAB-04**: Documentar e validar o fator `* 10` na conversão de escala
- [ ] **STAB-05**: Arquivo de configuração externalizado (GPIB addr, porta Bokeh, rollover, etc.)
- [ ] **STAB-06**: `requirements.txt` ou `environment.yml` para reprodutibilidade
- [ ] **STAB-07**: Logging com módulo `logging` (replace print statements no logger)
- [ ] **VIS-01**: Banda de confiança 95% (CI) sobre série histórica no Bokeh
- [ ] **VIS-02**: Forecast ARIMA/AR de 30 minutos com banda de incerteza propagada
- [ ] **VIS-03**: Rollover configurável no ColumnDataSource.stream()
- [ ] **VIS-04**: Indicador visual de status do sensor (online/offline/timeout)
- [ ] **ANA-01**: Integrar previsão no VarAmbseries GUI (anaálise histórica + projeção)
- [ ] **ANA-02**: Exportar série + forecast + CI para CSV/TXT estruturado

### Out of Scope

- Banco de dados (SQL/NoSQL) — XML é suficiente para escala atual
- Interface web além do Bokeh — não solicitado
- Autenticação/usuários — sistema local
- MQTT/SCADA integration — não solicitado
- HMM (Hidden Markov Model) para detecção de estados — ARIMA é preferível para escalares contínuos (conforme Stat2Science)
- Monte Carlo propagation — GUM linear suficiente (U_GUM já calculado e validado em DIMCI)

## Key Decisions

| Decisão | Racional | Resultado |
|---------|----------|-----------|
| ARIMA, não Cadeias de Markov | Stat2Science confirma: Markov é para estados discretos; ARIMA é o correto para forecast de scalares (T, RH) contínuos | ARIMA(p,d,q) com statsmodels — Pendente |
| k=2 para CI 95% | GUM (DIMCI) e Stat2Science: Teorema do Limite Central + graus de liberdade suficientes → normal → k=2 | Já implementado em SensorV2.py |
| Arquivo de config externo | Evitar editar código para mudar endereço GPIB, porta, thresholds | config.yaml ou config.ini — Pendente |
| Bokeh como dashboard | Já funcional na v0.5; não trocar framework | Manter Bokeh, adicionar funcionalidades |
| Manter XML como storage | Simples, auditável, compatível com VarAmbseries. Para escala atual (1 medida/30s) XML é apropriado | Manter XML + otimizar parser |

## Evolution

Este documento evolui a cada transição de fase (`/gsd-transition`) e milestone (`/gsd-complete-milestone`).

**Após cada transição de fase:**
1. Requisitos invalidados → mover para Out of Scope com razão
2. Requisitos validados → mover para Validated com referência à fase
3. Novos requisitos → adicionar em Active
4. Decisões novas → registrar em Key Decisions

**Após cada milestone:**
1. Revisão completa de todas as seções
2. Verificar se Core Value ainda é a prioridade correta
3. Auditar Out of Scope — razões ainda válidas?
4. Atualizar Context com estado atual

---
*Last updated: 2026-04-09 after initialization*

## References
- **Agilent Manuals**: Available via Google Drive link (contains Agient_Manual34972A.pdf and Agient_comannds34972A.pdf). Use browser subagent to fetch SCPI command validation when working on Phase 1 (Bug Fixes and scaling factor * 10 check).
