# ROADMAP.md

## Milestone 1: Stability and Configuration (Refactoring Base)
* **Status**: ⏳ Pending
* **Goal**: Garantir a estabilidade 24h sem crashes, retirar hardcodes do sistema via um INI. Exportar pacotes.

### Phase 1: Critical Robustness Patches (STAB 1-4)
* **Goal**: Corrigir runtime bugs para uso seguro ininterrupto.
* **Scope**: 
  - Corrigir unário mal formatado em retry loop (`ntries=+1`).
  - Corrigir referências inalcançáveis (`sys.exit(1)` após retorno no timeout).
  - Corrigir `NameError: datetime` em erros via parse_numeric com module references.
  - Revisar fator multiplicador x10 sob validação do SCPI manual.
* **Depends on**: N/A

### Phase 2: Configuration Externalisation (STAB 5)
* **Goal**: Todo parâmetro duro entra num arquivo `config.ini`.
* **Scope**:
  - `config.ini` contendo IPs/portas/canais/delay/scan intervals, e coeficientes (Shunt ohms, M e B param etc se não autocalculados).
  - Adaptação das layers para load parsing via `configparser`.
* **Depends on**: Phase 1

### Phase 3: Packaging and Logging Standards (STAB 6-7)
* **Goal**: Criar reproducibilidade local e tracking trace de console.
* **Scope**:
  - Gerar e versionar `environment.yml` e `requirements.txt`.
  - Replace em instâncias de print statements crus por `logging.getLogger` nativo em output diário (`RotatingFileHandler`).
* **Depends on**: Phase 2

## Milestone 2: GUM and Confidence Visuals
* **Status**: ⏳ Pending
* **Goal**: Apresentação visual rigorosa das leituras do sensor ao vivo.

### Phase 4: Bokeh Sensor Buffer Logic
* **Goal**: Configurar SensorV2.py state para preservar histórico de "buffer em andamento".
* **Scope**: Modificar o consumer data de stream para carregar um RingBuffer da última hora e poder projetar CI/Rolling metrics antes de atualizar interface.
* **Depends on**: Phase 3

### Phase 5: GUM 95% Confidence Band (VIS-01)
* **Goal**: Usar o cálculo GUM K=2 existente do SensorV2 para projetar Upper e Lower bands no canvas principal.
* **Scope**: Adicionar visualização estilo 'band' (`1.96 / k=2` envelope interval) usando VArea / Band plotting functions do Bokeh vinculados ao sensor stream source.
* **Depends on**: Phase 4

## Milestone 3: ARIMA Forecasting integration
* **Status**: ⏳ Pending
* **Goal**: Estatística avançada (ARIMA models baseados na janela móvel) de predição curta em ambiente background.

### Phase 6: ARIMA Engine Design (VIS-02a)
* **Goal**: Desenvolver o engine estatístico contínuo local.
* **Scope**: Criar worker methods (ex: `statsmodels.tsa.arima`) baseadas nas leituras na thread, fittando via grid um `ARIMA(2,0,1)` e retornando next 60 blocks de step, acompanhando intervalos de erro com alpha 0.05.
* **Depends on**: Phase 5

### Phase 7: ARIMA Visual Integration (VIS-02b)
* **Goal**: Visualizar tracejado da predição futura sobre o chart real.
* **Scope**: Bokeh ColumnDataSource modificado e extendido com patch p/ incluir os tempos T+i, plotando curva primária (valor esperado) + VArea de projeção estatística na mesma UI sem congelar MainLoop do backend.
* **Depends on**: Phase 6

### Phase 8: Dashboard Features Enhancements (VIS 3-4)
* **Goal**: Fechamento do Visualizer (Dynamic roll-overs and connections checks).
* **Scope**: Expor timeout labels ou green dots se GPIB alive via thread flags. Adicionar text field / spinbox input pro bokeh que defina live "Rollover Size".
* **Depends on**: Phase 7

## Milestone 4: Historical GUI Extension
* **Status**: ⏳ Pending
* **Goal**: Upgrade de features análogas da camada ao vivo para o viewer histórico local em Tkinter/mpl.

### Phase 9: VarAmbseries Upgrades
* **Goal**: Levar as capacidades stats pro explorador offile de arquivos.
* **Scope**: Atualizar a GUI app de processamento `VarAmbseries` atual com checkboxes para prever e projetar GUM confianças na UI via matplotlib `fill_between()`. Aprimoramento do file export p/ incluir esses limites calculados.
* **Depends on**: Phase 8

### Phase 10: Final Deployment Checks (Docs & Releases)
* **Goal**: Wrapup versão.
* **Scope**: Validar testes E2E do launcher script nas bats, checar `.gitignore`, finalizar a README.md (atualizar para utf-8 ao invés de UTF-16LE se aplicavel) registrando dependências e premissas. Refactoring de arquivos .bat caso necessário.
* **Depends on**: Phase 9
