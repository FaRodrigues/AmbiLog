# SensorV2.py

import time
import threading
import numpy as np  # NOVO: Importado para cálculos
from functools import partial
import configparser
import os
from collections import deque

from TestcodeLogging34970A_v2 import Datalog
from logger_config import setup_logger

logger = setup_logger('SensorV2')
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

SCAN_INTERVAL = config.getfloat('LOGGING', 'scan_interval_seconds', fallback=30.0)
RETRY_WAIT = config.getfloat('LOGGING', 'xml_retry_seconds', fallback=10.0)
BUFFER_SIZE = config.getint('LOGGING', 'buffer_size_elements', fallback=120)

vars_reader = Datalog(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'varamblog')))

# --- INÍCIO: CONSTANTES DE INCERTEZA (GUM) ---
# NOVO: Dados extraídos dos certificados de calibração e datasheet

# Fator de abrangência usado nos certificados
K_ABRANGENCIA = 2

# -- Sensor A (Final P4020022, Certificado DIMCI 1403/2023) --
# Incerteza expandida da calibração (U)
U_CAL_TEMP_A = 0.20  # °C, valor máximo da Tabela 5 
U_CAL_RH_A = 1.11   # %ur, valor máximo das Tabelas 2-4 
# Incerteza padrão da calibração (u = U/k)
u_cal_temp_A = U_CAL_TEMP_A / K_ABRANGENCIA
u_cal_rh_A = U_CAL_RH_A / K_ABRANGENCIA

# -- Sensor B (Final P4020013, Certificado DIMCI 1404/2023) --
# Incerteza expandida da calibração (U)
U_CAL_TEMP_B = 0.20  # °C, valor máximo da Tabela 5 
U_CAL_RH_B = 1.11   # %ur, valor máximo das Tabelas 2-4 
# Incerteza padrão da calibração (u = U/k)
u_cal_temp_B = U_CAL_TEMP_B / K_ABRANGENCIA
u_cal_rh_B = U_CAL_RH_B / K_ABRANGENCIA

# -- Incerteza da Resolução do Medidor (Agilent 34970A) --
# Resolução informada nos certificados [cite: 38, 39, 225, 226]
RESOLUCAO_TEMP = 0.01  # °C
RESOLUCAO_RH = 0.01    # %ur
# Incerteza padrão da resolução (distribuição retangular)
u_res_temp = (RESOLUCAO_TEMP / 2) / np.sqrt(3)
u_res_rh = (RESOLUCAO_RH / 2) / np.sqrt(3)

# --- FIM: CONSTANTES DE INCERTEZA ---


class Sensor(threading.Thread):
    def __init__(self, callbackFunc, running):
        threading.Thread.__init__(self)
        self.daemon = True # NOVO: Garante o fim nativo do Python on Exit
        self.val = 20
        self.running = running
        self.callbackFunc = callbackFunc
        self.lock = threading.Lock()
        self.buffer = {
            'timestamp': deque(maxlen=BUFFER_SIZE),
            'tempa': deque(maxlen=BUFFER_SIZE),
            'tempb': deque(maxlen=BUFFER_SIZE),
            'rha': deque(maxlen=BUFFER_SIZE),
            'rhb': deque(maxlen=BUFFER_SIZE),
            'err_tempa': deque(maxlen=BUFFER_SIZE),
            'err_tempb': deque(maxlen=BUFFER_SIZE),
            'err_rha': deque(maxlen=BUFFER_SIZE),
            'err_rhb': deque(maxlen=BUFFER_SIZE)
        }

    def get_buffer(self):
        with self.lock:
            # Retorna uma cópia da queue via list comprehension pura
            return {k: list(v) for k, v in self.buffer.items()}

    def run(self):
        while self.running.is_set():
            time.sleep(SCAN_INTERVAL)
            varsall = vars_reader.list_file()

            if varsall is None:
                logger.warning(f"varsall is None. Tentando novamente em {RETRY_WAIT} segundos.")
                # MODIFICADO: Enviando Nones para todos os novos argumentos
                self.callbackFunc.doc.add_next_tick_callback(partial(self.callbackFunc.update, None, None, None, None, None, None, None, None, None))
                time.sleep(RETRY_WAIT)
                continue

            try:
                self.tempa = varsall[1]
                self.tempb = varsall[3]
                self.rha = varsall[0]
                self.rhb = varsall[2]
                self.timestamp = varsall[4]

                # --- INÍCIO: CÁLCULO DE INCERTEZA (GUM) ---
                # NOVO: Calculando a incerteza para cada ponto de medição

                # Incerteza combinada (u_c) = raiz da soma dos quadrados das incertezas padrão
                uc_temp_A = np.sqrt(u_cal_temp_A**2 + u_res_temp**2)
                uc_rh_A = np.sqrt(u_cal_rh_A**2 + u_res_rh**2)
                uc_temp_B = np.sqrt(u_cal_temp_B**2 + u_res_temp**2)
                uc_rh_B = np.sqrt(u_cal_rh_B**2 + u_res_rh**2)

                # Incerteza expandida (U) = k * u_c (Este é o valor para a barra de erro)
                self.err_tempa = K_ABRANGENCIA * uc_temp_A
                self.err_rha = K_ABRANGENCIA * uc_rh_A
                self.err_tempb = K_ABRANGENCIA * uc_temp_B
                self.err_rhb = K_ABRANGENCIA * uc_rh_B
                # --- FIM: CÁLCULO DE INCERTEZA ---

                # Atualiza o Buffer Background (Phase 4)
                with self.lock:
                    self.buffer['timestamp'].append(self.timestamp)
                    self.buffer['tempa'].append(self.tempa)
                    self.buffer['tempb'].append(self.tempb)
                    self.buffer['rha'].append(self.rha)
                    self.buffer['rhb'].append(self.rhb)
                    self.buffer['err_tempa'].append(self.err_tempa)
                    self.buffer['err_tempb'].append(self.err_tempb)
                    self.buffer['err_rha'].append(self.err_rha)
                    self.buffer['err_rhb'].append(self.err_rhb)

                # MODIFICADO: Adicionado o envio das incertezas para a função de update
                self.callbackFunc.doc.add_next_tick_callback(
                    partial(self.callbackFunc.update,
                            self.tempa, self.tempb, self.rha, self.rhb, self.timestamp,
                            self.err_tempa, self.err_tempb, self.err_rha, self.err_rhb)
                )
                logger.info(f"last Measures of ambient variables at {self.timestamp}:\nUmid A: {self.rha:.2f} ± {self.err_rha:.2f}\nTemp A: {self.tempa:.2f} ± {self.err_tempa:.2f}\nUmid B: {self.rhb:.2f} ± {self.err_rhb:.2f}\nTemp B: {self.tempb:.2f} ± {self.err_tempb:.2f}\n")

            except (IndexError, TypeError) as e:
                logger.error(f"os dados de 'varsall' estão incompletos ou em formato incorreto: {e}")
                # MODIFICADO: Enviando Nones para todos os novos argumentos
                self.callbackFunc.doc.add_next_tick_callback(partial(self.callbackFunc.update, None, None, None, None, None, None, None, None, None))
                time.sleep(RETRY_WAIT)
                continue

        logger.info("Sensor thread killed")