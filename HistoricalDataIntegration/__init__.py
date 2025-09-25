"""
Azure Function extension for SCH Link History Data and Simulation Results

1. Read historical data from input sheets (historicalDemands & historicalProduction)
2. Send directly to ADX without impacting simulation
3. Create merged tables for PowerBI visualization
"""

import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any

from CosmoTech_Acceleration_Library.Accelerators.scenario_download.azure_function_main import generate_main
from Supplychain.Generic.cosmo_api_parameters import CosmoAPIParameters
from Supplychain.Generic.csv_folder_writer import CSVWriter
from Supplychain.Generic.memory_folder_io import MemoryFolderIO
from Supplychain.Transform.from_table_to_dict import FromTableToDictConverter
from Supplychain.Transform.patch_dict_with_parameters import DictPatcher
from Supplychain.HistoricalData.historical_data_integrator import HistoricalDataIntegrator
from cosmotech_api import Scenario


def apply_update(content: dict, scenario_data: Scenario) -> dict:
    """
    Apply_update function that processes historical data from input sheets.
    
    This function follows the reporter's approach:
    1. Process historicalDemands and historicalProduction sheets
    2. Send historical data directly to ADX
    3. Continue with normal simulation processing
    """
    dataset_content = content
    
    for dataset_id, dataset in content['datasets'].items():
        if dataset['type'] in ['adt', 'twincache']:
            dataset_content = dataset['content']
            continue
        if dataset['name'] == 'mass_lever_excel_file':
            mass_action_lever_content = dataset['content']
            _r = MemoryFolderIO()
            _r.files = mass_action_lever_content
            _w = MemoryFolderIO()
            with FromTableToDictConverter(reader=_r, writer=_w) as td:
                td.convert_all()
            dataset_content = _w.files
            break

    if _has_historical_sheets(dataset_content):
        _process_historical_sheets(scenario_data.id, dataset_content)

    tmp_parameter_dir = tempfile.mkdtemp()
    tmp_parameter_file = os.path.join(tmp_parameter_dir, "parameters.json")
    tmp_dataset_dir = tempfile.mkdtemp()

    parameters = []

    for parameter_name, value in content['parameters'].items():
        def add_file_parameter(compared_parameter_name: str):
            if parameter_name == compared_parameter_name:
                param_dir = os.path.join(tmp_parameter_dir, compared_parameter_name)
                os.mkdir(param_dir)
                _writer = CSVWriter(output_folder=param_dir)
                param_content = content['datasets'][value]['content']['content']
                _writer.write_from_list(param_content, 'content')
                parameters.append({
                    "parameterId": parameter_name,
                    "value": parameter_name,
                    "varType": "%DATASETID%"
                })

        add_file_parameter("demand_plan")
        add_file_parameter("transport_duration")
        add_file_parameter("production_resource_opening_time")
        
        if value in content['datasets']:
            continue
        parameters.append({
            "parameterId": parameter_name,
            "value": value,
            "varType": str(type(value))
        })

    with open(tmp_parameter_file, "w") as _file:
        json.dump(parameters, _file)

    _p = CosmoAPIParameters(parameter_folder=tmp_parameter_dir, dataset_folder=tmp_dataset_dir)

    reader = MemoryFolderIO()
    reader.files = dataset_content
    writer = MemoryFolderIO()

    handler = DictPatcher(reader=reader, writer=writer, parameters=_p)

    configuration = handler.memory.files['Configuration'][0]
    
    if scenario_data.run_template_id == "Lever":
        configuration['EnforceProductionPlan'] = True
        
    elif scenario_data.run_template_id == "MILPOptimization":
        _p.update_parameters([
            {
                'parameterId': 'stock_policy',
                'value': 'None',
                'varType': 'enum',
            },
            {
                'parameterId': 'stock_dispatch_policy',
                'value': 'None',
                'varType': 'enum',
            },
            {
                'parameterId': 'production_policy',
                'value': 'None',
                'varType': 'enum',
            },
        ])
        configuration['EnforceProductionPlan'] = False
        handler.handle_optimization_parameter()
        
    elif scenario_data.run_template_id == "UncertaintyAnalysis":
        configuration['EnforceProductionPlan'] = True
        configuration['ActivateUncertainties'] = True
        handler.handle_uncertainties_settings()

    _tmp_params = dict(_p.get_all_parameters())
    check = True
    for name in ['start_date', 'end_date', 'simulation_granularity']:
        if name not in _tmp_params:
            check = False
            break
    if check:
        handler.handle_simple_simulation()
    
    handler.handle_model_behavior()
    handler.handle_flow_management_policies()

    return writer.files


def _has_historical_sheets(dataset_content: dict) -> bool:
    """
    Check if the dataset contains historical data sheets.
    
    Args:
        dataset_content: Dataset content dictionary
        
    Returns:
        bool: True if historical sheets exist, False otherwise
    """
    return ('historicalDemands' in dataset_content or 
            'historicalProduction' in dataset_content or
            'historicalForecasts' in dataset_content or
            'historicalStocks' in dataset_content)


def _process_historical_sheets(simulation_run: str, dataset_content: dict) -> None:
    """
    Process historical data sheets and ingest into ADX.
    
    Args:
        simulation_run: Simulation run identifier
        dataset_content: Dataset content dictionary
    """
    try:
        integrator = HistoricalDataIntegrator()
        
        success = integrator.process_historical_sheets(simulation_run, dataset_content)
        
        if success:
            print(f"Successfully processed historical data sheets for simulation run: {simulation_run}")
        else:
            print(f"Warning: Some issues occurred while processing historical data sheets for simulation run: {simulation_run}")
        
    except Exception as e:
        print(f"Warning: Could not process historical data sheets: {e}")


main = generate_main(apply_update=apply_update, parallel=False)

