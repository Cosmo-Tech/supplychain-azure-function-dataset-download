from CosmoTech_Acceleration_Library.Accelerators.scenario_download.azure_function_main import generate_main
from cosmotech_api import Scenario

from ScenarioDownload import apply_update as update_dataset
from Supplychain.Generic.memory_folder_io import MemoryFolderIO
from Supplychain.Transform.from_dict_to_table import FromDictToTableConverter


def apply_update(content: dict, scenario_data: Scenario) -> dict:
    updated_dataset = update_dataset(content, scenario_data)

    # Default values to avoid error 500 if time info were not filed
    updated_dataset.setdefault('Configuration', [{}])
    updated_dataset['Configuration'][0].setdefault('SimulatedCycles', 1)
    updated_dataset['Configuration'][0].setdefault('StepsPerCycle', 1)

    # Using Dict -> Table to generate Demands tab
    r = MemoryFolderIO()
    w = MemoryFolderIO()
    r.files = updated_dataset
    with FromDictToTableConverter(reader=r, writer=w, simulation_id=None, keep_duplicate=True) as dt:
        dt.convert()
    columns_names = ['StockName', 'Step', 'PartId', 'SafetyStockLevels']
    columns = [{'field': _name} for _name in columns_names]
    for c in columns:
        if c['field'] in ['StockName', 'Step', 'PartId']:
            c['type'] = ['nonEditable', 'nonResizable']
        if c['field'] in ['SafetyStockLevels']:
            c['type'] = ['number']
            c['minValue'] = 0
    out = list()
    for element in w.files['Stocks']:
        out.append(dict(StockName=element['StockName'], Step=element['Step'], PartId=element['PartId'], SafetyStockLevels=element.get('SafetyQuantities',dict()).get('0',0)))
    return {'columns': columns, 'rows': sorted(out, key=lambda r: r['StockName'])}


main = generate_main(apply_update=apply_update)
