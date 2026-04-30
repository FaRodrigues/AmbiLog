# SUMMARY.md — Research Summary: LabVariab v0.6
<!-- Synthesized from: STACK.md, FEATURES.md, ARCHITECTURE.md, Stat2Science (NotebookLM 30 sources), v0.4 Configura_34970A-14082024.py, codebase/ (7 docs) -->

## What We're Building

**LabVariab v0.6** — upgrade do sistema de aquisição e monitoramento ambiental do laboratório LAORT. Consolida a v0.5 (estabilidade) e adiciona análise estatística avançada para uso científico: forecast ARIMA de 30 min e banda de confiança GUM 95%.

## Core Flow

```
Agilent 34970A
  → GPIB via pyvisa
  → 34970A_5.py (logger, will be stabilized)
  → varamblog/{YYDDD}/*.xml
  → streamingLab/SensorV2.py (sensor thread)
  → Bokeh ColumnDataSource
  → Visual.py (real-time plot + CI band + forecast)
```

## Key Technical Insights

### 1. ARIMA, não Markov (validado pelo Stat2Science)
- T e RH são séries temporais escalares contínuas → ARIMA/AR
- Markov: para estados discretos (falha/normal). HMM: ainda pior para valores contínuos.
- **Para 30 min com 1 medida/30s**: ARIMA(2,0,1) default, refit a cada 10 leituras (5 min)
- 60 steps × 30s = 30 min ✓

### 2. GUM k=2 para CI 95% (já implementado em SensorV2.py)
- u_c = √(u_A² + u_B²) onde u_A = incerteza tipo A (sensor), u_B = tipo B (calibração DIMCI)
- U = k × u_c com k=2 → ≈95% CI (Normal, graus de liberdade suficientes)
- **Para banda temporal**: rolling window de U sobre os últimos N pontos → upper = Ȳ + U_rolling, lower = Ȳ - U_rolling
- Implementado com Bokeh `Band` glyph

### 3. Bugs críticos na v0.5 que DEVEM ser corrigidos primeiro
1. `datetime.now()` → `NameError` no path de erro (deve ser `dtime.now()`)
2. `ntries=+1` → unário, nunca incrementa (deve ser `ntries += 1`)
3. `tree = ET.parse()` antes do loop → dados nunca atualizados no retry
4. Fator `* 10` em `safe_parse_scientific` — provavelmente correto (SCPI retorna V×0.1, ×10 → corrige escala) mas PRECISA SER VALIDADO com manual do 34970A
5. `resp = ''` após 10 falhas GPIB → pode causar IndexError em `decode_to_dict`

### 4. Config externalizado é o alicerce de todo o resto
- `config.ini` com GPIB address, porta Bokeh, parâmetros ARIMA, rollover
- Todas as fases subsequentes dependem disso para não hardcodar nada novo

### 5. Bokeh threading — padrão para features novas
- TODA atualização de UI deve usar `doc.add_next_tick_callback(partial(func, data))`
- Nunca atualizar `ColumnDataSource` direto do thread do sensor
- ARIMA fit: pesado → roda no thread do sensor (bloqueante OK pois ocorre só a cada 5 min)

## Risk Register

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| ARIMA CPU spike bloqueia loop de 30s | Média | Alto | Fit só a cada 10 leituras; timeout de model fit |
| `statsmodels` não instalado no Conda `freq` | Baixa | Alto | Adicionar ao environment.yml + requirements.txt antes de Phase 4 |
| Ring buffer vazio no startup | Alta | Médio | Guard: forecat só começa com ≥30 pontos no buffer |
| XML truncado por crash do logger | Baixa | Médio | Já tratado; aprimorar com logging |
| Bokeh 2→3 API changes | Baixa | Alto | Verificar versão exata no Conda `freq` antes de usar novas APIs |

## Build Sequence (Fine Granularity — 10 fases)

| Fase | Entregável | Dependências |
|------|-----------|--------------|
| 1 | Bug fixes críticos no logger (STAB-01..04) | Nenhuma |
| 2 | Config.ini + leitura em 34970A_5.py e SensorV2.py | Fase 1 |
| 3 | requirements.txt + environment.yml | Fase 1 |
| 4 | Logging modules (logger + sensor thread) | Fase 2 |
| 5 | Ring buffer de dados no SensorV2 | Fase 2 |
| 6 | CI 95% Band (Bokeh Band glyph) | Fase 5 |
| 7 | ARIMA forecast engine (statsmodels) | Fase 5 + 6 |
| 8 | Integração visual forecast no Bokeh | Fase 7 |
| 9 | VarAmbseries: forecast + exportar CI+forecast CSV | Fase 7 |
| 10 | Limpeza, .gitignore, docs finais, tag v0.6 | Fase 8 + 9 |
