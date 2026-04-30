import time
from collections import deque
import pyvisa
import sympy as sym
import numpy as np
from datetime import datetime
import sys
import os
from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as ET
from astropy.time import Time
from datetime import datetime as dtime

datetimeagora = 0
treex = ElementTree(ET.XML(f"<ambientvariables datetime='{datetimeagora}'></ambientvariables>"))
treelocal = ElementTree(ET.XML(f"<ambientvariables datetime='{datetimeagora}'></ambientvariables>"))
currentxmlpath = ""
currentdoy = 0
currentshortyear = 0


def updateTimeProperties():
    datetimenow = Time(dtime.now())
    # horario = dtime.now().time().isoformat(timespec="seconds")
    data = dtime.now().date()
    SHORTYEAR = data.year - 2000
    DOY = dtime.now().timetuple().tm_yday
    # print(f"horário = {horario} | date = {data} | SHORTYEAR = {SHORTYEAR} | DOY = {DOY} ")
    data1 = Time(str(datetimenow))
    MJD = int(data1.to_value('mjd'))
    return {'datetimenow': datetimenow, "date": data, "shortyear": SHORTYEAR, "doy": DOY, "mjd": MJD}


def updatePathProperties():
    timeupdatedict = updateTimeProperties()
    print(timeupdatedict)

    global currentdoy, treelocal, treex, currentxmlpath
    global currentshortyear
    global datetimeagora

    currentdoy = timeupdatedict['doy']
    currentshortyear = timeupdatedict['shortyear']
    datetimeagora = timeupdatedict['datetimenow']

    rootdir_for_log = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "varamblog"))

    if not os.path.exists(rootdir_for_log):
        os.mkdir(rootdir_for_log)

    ydaydir_for_log = os.path.join(rootdir_for_log,
                                   "{}{:03d}".format(currentshortyear, currentdoy))

    if not os.path.exists(ydaydir_for_log):
        os.mkdir(ydaydir_for_log)

    pathxmlcandidate = os.path.join(ydaydir_for_log,
                                    f"log_ambientvars-{currentshortyear}{currentdoy}.xml")

    print(f"pathxmlcandidate = {pathxmlcandidate}")

    if os.path.exists(pathxmlcandidate):
        # treex = ET.parse(pathxmlcandidate)
        treecandidate = ET.parse(pathxmlcandidate)
        # print(f"atributo = {treex.getroot().attrib}")
        time.sleep(1)
        datetimestring = treecandidate.getroot().attrib['datetime']
        # treecandidate = treex
        currentxmlpath = pathxmlcandidate
        try:
            datetime_object = datetime.strptime(datetimestring, '%Y-%m-%d %H:%M:%S.%f')
            lastdoy = datetime_object.timetuple().tm_yday
            nowdoy = datetimeagora.to_datetime().timetuple().tm_yday
            # if lastdoy < nowdoy:
            #     criarquivoXML(treex, pathxmlcandidate)
            # else:
            #     print("lastdoy >= nowdoy")

        except ValueError as ve1:
            print('ValueError 1:', ve1)
    else:
        currentxmlpath = pathxmlcandidate
        # criarquivoXML(treex, pathxmlcandidate)
        #print(datetimeagora)

        print(f"Criando arquivo XML com {str(datetimeagora)}")
        treecandidate = ElementTree(
            ET.XML(f"<ambientvariables datetime='{str(datetimeagora)}'></ambientvariables>"))
        #ET.indent(treex)
        treecandidate.write(currentxmlpath, encoding='utf-8', xml_declaration=True)

    return treecandidate, currentxmlpath


treeresploc, pathxmlresp = updatePathProperties()
print(f"path XML is {pathxmlresp}")
print(f"The currentshortyear is {currentshortyear}")
print(f"The currentdoy is {currentdoy}")
print(f"The datetimenow is {datetimeagora}")


def updateXmlFromDict(treelocalparam, dictlist):
    print(dictlist)
    # Itera sobre uma lista de dictmeasure. Cada dictmeasure contém um conjunto de medidas
    contador = 0
    for dictmeasure in dictlist:
        timestamp = datetime.now()
        measurenode = ET.Element('measure', attrib={"timestamp": str(timestamp)})
        for elem in dictmeasure:
            subnode = ET.SubElement(measurenode, elem)
            subnode.text = str(dictmeasure[elem])
        # print(ET.dump(measure))
        # Far uma inserção dos nós dictmeasure na raiz (memória) do XML definido em currentxmlpath.
        treelocalparam.getroot().append(measurenode)
        contador += 1
        print(f"COUNTER = {contador}")
    time.sleep(5)
    treelocalparam.write(currentxmlpath, encoding='utf-8', xml_declaration=True)

def safe_parse_scientific(s):
    # Remove caracteres estranhos
    s = s.strip().replace('*','').replace('D','E')
    # Se terminar em 'E' sem expoente, assume expoente zero
    if re.match(r'.*[eE]$', s):
        s = s + '0'
    try:
        return float(s) * 10
    except ValueError:
        # Loga e retorna NaN para não interromper o loop
        print(f"[{datetime.now().isoformat()}] Erro parseando '{s}'")
        return float('nan')

def decodeValueToDict(value, roundparam):
    dictresult = {}
    val = str(value).strip().split(",")
    for index in range(len(val)):
        v = val[index]
        xtrans = safe_parse_scientific(v)
        rxtrans = np.round(xtrans, roundparam)
        dictresult[list(dictprop.keys())[index]] = rxtrans
    return dictresult


dequetowrite = deque([])
dequetoread = deque([])
dequetoconfigure = deque([])

singlechannel = False

nomedohumidostato = "VAISALA"
ampmin = 4  # em mA
ampmax = 20  # em mA
slicefactor = 10000
unidade = 10 ** 3  # Ajuste para representação da tensão em Volts

# Em ampéres
Ampere = np.divide(np.divide(list(range(ampmin * slicefactor, (ampmax * slicefactor) + 1, 1)), slicefactor), unidade)
print(f"\nCorrente  =   {Ampere}", len(Ampere))
Shunt = 268  # Em ohms
Voltage = Ampere * Shunt
print(f"Voltagem  =   {Voltage}", len(Voltage), "\n")

# Cálculo para conversão - Temperatura
M, B = sym.symbols('M, B')
eq1 = sym.Eq(M * Voltage[0] + B, -20)
eq2 = sym.Eq(M * Voltage[-1] + B, 80)
resultForTemperature = sym.solve([eq1, eq2], (M, B))
MT = round(resultForTemperature[M], 5)
BT = round(resultForTemperature[B], 2)
print("Temperature => Gain MT = {} | Offset BT = {}".format(MT, BT))

# Cálculo para conversão - Uumidade
M, B = sym.symbols('M, B')
eq3 = sym.Eq(M * Voltage[0] + B, 0)
eq4 = sym.Eq(M * Voltage[-1] + B, 100)
resultForHumidity = sym.solve([eq3, eq4], (M, B))
MH = round(resultForHumidity[M], 5)
BH = round(resultForHumidity[B], 2)
print("Umidity => Gain MH = {} | Offset BH = {}".format(MH, BH))

numberMeasurements = 1  # Em calibração usar número maior
measurementDelay = 0.1
scanInterval = 1
numPLC =1 # 10

# For label rules see pág. 133 of Keysight 34970A/34972A User’s Guide
dictprop = {
    "RHA": [101, MH, BH],
    "TCA": [102, MT, BT],
    "RHB": [103, MH, BH],
    "TCB": [104, MT, BT],
}

rm = pyvisa.ResourceManager()
rm.list_resources()
inst34970A = rm.open_resource('GPIB0::5::INSTR')

dequetoconfigure.append("*CLS")
dequetoconfigure.append(":SYST:PRES")
dequetoconfigure.append(":FORM:READ:CHAN OFF")
dequetoconfigure.append(":FORM:READ:TIME OFF")

dequetoconfigure.append(":CONF:VOLT:DC 10,0.001,(@101,102,103,104)")
dequetoconfigure.append(
    f":SENS:VOLT:DC:NPLC {numPLC},(@101,102,103,104)")  # Ver pág 133 do Keysight 34970A/34972A User’s Guide
dequetoconfigure.append(":ROUT:SCAN (@101,102,103,104)")
dequetoconfigure.append(f":ROUT:CHAN:DELAY {measurementDelay}")
# dequetoconfigure.append("TRIG:SOUR BUS")
# dequetoconfigure.append("INIT")

dequetoconfigure.append(":TRIG:SOURCE TIMER")  # Select the interval timer configuration
dequetoconfigure.append(f":TRIG:TIMER {scanInterval}")  # Set the scan interval in seconds
dequetoconfigure.append(f":TRIG:COUNT {numberMeasurements}")  # Sweep the scan list 2 times (Number of SCANs)

for chave in dictprop.keys():
    param = dictprop[chave]
    canal = param[0]
    gain = param[1]
    offset = param[2]
    dequetowrite.append(f":CALC:SCAL:GAIN {gain},(@{canal})")  # ''' configura medida de humidade '''
    dequetowrite.append(f":CALC:SCAL:OFFSET {offset},(@{canal})")
    dequetowrite.append(f":CALC:SCAL:UNIT '{chave}',(@{canal})")
    dequetowrite.append(f":CALC:SCAL:STATE ON,(@{canal})")

dequetowrite.append(":SYST:TIME {:02d},{:02d},{:02d}".format(14, 40, 00))
dequetowrite.append(":SYST:DATE {},{:02d},{:02d}".format(2024, 4, 19))
dequetowrite.append(":INIT")

# Open data log file
f = open("data_log.txt", 'w')

for comando in dequetoconfigure:
    print(comando)
    inst34970A.write(comando)
    if comando == "*CLS":
        time.sleep(0.5)
    else:
        time.sleep(0.1)

time.sleep(1)

for comando in dequetowrite:
    print(comando)
    time.sleep(0.1)
    inst34970A.write(comando)

channelist = deque([101, 102, 103, 104])

para = False

timeforwait = 1 * numPLC * round(
    4 * (numberMeasurements * scanInterval) + 2 * (numberMeasurements - 1) * measurementDelay + 1)
print(f"Getting data time for each channel {timeforwait} secs\n")

count = 0
dequelistval = deque([])

while not para:
    inst34970A.write("DISP:TEXT 'SCAN ATIVADO'")
    time.sleep(15)
    print(inst34970A.query(":SYSTEM:TIME:SCAN?", delay=0.2))
    channel = channelist[0]
    # inst34970A.write("*TRG")  # Ativa o trigger
    num_data_pts = inst34970A.query("DATA:POINTS?", delay=0.2).replace("*", "").strip()
    print("Number of buffer pts: " + str(num_data_pts))
    print("Showing channel: {}".format(channel))
    numdatapts = int(num_data_pts)
    resposta = " "
    if numdatapts > 0:
        try:
            # resposta = inst34970A.query(f"DATA:REMOVE? {numdatapts}", delay=0.4)

            if numberMeasurements > 1:
                metodo = "CALC:AVER:AVER?"
                resposta = inst34970A.query(f"{metodo} (@101,102,103,104)", delay=0.2)
            else:
                metodo = "FETC?"
                resposta = inst34970A.query(f"{metodo}", delay=0.2)

            print(f"Measuremnt method {metodo}\n{resposta}")

            dictresp = decodeValueToDict(resposta, 2)
            print(f"Measuremnt method {metodo}\n{dictresp}")

            treeresploc, respath = updatePathProperties()

            
            listvals = list(dictresp.values())
            print(f"resposta: {listvals}\n")
            print([listvals[0]],"\n")

            dequelistval.append(dictresp)
            print(f"List of outputs {dequelistval}")
            count += 1
            # print(f"Contador = {count} | {len(dequelistval)}")
            if count % 2 == 0: #control of numbers of measures for each round to be outpt to xml file
                print(f"Last measurement processed  {count} measures")
                updateXmlFromDict(treeresploc, dequelistval)
                dequelistval.clear()
                count = len(dequelistval)

            inst34970A.write("DISP:TEXT:CLE")
            inst34970A.write(f"ROUT:MON (@{channel})")
            inst34970A.write("ROUT:MON:STATE ON")
            inst34970A.write("INIT")  # Ativa o SCAN
        except:
            print("ERRORS")
    else:
        print("There is no data!")
    channelist.rotate(-1)
    time.sleep(timeforwait)
