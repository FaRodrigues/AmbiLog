import glob
import os
import time
import xml.etree.ElementTree as ET
# Adapted for standard desviation
class Datalog:
    def __init__(self, directory):
        self.directory = directory

    def get_latest_xml_file(self):
        # Encontra a subpasta mais recente (formato YYDDD)
        root_dir = os.path.join(self.directory, 'varamblog')
        if not os.path.exists(root_dir):
            return None
            
        all_subdirs = [os.path.join(root_dir, d) for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
        if not all_subdirs:
            return None
        
        latest_folder = max(all_subdirs, key=os.path.getmtime)

        # Encontra o arquivo XML mais recente na pasta
        file_pattern = os.path.join(latest_folder, '*.xml')
        file_list = glob.glob(file_pattern)
        if not file_list:
            return None

        return max(file_list, key=os.path.getmtime)

    def list_file(self):
        ntries = 1
        # Tenta encontrar o arquivo por um tempo para dar chance de ser criado/atualizado
        for _ in range(5):
            latest_file = self.get_latest_xml_file()
            if latest_file:
                break
            print("Nenhum arquivo de log encontrado, tentando novamente em 5 segundos...")
            time.sleep(5)
        else:
            print("Arquivo de log não encontrado após várias tentativas.")
            return None

        try:
            tree = ET.parse(latest_file)
            root = tree.getroot()

            # Espera até que o arquivo tenha pelo menos uma medição
            while len(root.findall('measure')) == 0:
                print(f"Arquivo XML encontrado, mas vazio. Aguardando dados... (Tentativa {ntries})")
                time.sleep(10)
                tree = ET.parse(latest_file)
                root = tree.getroot()
                ntries += 1
                if ntries > 10:
                     print("Timeout: Nenhum dado de medição apareceu no arquivo XML.")
                     return None
            
            # Pega o último nó <measure>
            last_measure_node = root.find('.//measure[last()]')
            if last_measure_node is None:
                print("Nenhum nó de medição encontrado no XML.")
                return None

            timestamp = last_measure_node.get("timestamp")

            # ALTERADO: Busca os valores pelos nomes das tags para robustez
            def get_value(node, tag_name):
                found_node = node.find(tag_name)
                if found_node is not None and found_node.text:
                    return float(found_node.text)
                return 0.0 # Retorna 0.0 se a tag não for encontrada, para evitar erros

            # Médias
            rha = get_value(last_measure_node, 'RHA')
            tca = get_value(last_measure_node, 'TCA')
            rhb = get_value(last_measure_node, 'RHB')
            tcb = get_value(last_measure_node, 'TCB')

            # NOVO: Desvios Padrão
            sdev_rha = get_value(last_measure_node, 'SDEV_RHA')
            sdev_tca = get_value(last_measure_node, 'SDEV_TCA')
            sdev_rhb = get_value(last_measure_node, 'SDEV_RHB')
            sdev_tcb = get_value(last_measure_node, 'SDEV_TCB')

            print(f"Dados lidos do XML: {rha, tca, rhb, tcb, timestamp, sdev_rha, sdev_tca, sdev_rhb, sdev_tcb}")
            
            # Retorna a tupla de 9 elementos no formato esperado por SensorV2.py
            return (rha, tca, rhb, tcb, timestamp, sdev_rha, sdev_tca, sdev_rhb, sdev_tcb)

        except ET.ParseError as e:
            print(f"Erro ao parsear XML '{latest_file}': {e}")
            return None
        except Exception as e:
            print(f"Erro inesperado ao ler o arquivo de log: {e}")
            return None