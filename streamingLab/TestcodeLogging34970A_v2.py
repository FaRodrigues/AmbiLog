import glob
import os
import time
import xml.etree.ElementTree as ET
import configparser
from logger_config import setup_logger

logger = setup_logger('XMLParser')
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

XML_RETRY_SECONDS = config.getint('LOGGING', 'xml_retry_seconds', fallback=10)
XML_MAX_RETRIES = config.getint('LOGGING', 'xml_max_retries', fallback=50)

class Datalog:  # Agilent 34970A format XML August 2024

    def __init__(self, directory):
        self.directory = directory

    def get_folders_in_directories_recursively(self, index=0):
        folder_list = []
        for path, subdirs, _ in os.walk(self.directory):
            depth = path[len(self.directory):].count(os.sep)
            if index == 0 or depth == index:
                for sdirs in subdirs:
                    folder_path = os.path.join(path, sdirs)
                    folder_list.append(folder_path)
        return folder_list

    def list_file(self):
        folder_list = self.get_folders_in_directories_recursively(0)
        ntries=1
        if not folder_list:
            logger.warning("Nenhuma pasta encontrada.")
            return

        latest_folder = folder_list[-1]
        logger.info(f"Última pasta: {latest_folder}")

        # Lista arquivos XML na última pasta
        file_pattern = os.path.join(latest_folder, '*.xml')
        file_list = glob.glob(file_pattern)

        if not file_list:
            logger.warning("Nenhum arquivo XML encontrado.")
            return

        # Encontra o arquivo mais recente
        latest_file = max(file_list, key=os.path.getmtime)
        logger.debug(f"Último arquivo: {latest_file}")

        try:
            # Encontra o último antes do loop e já parseia
            tree = ET.parse(latest_file)
            
            # Verifica e extrai informações do XML
            for retry in range(XML_MAX_RETRIES): # to avoid time lapse for first entries into xml new day
                time.sleep(XML_RETRY_SECONDS)
                
                logger.info(f"Wait, retrying #{ntries}")
                ntries += 1

                latest_folder = folder_list[-1]
                file_pattern = os.path.join(latest_folder, '*.xml')
                file_list = glob.glob(file_pattern)

                if file_list:
                    latest_file = max(file_list, key=os.path.getmtime)
                    logger.debug(f"Último arquivo: {latest_file}")
                    
                    # Ensure we re-parse on every retry to catch new elements!
                    tree = ET.parse(latest_file)

                root = tree.getroot()
                
                last_measure = root[-1]
                if len(root) >= 1:
                    rha = float(last_measure.find('RHA').text) if last_measure.find('RHA') is not None else None
                    tca = float(last_measure.find('TCA').text) if last_measure.find('TCA') is not None else None
                    rhb = float(last_measure.find('RHB').text) if last_measure.find('RHB') is not None else None
                    tcb = float(last_measure.find('TCB').text) if last_measure.find('TCB') is not None else None
                    timestamp = last_measure.get("timestamp")
                    logger.debug(f"XML Parsed: {rha}, {tca}, {rhb}, {tcb}, {timestamp}")
                    return rha, tca, rhb, tcb, timestamp
            else:
                logger.error("Estrutura XML inesperada.")
                return None

        except ET.ParseError as e:
            logger.error(f"Erro ao parsear XML: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return None

# Exemplo de uso
# datalog = Datalog('/caminho/para/diretorio')
# datalog.list_file()
