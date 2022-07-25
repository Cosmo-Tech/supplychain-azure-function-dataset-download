# supplychain-azure-function-dataset-download Function App


The **_supplychain-azure-function-dataset-download_** is a specialization for the Cosmo Tech Supply Chain solution of the the generic azure function app [_azure-function-scenario-download_](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This Supply Chain specific version is based on the [Cosmotech Azure function Scenario Download](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This azure function app aims to be integrated in the Cosmo Tech Supply Chain Web-app : [azure-supplychain-webapp](https://github.com/Cosmo-Tech/azure-supplychain-webapp) for Cosmo Tech internal use or [azure-supplychain-webapp-shared](https://github.com/Cosmo-Tech/azure-supplychain-webapp-shared) for external use


# Deploy the generic Supply Chain Azure Function App

## Pre-Requisites

- Dedicated App registration created (see details below)

<br>

### Dedicated app registration :
1. Create a new app registration
2. Add a API permission to the Cosmo Tech Platform API, choose the permission type *_Application_* (not *_Delegated_*) and select the permission *_Organization.user_*
3. Create a client secret
4. In the related Azure Digital Twins resources, assign the role _Azure Digital Twin Data Reader_  to app registration 
<br><br>

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FCosmo-Tech%2Fsupplychain-azure-function-dataset-download%2Fmain%2Fdeploy%2Fazuredeploy.json)

<br>

## Installation options

| Parameter            | Note                                                                                                                                                                                                                                       |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Subscription         | Choose same as the related platform and webapp                                                                                                                                                                                             |
| Resource group       | Choose same as the related platform and webapp                                                                                                                                                                                             |
| Region               | Choose same as related platform and webapp                                                                                                                                                                                                 |
| Site Name            | Choose a name for the function app or leave the default value for auto-generated name                                                                                                                                                      |
| Storage Account Name | Choose a name for the storage account required for the function app or leave the default value for auto-generated name                                                                                                                     |
| Location             | Location for the resources to be created (Function App, App Service plan and Storage Account)                                                                                                                                              |
| Csm Api Host         | Cosmo Tech Platform API host                                                                                                                                                                                                               |
| Csm Api Scope        | Scope for accessing the Cosmo Tech Platform API (must end with /.default)                                                                                                                                                                  |
| Az Cli ID	           | Client ID of the dedicated app registration (see pre-requisites)                                                                                                                                                                           |
| Az Cli Secret        | Client Secret create of the dedicated app registration (see pre-requisites)                                                                                                                                                                |
| Package Address      | URL of the Azure function package to be deployed  - IMPORTANT : pick the URL from the latest release, ex [release 2.1.10](https://github.com/Cosmo-Tech/supplychain-azure-function-dataset-download/releases/download/2.1.10/artifact.zip) |

<br>


## Configure CORS

### Request Credentials
Check option _*Enable Access-Control-Allow-Credentials*_

### Allowed Origins :
- Add the URL of the Cosmo Tech Supply Chain Web-App
- For dev usage (optional) add http://localhost:3000

<br>


# Secure the Azure Function

The azure function includes a first level of securizartion with the host key.<br>
This keys being included in the web application, we need a second layer of securization by limiting the azure function calls to the users being authorized to the Cosmo Tech API 

## Add identity provider

- Go to Authentication
- Add identity provider
- Select "Microsoft"
- In "App registration type", select "Pick an existing app registration in this directory"
- Name or app ID : enter the web application name.<br>
**Note** : You may need to enter the app registration ID created for the webapp instead of its name. And in this case, you will have to create a secret for the app registration of the web app and provide it here.
<br>

- Restrict access : "Require authentication"
- Unauthenticated requests : HTTP 401
- Token store : leave checked
<br>

## Configure audience
- In the created identity provider, click on "Edit"
- Allowed token audiences : Enter the appplication ID URL of the platform app registration (of type  "https://_*cosmo platform url*_" or "api://_*platform app registrion application id uri*_" ) 


# Integrate in the Cosmo Tech Supply Chain web-app


## Configure for the flowchart

### in file "src/config/AppInstance.js"

```javascript
export const AZURE_FUNCTION_FLOWCHART_URL =
  'https://<azure function deployment url>/api/ScenarioDownload';
export const AZURE_FUNCTION_FLOWCHART_HEADERS = {
  'x-functions-key': '<default host keys>',
};
```

## Configure for the lever tables

### in file "src/config/ScenarioParameters.js", for each lever table

Example with the demand plan table

```javascript
  demand_plan: {
    connectorId: 'c-ll43p5nll5xqx',
    defaultFileTypeFilter: '.csv',
    subType: 'AZURETABLE',
    azureFunction: 'https://<azure function deployment url>/api/DemandsPlan',
    azureFunctionHeaders: { 'x-functions-key': '<default host keys>' },
  }
```



# Build and deploy the function app using a specific Supply Chain library version 

## Change the Supply Chain Library dependency

By default, the azure function app references the Cosmo-Tech Supply Chain generic PyPi package [CosmoTech-SupplyChain](https://pypi.org/project/CosmoTech-SupplyChain/) from the [requirements.txt](./requirements.txt) file

In case, you need to use your own library version, you need to change this dependency by pointing to your own PyPi package or your specific git repository, like for exemple `git+ssh://git@github.com/<your repo>/supplychain-python-library.git@main#egg=SupplyChain`.

**Note** : in the azure function references in the [requirements.txt](./requirements.txt) file, you have to leave the dependency to the PyPi package `CosmoTech-Acceleration-Library` unchanged since this is one is generic.


## Build the specific azure function

The generic azure comes with an GitHub action allowing to automate its build and the generation of the artifact  `Artifact.zip`.
This automatic build is facilitated by the fact that the generic PyPi package is public.

When you change the library dependency to a private repository, you need to put in place credentials management to use your own repository.
You may find easier to simply build the azure function locally (using your git credentials)

```bash
pip install --target .python_packages/lib/site-packages/ -r requirements.txt
zip -r artifact.zip . -x ".git/*" ".github/*" ".gitignore"
```

## Deploy the new specific Azure Function version


In order to deploy the new artifact, you have to make it accessible for deployment from the azure function app instance through an https URL.

- if the build can be automated, URL can point to a GitHub release (like the generic azure function)<br />
Example URL : https://github.com/Cosmo-Tech/supplychain-azure-function-dataset-download/releases/download/2.2.2/artifact.zip

- if not, the artifact zip file can be copied to an azure blob storage<br />
example URL : https://myblobstorage.blob.core.windows.net/content/artifact.zip?st=2018-02-13T09%3A48%3A00Z&se=2044-06-14T09%3A48%3A00Z&sp=rl&sv=2017-04-17&sr=b&sig=bNrVrEFzRHQB17GFJ7boEanetyJ9DGwBSV8OM3Mdh%2FM%3D



Then to deploy the new artifact version, go to the azure function app settings in the Azure portal.<br />
Change the `WEBSITE_RUN_FROM_PACKAGE` parameter with the new artifact URL.

Or execute the following command from the Azure CLI
```bash
az webapp config appsettings set --name <function app name> --resource-group <resource group name> --settings WEBSITE_RUN_FROM_PACKAGE=<URL>
```

**Note** : The function app automatically restarts after a configuration change.
