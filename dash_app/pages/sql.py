import json

import dash
import pandas as pd
from dash import html, dcc, callback, Input, Output, ALL
import intersystems_iris.dbapi._DBAPI as dbapi
from dotenv import load_dotenv
load_dotenv()
import os
import dash_bootstrap_components as dbc
from datetime import datetime
from dash_table import DataTable

dash.register_page(__name__, title="Tables", name="Tables (SQL)",path="/tables")

password = os.getenv("SQL_PASSWORD")
user = os.getenv("SQL_USERNAME")
host = os.getenv("SQL_SERVER")
namespace = os.getenv("SQL_NAMESPACE")
port = os.getenv("SQL_PORT")
if isinstance(port, str):
    port = int(port)

config = {
    "hostname": host,
    "port": port,
    "namespace": namespace,
    "username": user,
    "password": password,
}

try:
    conn = dbapi.connect(**config)
    print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

# create a cursor
cursor = conn.cursor()
print("Cursor created successfully!")


layout = html.Div([
    html.H1('Tables (SQL)'),
    dbc.Row([
        dcc.Store(id='intermediate-valueSQL'),
        dcc.Interval(
            id='interval-componentSQL',
            interval=2*60*1000, # in milliseconds
            n_intervals=0
        ),
        html.Label(id='updatedSQL')
    ]),
    html.H3("FHIR Resources"),
    DataTable(
        id='resourceTable',
        data=[],
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")
    ),
    html.H3("Organisation Reports Counts"),
    DataTable(
        id='organisationTable',
        data=[],
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")
    ),
    html.H3("ICS Reports Counts"),
    DataTable(
        id='icsTable',
        data=[],
        style_cell=dict(textAlign='left'),
        style_header=dict(backgroundColor="paleturquoise"),
        style_data=dict(backgroundColor="lavender")
    )
])

@callback(
    [Output("resourceTable", "data"),
     Output('resourceTable', 'columns')],
    Input('intermediate-valueSQL', 'data')
)
def resourceTable(_value):
    print("update Resource Table called")
    if _value is None:
        return dash.no_update
    print("has Data")
    datasets = json.loads(_value)
    df = pd.read_json(datasets['dfResource'], orient='split')
    data = df.to_dict('records')
    return data, [{"name": i, "id": i} for i in df.columns]

@callback(
    [Output("organisationTable", "data"),
     Output('organisationTable', 'columns')],
    Input('intermediate-valueSQL', 'data')
)
def organisationTable(_value):
    print("update organisation Table called")
    if _value is None:
        return dash.no_update
    print("has Data")
    datasets = json.loads(_value)
    df = pd.read_json(datasets['dfOrg'], orient='split')
    data = df.to_dict('records')
    return data, [{"name": i, "id": i} for i in df.columns]

@callback(
    [Output("icsTable", "data"),
     Output('icsTable', 'columns')],
    Input('intermediate-valueSQL', 'data')
)
def icsTable(_value):
    print("update ICS Table called")
    if _value is None:
        return dash.no_update
    print("has Data")
    datasets = json.loads(_value)
    df = pd.read_json(datasets['dfICS'], orient='split')
    data = df.to_dict('records')
    return data, [{"name": i, "id": i} for i in df.columns]

@callback(
    Output('updatedSQL', 'children'),
    Output('intermediate-valueSQL', 'data'),
    Input('interval-componentSQL', 'n_intervals'))
def update_metrics(n):
    print("update_metrics called")
    print(n)
    updated = [html.P('Last updated ' +str(datetime.now()))]
    return updated,getData()

def getData():
    sql = """
          select ResourceType, count(*) Total from HSFHIR_X0001_R.Rsrc group by ResourceType \
          """

    cursor.execute(sql)
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    dfResource = pd.DataFrame(data, columns=column_names)

    sql = """
          select
              dr.ID1
               ,sr.requester_IdentifierValue ODS
               ,org.phonetic name
               ,org.partof_IdentifierValue ICS
               ,parent.phonetic ICSName
          from HSFHIR_X0001_S.DiagnosticReport dr                                             join HSFHIR_X0001_S_DiagnosticReport.basedOn drb on drb.Key = dr.Key               left outer join HSFHIR_X0001_S.ServiceRequest sr on drb.value_Reference=sr.key
                                                                                              left outer join HSFHIR_X0001_S.Organization org on org.key = sr.requester_RelativeRef                                                             left outer join HSFHIR_X0001_S.Organization parent on parent.key = org.partof_Reference \
          """

    cursor.execute(sql)
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=column_names)

    dfOrg = df.groupby(['ODS','name']).size().reset_index(name='Total')
    dfICS = df.groupby(['ICS','ICSName']).size().reset_index(name='Total')


    datasets = {
        'dfResource': dfResource.to_json(orient='split', date_format='iso'),
        'dfOrg': dfOrg.to_json(orient='split', date_format='iso'),
        'dfICS': dfICS.to_json(orient='split', date_format='iso')
    }
    return json.dumps(datasets)

