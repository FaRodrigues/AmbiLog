#!/usr/bin/env python3
import time
from collections import deque
import pyvisa
import re
import sympy as sym
import numpy as np
from datetime import datetime as dtime
import os
import xml.etree.ElementTree as ET
import configparser
from astropy.time import Time
from pyvisa.errors import VisaIOError
from streamingLab.logger_config import setup_logger

logger = setup_logger('LabVariab')

# --- GUM Uncertainty Constants (Certificados DIMCI 2023) ---
K_ABRANGENCIA = 2
U_CAL_TEMP = 0.20   # °C (Tcb / Tca)
U_CAL_RH = 1.11     # %ur (Rha / Rhb)
RESOLUCAO = 0.01    # Unidade padrão
u_res = (RESOLUCAO / 2) / np.sqrt(3) # Incerteza padrão da resolução

def get_sigma(label):
    u_cal = (U_CAL_RH if 'RH' in label else U_CAL_TEMP) / K_ABRANGENCIA
    uc = np.sqrt(u_cal**2 + u_res**2)
    return round(K_ABRANGENCIA * uc, 2)

# --- Configuration Load ---
config = configparser.ConfigParser()
config.read('config.ini')

# ----- Time & Path Utilities -----
def update_time_properties():
    datetimenow = Time(dtime.now())
    data = dtime.now().date()
    short_year = data.year - 2000
    doy = dtime.now().timetuple().tm_yday
    mjd = int(datetimenow.to_value('mjd'))
    return {'datetimenow': datetimenow, "date": data, "shortyear": short_year, "doy": doy, "mjd": mjd}

def ensure_xml_file():
    global current_doy, current_shortyear, current_xmlpath, datetime_now
    props = update_time_properties()
    current_doy = props['doy']
    current_shortyear = props['shortyear']
    datetime_now = props['datetimenow']

    rootdir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'varamblog'))
    os.makedirs(rootdir, exist_ok=True)
    day_dir = os.path.join(rootdir, f"{current_shortyear:02d}{current_doy:03d}")
    os.makedirs(day_dir, exist_ok=True)

    xml_path = os.path.join(day_dir, f"log_ambientvars-{current_shortyear}{current_doy}.xml")

    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            tree = ET.ElementTree(ET.Element('ambientvariables', datetime=str(datetime_now)))
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    else:
        tree = ET.ElementTree(ET.Element('ambientvariables', datetime=str(datetime_now)))
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)

    current_xmlpath = xml_path
    return tree, xml_path

def update_xml_from_dict(tree, measures):
    for m in measures:
        node = ET.SubElement(tree.getroot(), 'measure', timestamp=str(dtime.now()))
        for k, v in m.items():
            sub = ET.SubElement(node, k)
            if v is not None:
                sub.text = f"{v:.2f}" # Garante precisão de 2 casas decimais
            else:
                sub.text = "None"
    tree.write(current_xmlpath, encoding='utf-8', xml_declaration=True)


def safe_parse_scientific(s):
    # Remove caracteres estranhos
    s = s.strip().replace('*','').replace('D','E')
    # Se terminar em 'E' sem expoente, assume expoente zero
    if re.match(r'.*[eE]$', s):
        s = s + '0'
    try:
        return float(s) * 10 # Multiplicador de escala corrigido para v0.5/0.6 (conforme v0.4 original)
    except ValueError:
        # Loga e retorna NaN para não interromper o loop
        logger.error(f"Erro parseando '{s}'")
        return float('nan')


def decode_to_dict(val, rnd):
    parts = [v for v in val.strip().split(',') if v.strip()]
    res = {}
    for i, key in enumerate(list(dictprop.keys())):
        if i < len(parts):
            num = safe_parse_scientific(parts[i]) 
            if not np.isnan(num):
                res[key] = round(num, rnd)
                res[f"SIGMA_{key}"] = get_sigma(key)
            else:
                res[key] = None
                res[f"SIGMA_{key}"] = None
        else:
            res[key] = None
            res[f"SIGMA_{key}"] = None
    return res


# ----- Measurement Conversion Setup -----
amp_min = config.getfloat('CALIBRATION', 'amp_min', fallback=4)
amp_max = config.getfloat('CALIBRATION', 'amp_max', fallback=20)
slicef = config.getfloat('CALIBRATION', 'slicef', fallback=10000)
unit_scale = config.getfloat('CALIBRATION', 'unit_scale', fallback=1e3)
amps = np.arange(amp_min * slicef, (amp_max * slicef) + 1) / slicef / unit_scale
shunt = config.getfloat('CALIBRATION', 'shunt', fallback=268)
volts = amps * shunt

M, B = sym.symbols('M B')
sol_t = sym.solve([
    sym.Eq(M * volts[0] + B, -20),
    sym.Eq(M * volts[-1] + B,  80)
], (M, B))
MT, BT = float(sol_t[M]), float(sol_t[B])

sol_h = sym.solve([
    sym.Eq(M * volts[0] + B,   0),
    sym.Eq(M * volts[-1] + B, 100)
], (M, B))
MH, BH = float(sol_h[M]), float(sol_h[B])

chan_rha = config.getint('SENSORS', 'chan_rha', fallback=101)
chan_tca = config.getint('SENSORS', 'chan_tca', fallback=102)
chan_rhb = config.getint('SENSORS', 'chan_rhb', fallback=103)
chan_tcb = config.getint('SENSORS', 'chan_tcb', fallback=104)

dictprop = {
    'RHA': [chan_rha, MH, BH],
    'TCA': [chan_tca, MT, BT],
    'RHB': [chan_rhb, MH, BH],
    'TCB': [chan_tcb, MT, BT],
}

# ----- VISA & 34970A Setup -----
rm = pyvisa.ResourceManager()
gpib_address = config.get('HARDWARE', 'gpib_address', fallback='GPIB0::5::INSTR')
inst = rm.open_resource(gpib_address)
timeout_val = config.getint('HARDWARE', 'timeout', fallback=60000)
inst.timeout = timeout_val

# Extract scan logic configs
scan_interval = config.getint('LOGGING', 'scan_interval_seconds', fallback=30)
retry_wait = config.getint('LOGGING', 'retry_wait_seconds', fallback=5)
max_retries = config.getint('LOGGING', 'max_retries', fallback=10)

chans_str = f"(@{chan_rha},{chan_tca},{chan_rhb},{chan_tcb})"

cfg = deque([
    '*CLS',
    'SYST:PRESet',
    'FORM:READ:CHAN OFF',
    'FORM:READ:TIME ON',
    'FORM:READ:TIME:TYPE RELative',
    'FORM:READ:ALARm OFF',
    f'CONF:VOLT:DC 10,0.001,{chans_str}',
    f'SENS:VOLT:DC:NPLC 1,{chans_str}',
    f'ROUT:SCAN {chans_str}',
    'ROUT:CHAN:DELAY 0.1',
    'TRIG:SOURCE TIMER',
    'TRIG:TIMER 1',
    'TRIG:COUNT 1',
])
for label, (ch, g, o) in dictprop.items():
    cfg.extend([
        f'CALC:SCAL:GAIN {g},(@{ch})',
        f'CALC:SCAL:OFFSET {o},(@{ch})',
        f"CALC:SCAL:UNIT '{label}',(@{ch})",
        f'CALC:SCAL:STATE ON,(@{ch})',
    ])
cfg.append('INIT')
for cmd in cfg:
    inst.write(cmd)
    time.sleep(0.1 if cmd not in ('*CLS','INIT') else 0.5)

# ----- Main Data Loop -----
tree, xml_path = ensure_xml_file()
while True:
    new_tree, new_path = ensure_xml_file()
    if new_path != xml_path:
        tree, xml_path = new_tree, new_path

    try:
         # --- Bloco de retry para leitura VISA ---
        for attempt in range(max_retries):
            try:
                inst.write(f'CALC:AVER:AVER? {chans_str}')
                time.sleep(scan_interval)
                resp=inst.read()
                break
            except VisaIOError as e:
                logger.warning(f"TIMEOUT VISA (tentativa {attempt+1}): {e}")
                time.sleep(retry_wait)
        else:
            logger.error(f"Falha após {max_retries} tentativas de leitura.")
            resp = ''
        # --- Fim do bloco de retry ---
                
        measures = decode_to_dict(resp, 2)
        logger.info(f"Measures: {measures}")
        update_xml_from_dict(tree, [measures])
        inst.write('INIT')
    except Exception as e:
        logger.error(f"No data or error: {e}")
    time.sleep(1)
