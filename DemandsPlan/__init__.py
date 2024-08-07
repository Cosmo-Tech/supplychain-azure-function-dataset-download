from CosmoTech_Acceleration_Library.Accelerators.scenario_download.azure_function_main import generate_main
from Supplychain.Generic.memory_folder_io import MemoryFolderIO
from Supplychain.Transform.from_dict_to_table import FromDictToTableConverter
from cosmotech_api import Scenario

from ScenarioDownload import apply_update as update_dataset


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
    columns_names = ['id', 'Timestep', 'Demands', 'DemandUncertainties', 'DemandWeights']
    columns = [{'field': _name} for _name in columns_names]

    for c in columns:
        if c['field'] in ['id', 'Timestep']:
            c['type'] = ['nonEditable']
        if c['field'] in ['Demands', 'DemandUncertainties', 'DemandWeights']:
            c['type'] = ['number']
            c['minValue'] = 0

    return {'columns': columns, 'rows': w.files['Demands']}


main = generate_main(apply_update=apply_update)
