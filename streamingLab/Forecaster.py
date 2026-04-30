import time
import threading
from functools import partial
import warnings
from datetime import timedelta, datetime
import numpy as np

from logger_config import setup_logger
from statsmodels.tsa.arima.model import ARIMA

logger = setup_logger('Forecaster')

class Forecaster(threading.Thread):
    def __init__(self, sensor, visual, scan_interval=30.0, forecast_points=60):
        threading.Thread.__init__(self)
        self.daemon = True # NOVO: Daemon flag anti-blocks ao encerrar pelo terminal
        self.sensor = sensor
        self.visual = visual
        self.scan_interval = scan_interval
        self.forecast_points = forecast_points
        self.running = threading.Event()
        self.sleep_interval = 60.0  # Run prediction every 60 seconds
        
    def start_forecasting(self):
        self.running.set()
        self.start()
        
    def stop(self):
        self.running.clear()
        
    def run(self):
        # Ignora avisos de convergência do ARIMA para não poluir o logger
        warnings.filterwarnings("ignore")
        
        while self.running.is_set():
            time.sleep(self.sleep_interval)
            
            if not self.visual.predict_enabled:
                continue
                
            buffer = self.sensor.get_buffer()
            timestamps_str = buffer.get('timestamp')
            
            # Necessita de um número mínimo de amostras para o ARIMA
            if not timestamps_str or len(timestamps_str) < 30: 
                continue
                
            last_timestamp_str = timestamps_str[-1]
            try:
                last_time = datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            except (ValueError, TypeError):
                continue
                
            # Projeção de timestamps no futuro (ex: próximos 30 min)
            future_times = [last_time + timedelta(seconds=self.scan_interval * (i+1)) for i in range(self.forecast_points)]
            predictions = {'DateTime': future_times}
            
            # MAPEAMENTO: 'tempa' -> 'y1', 'tempb' -> 'y2', 'rha' -> 'y3', 'rhb' -> 'y4'
            var_mapping = {
                'tempa': 'y1',
                'tempb': 'y2',
                'rha': 'y3',
                'rhb': 'y4'
            }
            
            for buffer_key, y_key in var_mapping.items():
                data = list(buffer[buffer_key])
                try:
                    # ARIMA(1, 1, 0) emula um comportamento random walk / AR1 com dif,
                    # modelando a essência estatística das cadeias de Markov adaptadas
                    model = ARIMA(data, order=(1, 1, 0))
                    fitted = model.fit()
                    forecast = fitted.get_forecast(steps=self.forecast_points)
                    mean = forecast.predicted_mean.values if hasattr(forecast.predicted_mean, 'values') else forecast.predicted_mean
                    conf_int = forecast.conf_int(alpha=0.05) # 95% Confidence Interval
                    
                    if hasattr(conf_int, 'values'):
                        conf_int = conf_int.values

                    predictions[y_key] = mean
                    predictions[f'{y_key}_lower'] = conf_int[:, 0]
                    predictions[f'{y_key}_upper'] = conf_int[:, 1]
                except Exception as e:
                    logger.error(f"Erro ao prever {buffer_key}: {e}")
                    # Caso de falha (matriz singular etc), emite linha constante
                    last_val = data[-1]
                    predictions[y_key] = [last_val] * self.forecast_points
                    predictions[f'{y_key}_lower'] = [last_val * 0.95] * self.forecast_points
                    predictions[f'{y_key}_upper'] = [last_val * 1.05] * self.forecast_points
                    
            # Submete a atualização das previsões ao Visual na thread do Bokeh
            self.visual.doc.add_next_tick_callback(
                partial(self.visual.update_predictions, predictions)
            )

        logger.info("Forecaster thread finalizada")
