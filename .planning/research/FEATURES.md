# FEATURES.md — Features Research: LabVariab v0.6

## Table Stakes (must have — usuarios básicos do sistema esperam)

### Logger Robusto
- [ ] Rodar indefinidamente sem intervenção humana (24/7)
- [ ] Nunca perder medida por bug evitável (NameError, TypeError silencioso)
- [ ] Day-rollover automático de XML (já existe, mas com bug de árvore estática)
- [ ] Retry GPIB com feedback claro nos logs (não apenas print)
- [ ] GPIB address configurável sem editar código

### Dashboard Tempo Real
- [ ] Temperatura e umidade de 2 sensores em tempo real
- [ ] Barras de erro GUM visíveis (já existe em SensorV2.py/Visual.py)
- [ ] Indicador de status (sensor online / timeout / sem dados)
- [ ] Rollover configurável (não hardcoded 100 pontos)

### Análise Histórica
- [ ] Seleção de período por data/hora (já existe em VarAmbseries0.6.2.py)
- [ ] Estatísticas (média, mediana, min, max) exportadas em TXT (já existe)

## Differentiators (competitive advantage — o que torna este sistema cientificamente diferenciado)

### 95% Confidence Band em Tempo Real
- Banda de confiança sobre a série histórica visível no Bokeh
- Baseada em GUM (incerteza combinada propagada), não em estatística ingênua
- Fator k=2 conforme certificados DIMCI — rastreável metrológicamente
- **Complexidade**: Média — Band glyph no Bokeh + rolling window de u_c

### Forecast ARIMA 30 minutos
- Projeção de T e RH para os próximos 30 min (6 pontos a 30s de intervalo)
- Modelo ARIMA(p,d,q) fitado automaticamente via auto_arima ou grid-search leve
- Banda de incerteza do forecast propagada (GUM + variância do modelo)
- Exibido como linha tracejada + sombra no dashboard Bokeh
- **Complexidade**: Alta — requer statsmodels, thread-safe callback, refit periódico

### Configuração Externalizada
- `config.ini` com todos os parâmetros do instrumento e dashboard
- Documentado com comentários — operável por técnico sem programação
- **Complexidade**: Baixa

### Logging Científico
- Módulo `logging` com RotatingFileHandler
- Níveis: INFO (medição normal), WARNING (retry), ERROR (crash, dado inválido)
- **Complexidade**: Baixa

## Anti-Features (coisas a deliberadamente NÃO construir)

| Anti-Feature | Por quê |
|-------------|---------|
| Banco de dados | XML é suficiente para a taxa atual (1 medida/30s). Adicionar DB é over-engineering |
| Interface web além do Bokeh | Bokeh já é web. Dupla interface = dupla manutenção |
| Autenticação/login | Sistema local de laboratório, não exposto à internet |
| HMM / estados discretos | T e RH são contínuos — Markov oculto não agrega |
| Monte Carlo propagation | GUM linear é suficiente (u_c já < linearização), conformidade DIMCI |
| Dashboard em Plotly/Dash | Troca de stack sem ganho claro — risco de quebrar o que funciona |
| Forecast > 30 min | Precisão degrada rapidamente; 30 min é o horizonte útil para operação |
| Múltiplos instrumentos | Out of scope desta versão |

## Dependency Map

```
Forecast 30min
  └── ARIMA em backgroundthread (statsmodels)
      └── Dados históricos XML (varamblog/)
          └── Logger robusto sem crashes
              └── Config externalizado (GPIB addr)

CI 95% em tempo real
  └── Band glyph Bokeh
      └── Rolling u_c GUM (numpy rolling)
          └── Constantes de incerteza do sensor (SensorV2.py — já tem)
```
