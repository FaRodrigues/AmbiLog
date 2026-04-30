

 #   definePlot()
  #      Create two graphs to plot values against time
   #     x-axis of the second graph is linked to the first graph via the command x_range=p1.x_range
    #    First graph plots raw sensor data
     #   Second graph plots processed sensor data (in the left y-axis) and classification results (in the right y-axis)
      #  Places the two graphs into a gridplot for vertical alignment
    #update()
     #   This function will be called by the Sensor thread whenever new data is available for adding into the time plot
      #  New data points for each graph is structured into a dictionary
       # The graphs are updated by feeding the dictionary into a stream as given by self.source.stream(new_data, rollover=20) with a rollover period
        #The plots will be only be updated if the self.updateValue is True
    #checkbox1Handler()
     #   This function will be invoked whenever there is a change to the checkboxes’s state
      #  If the first checkbox transitions from ‘unticked’ to ‘ticked’, then the Sensor thread will be restarted
       # If the first checkbox is unticked, then the Sensor thread will be terminated by clearing the Flag
        #If the second checkbox is ticked, the Bokeh server will enable updating of the graphs
    #layout()
     #   Define two checkboxes and their handler/callback function, namely checkbox1Handler()
      #  Position the text, checkboxes, and graphs into a nice layout
       # Add the layout to the web document to be served to the browser by the Bokeh server

# Visual.py

from bokeh.plotting import figure
from bokeh.models import (LabelSet, DatetimeTickFormatter, LinearAxis, Range1d, 
                          HoverTool, ColumnDataSource, Legend, Text, Label)
from bokeh.layouts import gridplot, column, row
from bokeh.models.widgets import CheckboxGroup, Div, Toggle
from bokeh.io import curdoc
from tornado import gen
from datetime import timedelta, datetime

class Visual:
    def __init__(self, callbackFunc, running):
        header_html = """
        <div style="background: linear-gradient(90deg, #bbd2c5 0%, #536976 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-family: 'Inter', 'Roboto', sans-serif;
                    font-weight: 600;
                    margin-bottom: 0;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
                    font-size: 26px;">
            Monitoramento em Tempo Real: Temperatura e Umidade com Incerteza de Medição
        </div>
        """
        self.text1 = Div(text=header_html, sizing_mode="stretch_width", height=50)
        self.running = running
        self.callbackFunc = callbackFunc
        self.hover = HoverTool(
                tooltips=[
                    ("Timestamp", "@DateTime{%d/%m %H:%M:%S}"),
                    ("Valor", "$y"),
                ],
                formatters={'@DateTime': 'datetime'}
            )
        self.tools = "pan,box_zoom,wheel_zoom,reset"
        self.plot_options = dict(sizing_mode="stretch_width", height=400, tools=[self.hover, self.tools])
        self.updateValue = True
        self.predict_enabled = False
        self.label_opts=dict(x=0, y=0, x_units='screen', y_units='screen')
        self.caption = Label(text="Canais", **self.label_opts)

        self.source, self.pAll = self.definePlot()
        self.doc = curdoc()
        self.doc.theme = 'dark_minimal'
        self.layout()
        
    def definePlot(self):
        p1 = figure(**self.plot_options, title=None)
        p1.yaxis.axis_label = "Temperatura (°C)"
        p1.xaxis.formatter = DatetimeTickFormatter(
            months="%d/%m %H:%M", days="%d/%m %H:%M", hours="%d/%m %H:%M", minutes="%H:%M:%S"
        )
         
        p2 = figure(**self.plot_options, x_range=p1.x_range, title=None) # Link x-axis
        p2.xaxis.axis_label = "Tempo (dd/mm HH:MM)"
        p2.yaxis.axis_label = "Umidade Relativa (%ur)"
        p2.xaxis.formatter = DatetimeTickFormatter(
            months="%d/%m %H:%M", days="%d/%m %H:%M", hours="%d/%m %H:%M", minutes="%H:%M:%S"
        )
         
        # MODIFICADO: Adicionadas colunas para os limites das barras de erro
        source_data = dict(
            DateTime=[datetime.now()], 
            y1=[0], y1_upper=[0], y1_lower=[0],  # Temp A
            y2=[0], y2_upper=[0], y2_lower=[0],  # Temp B
            y3=[0], y3_upper=[0], y3_lower=[0],  # Umid A
            y4=[0], y4_upper=[0], y4_lower=[0]   # Umid B
        )
        source = ColumnDataSource(data=source_data)
        
        # Source para o forecast
        pred_data = dict(
            DateTime=[], 
            y1=[], y1_upper=[], y1_lower=[],
            y2=[], y2_upper=[], y2_lower=[],
            y3=[], y3_upper=[], y3_lower=[],
            y4=[], y4_upper=[], y4_lower=[]
        )
        pred_source = ColumnDataSource(data=pred_data)

        # Gráfico 1: Temperatura
        p1_pred_band_A = p1.varea(x='DateTime', y1='y1_lower', y2='y1_upper', source=pred_source, fill_color="salmon", fill_alpha=0.1)
        p1_pred_line_A = p1.line(x='DateTime', y='y1', source=pred_source, color="salmon", line_width=2, line_dash="dashed")
        
        r1_band = p1.varea(x='DateTime', y1='y1_lower', y2='y1_upper', source=source, fill_color="firebrick", fill_alpha=0.2)
        r1 = p1.line(x='DateTime', y='y1', source=source, color="firebrick", line_width=2)
        r1a = p1.circle(x='DateTime', y='y1', source=source, color="firebrick", fill_color="white", size=8)

        p1_pred_band_B = p1.varea(x='DateTime', y1='y2_lower', y2='y2_upper', source=pred_source, fill_color="lightskyblue", fill_alpha=0.1)
        p1_pred_line_B = p1.line(x='DateTime', y='y2', source=pred_source, color="lightskyblue", line_width=2, line_dash="dashed")

        r1b_band = p1.varea(x='DateTime', y1='y2_lower', y2='y2_upper', source=source, fill_color="lightskyblue", fill_alpha=0.3)
        r1b = p1.line(x='DateTime', y='y2', source=source, color="lightskyblue", line_width=2)
        r1c = p1.circle(x='DateTime', y='y2', source=source, color="indigo", size=8)

        # Gráfico 2: Umidade
        p2_pred_band_A = p2.varea(x='DateTime', y1='y3_lower', y2='y3_upper', source=pred_source, fill_color="lightgreen", fill_alpha=0.1)
        p2_pred_line_A = p2.line(x='DateTime', y='y3', source=pred_source, color="lightgreen", line_width=2, line_dash="dashed")

        r2_band = p2.varea(x='DateTime', y1='y3_lower', y2='y3_upper', source=source, fill_color="darkgreen", fill_alpha=0.2)
        r2 = p2.line(x='DateTime', y='y3', source=source, color="darkgreen", line_width=2)
        r2a = p2.circle(x='DateTime', y='y3', source=source, color="darkgreen", fill_color="white", size=8)

        p2_pred_band_B = p2.varea(x='DateTime', y1='y4_lower', y2='y4_upper', source=pred_source, fill_color="orange", fill_alpha=0.1)
        p2_pred_line_B = p2.line(x='DateTime', y='y4', source=pred_source, color="orange", line_width=2, line_dash="dashed")

        r2b_band = p2.varea(x='DateTime', y1='y4_lower', y2='y4_upper', source=source, fill_color="orange", fill_alpha=0.3)
        r2b = p2.line(x='DateTime', y='y4', source=source, color="orange", line_width=2)
        r2c = p2.circle(x='DateTime', y='y4', source=source, color="saddlebrown", size=8)
        
        # Legendas
        legend1 = Legend(items=[
            ("Temp. Sensor A", [r1_band, r1, r1a]),
            ("Temp. Pred A", [p1_pred_band_A, p1_pred_line_A]),
            ('Temp. Sensor B', [r1b_band, r1b, r1c]),
            ("Temp. Pred B", [p1_pred_band_B, p1_pred_line_B])
        ], location="top_left", orientation="horizontal")
        p1.add_layout(legend1, 'above')
        p1.legend.click_policy = "hide"

        legend2 = Legend(items=[
            ("Umid. Sensor A", [r2_band, r2, r2a]), 
            ("Umid. Pred A", [p2_pred_band_A, p2_pred_line_A]),
            ('Umid. Sensor B', [r2b_band, r2b, r2c]),
            ("Umid. Pred B", [p2_pred_band_B, p2_pred_line_B])
        ], location="top_left", orientation="horizontal")
        p2.add_layout(legend2, 'above')
        p2.legend.click_policy = "hide"

        pAll = gridplot([[p1], [p2]], sizing_mode="stretch_width")
        self.pred_source = pred_source
        return source, pAll

    @gen.coroutine
    def update(self, tempa, tempb, rha, rhb, timestamp, err_tempa, err_tempb, err_rha, err_rhb):
        # MODIFICADO: A função agora recebe os valores de incerteza
        if self.updateValue and timestamp is not None:
            try:
                newx = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                
                # NOVO: Calcula os limites superior e inferior para as barras de erro
                new_data = dict(
                    DateTime=[newx],
                    y1=[tempa], y1_upper=[tempa + err_tempa], y1_lower=[tempa - err_tempa],
                    y2=[tempb], y2_upper=[tempb + err_tempb], y2_lower=[tempb - err_tempb],
                    y3=[rha],   y3_upper=[rha + err_rha],   y3_lower=[rha - err_rha],
                    y4=[rhb],   y4_upper=[rhb + err_rhb],   y4_lower=[rhb - err_rhb],
                )
                # MODIFICADO: A coluna y5 foi removida pois não estava sendo usada
                self.source.stream(new_data, rollover=100) # Aumentei o rollover para ver mais pontos
            except (ValueError, TypeError) as e:
                print(f"Erro ao processar novos dados para o gráfico: {e}")

    @gen.coroutine
    def update_predictions(self, data_dict):
        # Substitui os dados inteiramente com a nova forecast Array
        if self.predict_enabled:
            self.pred_source.data = data_dict
        else:
            # Clear se estiver desabilitado
            empty_dict = {k: [] for k in data_dict.keys()}
            self.pred_source.data = empty_dict

    def checkbox1Handler(self, attr, old, new):
        if 0 in list(new):
            if 0 not in list(old):
                self.running.set()
                self.callbackFunc(self, self.running)
        else:
            self.running.clear()
        
        self.updateValue = 1 in list(new)

    def togglePredictHandler(self, active):
        self.predict_enabled = active
        if not self.predict_enabled:
            # Limpa os plots preditivos na mesma hora
            empty_dict = {k: [] for k in self.pred_source.data.keys()}
            self.doc.add_next_tick_callback(lambda: self.pred_source.data.update(empty_dict))

    def layout(self):
        checkbox1 = CheckboxGroup(labels=["Iniciar/Parar Aquisição", "Iniciar/Parar Gráfico"], active=[0, 1])
        checkbox1.on_change('active', self.checkbox1Handler)
        
        self.toggle_predict = Toggle(label="Modo Preditivo (Markov / ARIMA): OFF", button_type="success", active=False)
        self.toggle_predict.on_change('active', lambda attr, old, new: self.togglePredictHandler(new))
        self.toggle_predict.on_click(lambda active: setattr(self.toggle_predict, 'label', f"Modo Preditivo (Markov / ARIMA): {'ON' if active else 'OFF'}"))
        
        # Estilização da linha de controles
        controls_row = row(checkbox1, self.toggle_predict, sizing_mode="stretch_width", margin=(10, 0, 20, 0))
        layout = column(self.text1, controls_row, self.pAll, sizing_mode="stretch_width") # MODIFICADO: Layout responsivo
        self.doc.title = "Monitoramento com Incerteza e Predição"
        self.doc.add_root(layout)