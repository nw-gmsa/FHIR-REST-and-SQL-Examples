import io

import dash
from dash import html, dcc, callback, Input, Output, ALL
import plotly.express as px
import dash_bootstrap_components as dbc
import os
import pandas as pd
import json
import requests
from requests.auth import HTTPBasicAuth

import fhirclient.models.meta as meta
import fhirclient.models.servicerequest as sr
import fhirclient.models.specimen as sp
import fhirclient.models.diagnosticreport as dr
from dotenv import load_dotenv
from dateutil import parser
from datetime import datetime




# convert to share data between callbacks https://dash.plotly.com/sharing-data-between-callbacks

dash.register_page(__name__,title="Graphs", name="Graphs (FHIR REST)", path="/")

load_dotenv()

fhir_password = os.getenv("FHIR_PASSWORD")
fhir_username = os.getenv("FHIR_USERNAME")
server = os.getenv("FHIR_SERVER")

dateRangeStart = pd.Timestamp(2025,11,1)

layout = html.Div([
    html.H1("Graphs (REST)"),
    dbc.Row([
        dcc.Store(id='intermediate-value'),
        dcc.Interval(
            id='interval-component',
            interval=2*60*1000, # in milliseconds
            n_intervals=0
        ),
        html.Label(id='updated')
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='lines'),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='releaseLine'),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='specimenTimeLine'),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='orderTimeLine'),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='specimens'),
        ]),
        dbc.Col([
            dcc.Graph(id='specimensByCode'),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='durations')
        ]),
        dbc.Col([
            dcc.Graph(id='release'),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='reportsByRequester'),
        ]),
        dbc.Col([
            dcc.Graph(id='reportsByTestCode'),
        ])

    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='orderByRequester'),
        ]),
        dbc.Col([
            dcc.Graph(id='orderByCICode'),
        ])

    ])
])

def load_and_aggregate_data(n):
    print("load_and_aggregate_data called")

    # Look at replacing with https://dash.plotly.com/live-updates
    df = getInitialData()
    dti = pd.date_range("2025-10-01", periods=100, freq="d").to_frame(index=False, name="date")
    dti['date'] = dti['date'].dt.date
    print("load_and_aggregate_data called")
    dfA = df.groupby(['ReportSentDT']).size().reset_index(name='ReportSent')
    dfB = df.groupby(['ReportIssuedDT']).size().reset_index(name='ReportIssued')
    dfC = df.groupby(['OrderAuthoredDT']).size().reset_index(name='OrderAuthored')
    dfD = df.groupby(['SpecimenReceivedDT']).size().reset_index(name='SpecimenReceived')

    df_merged = pd.merge(dti, dfA, left_on='date', right_on='ReportSentDT', how='left')
    df_merged = pd.merge(df_merged, dfB, left_on='date', right_on='ReportIssuedDT', how='left')
    df_merged = pd.merge(df_merged, dfC, left_on='date', right_on='OrderAuthoredDT', how='left')
    df_merged = pd.merge(df_merged, dfD, left_on='date', right_on='SpecimenReceivedDT', how='left')
    df_merged.drop(columns=['ReportSentDT', 'ReportIssuedDT', 'OrderAuthoredDT','SpecimenReceivedDT'], inplace=True)

    dfmelt = df_merged.melt(id_vars=["date"],
                            var_name="DateType",
                            value_name="Count")


    datasets = {
        'df': df.to_json(orient='split', date_format='iso'),
        'dfmelt': dfmelt.to_json(orient='split', date_format='iso')
    }


    return json.dumps(datasets)

@callback(
    Output('updated', 'children'),
          Output('intermediate-value', 'data'),
          Input('interval-component', 'n_intervals'))
def update_metrics(n):
    print("update_metrics called")
    print(n)
    updated = [html.P('Last updated ' +str(datetime.now()))]
    return updated,load_and_aggregate_data(n)


#@callback(
#    Output('intermediate-value2', 'data'),
#    Input('load-button', 'n_clicks'),
#    prevent_initial_call=True
#)
#def load_button(n):
#    print("load_button called")
#    return None




@callback(
    Output('reportsByRequester', 'figure'),
    Input('intermediate-value', 'data'))
def reportsByRequester(_value):
    print("reportsByRequester called")
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfReports = df.groupby(['requesterCode', 'codingCode']).size().reset_index(name='count')
    dfReports.sort_values('count', inplace=True, ascending=False)

    fig = px.bar(dfReports, x="requesterCode", y="count", color="codingCode", title="Report Sent by NHS Trust")

    return fig

@callback(
    Output('orderByRequester', 'figure'),
    Input('intermediate-value', 'data'))
def orderByRequester(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfReports = df.groupby(['requesterCode', 'CICode']).size().reset_index(name='count')
    dfReports.sort_values('count', inplace=True, ascending=False)

    fig = px.bar(dfReports, x="requesterCode", y="count", color="CICode", title="Order by NHS Trust")

    return fig

@callback(
    Output('reportsByTestCode', 'figure'),
    Input('intermediate-value', 'data'))
def reportsByTestCode(_value):
    print("reportsByTestCode called")
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfReports = df.groupby(['requesterCode', 'codingCode']).size().reset_index(name='count')
    figTC = px.bar(dfReports, x="codingCode", y="count", color="requesterCode", title="Report Sent by Test Code")
    return figTC

@callback(
    Output('orderByCICode', 'figure'),
    Input('intermediate-value', 'data'))
def orderByCICode(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfReports = df.groupby(['requesterCode', 'CICode']).size().reset_index(name='count')
    figTC = px.bar(dfReports, x="CICode", y="count", color="requesterCode", title="Order by CI Code")
    return figTC

@callback(
    Output('durations', 'figure'),
    Input('intermediate-value', 'data')
)
def durations(_value):
    print("durations called")
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['SpecimenReceivedDate', 'testingDuration', 'codingCode']]
    dfS = dfS.dropna(subset=['SpecimenReceivedDate'])
    dfS['SpecimenReceivedDate'] = pd.to_datetime(dfS['SpecimenReceivedDate'], utc=True).dt.tz_localize(None)
    dfS = dfS[(dfS['SpecimenReceivedDate'] > dateRangeStart)]
    dfS = dfS.groupby(['SpecimenReceivedDate', 'testingDuration', 'codingCode']).size().reset_index(name='counts')
    # Now the scatter plot will work as expected
    figD = px.bar(
        dfS,
        x="testingDuration",
        y="counts",
        color="codingCode",
        title="Testing Time from Specimen Collection to Report Release"
    )

    return figD

@callback(
    Output('specimens', 'figure'),
    Input('intermediate-value', 'data')
)
def specimensByNHS(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)

    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['OrderDate', 'OrderToSpecimenReceivedDuration', 'requesterCode']]
    dfS = dfS.dropna(subset=['OrderDate'])
    dfS = dfS.groupby(['OrderDate', 'OrderToSpecimenReceivedDuration', 'requesterCode']).size().reset_index(name='counts')
    dfS['OrderDate'] = pd.to_datetime(dfS['OrderDate'], utc=True).dt.tz_localize(None)
    dfS = dfS[(dfS['OrderDate'] > dateRangeStart)]
    # Now the scatter plot will work as expected
    figD = px.bar(
        dfS,
        x="OrderToSpecimenReceivedDuration",
        y="counts",
        color="requesterCode",
        title="Time from Order from NHS Trust to Specimen Received"
    )

    return figD

@callback(
    Output('specimensByCode', 'figure'),
    Input('intermediate-value', 'data')
)
def specimensByCode(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['OrderDate', 'OrderToSpecimenReceivedDuration', 'codingCode']]
    dfS = dfS.dropna(subset=['OrderDate'])
    dfS = dfS.groupby(['OrderDate', 'OrderToSpecimenReceivedDuration', 'codingCode']).size().reset_index(name='counts')
    dfS['OrderDate'] = pd.to_datetime(dfS['OrderDate'], utc=True).dt.tz_localize(None)
    dfS = dfS[(dfS['OrderDate'] > dateRangeStart)]
    # Now the scatter plot will work as expected
    figD = px.bar(
        dfS,
        x="OrderToSpecimenReceivedDuration",
        y="counts",
        color="codingCode",
        title="Time from Order to Specimen Received by Test Code"
    )

    return figD

@callback(
    Output('release', 'figure'),
    Input('intermediate-value', 'data')
)
def release(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['ReportIssuedDate', 'releaseDuration', 'codingCode']]
    dfS = dfS.dropna(subset=['ReportIssuedDate'])
    dfS = dfS.groupby(['ReportIssuedDate', 'releaseDuration', 'codingCode']).size().reset_index(name='counts')
    # Now the scatter plot will work as expected
    figE = px.bar(
        dfS,
        x="releaseDuration",
        y="counts",
        color="codingCode",
        title="Time from Report Release to Report Sent"
    )
    return figE


@callback(
    Output('releaseLine', 'figure'),
    Input('intermediate-value', 'data')
)
def releaseLine(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['ReportLastUpdatedDate', 'releaseDurationMin']]
    dfS = dfS.dropna(subset=['ReportLastUpdatedDate'])
    dfS['ReportLastUpdatedDate'] = pd.to_datetime(dfS['ReportLastUpdatedDate'], utc=True).dt.tz_localize(None)
    dfS = dfS.sort_values('ReportLastUpdatedDate')
    dfS = dfS[(dfS['ReportLastUpdatedDate'] > dateRangeStart)]
    dfS = dfS.sort_values('releaseDurationMin')
    # Now the scatter plot will work as expected
    figE = px.scatter(
        dfS,
        x="ReportLastUpdatedDate",
        y="releaseDurationMin",
        title="Time from Report Authorised to Report Sent (minutes)"
    )
    return figE

@callback(
    Output('orderTimeLine', 'figure'),
    Input('intermediate-value', 'data')
)
def orderTimeLine(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['OrderDate', 'OrderToSpecimenReceivedDuration']]
    dfS = dfS.dropna(subset=['OrderDate'])
    dfS['OrderDate'] = pd.to_datetime(dfS['OrderDate'], utc=True).dt.tz_localize(None)
    dfS = dfS[(dfS['OrderDate'] > dateRangeStart)]
    dfS = dfS.sort_values('OrderToSpecimenReceivedDuration')
    # Now the scatter plot will work as expected
    figE = px.scatter(
        dfS,
        x="OrderDate",
        y="OrderToSpecimenReceivedDuration",
        title="Time from Order Created to Specimen Received (days)"
    )
    return figE

@callback(
    Output('specimenTimeLine', 'figure'),
    Input('intermediate-value', 'data')
)
def specimenTimeLine(_value):
    if _value is None:
        return dash.no_update
    print("specimenTimeLine called")
    datasets = json.loads(_value)
    df = pd.read_json(io.StringIO(datasets['df']),orient='split')
    dfS = df[['SpecimenReceivedDate', 'testingDurationMinutes']]
    dfS = dfS.dropna(subset=['SpecimenReceivedDate'])
    dfS['SpecimenReceivedDate'] = pd.to_datetime(dfS['SpecimenReceivedDate'], utc=True).dt.tz_localize(None)
    dfS = dfS.sort_values('SpecimenReceivedDate')
    dfS = dfS[(dfS['SpecimenReceivedDate'] > dateRangeStart)]
    # Now the scatter plot will work as expected
    figE = px.scatter(
        dfS,
        x="SpecimenReceivedDate",
        y="testingDurationMinutes",
        title="Time from Specimen received to Report Authorised (minutes)"
    )
    return figE

@callback(
    Output('lines', 'figure'),
    Input('intermediate-value', 'data')
)
def lines(_value):
    if _value is None:
        return dash.no_update
    datasets = json.loads(_value)
    dfmelt = pd.read_json(io.StringIO(datasets['dfmelt']),orient='split')
    figL = px.bar(dfmelt,x="date", y="Count", color="DateType",  title="Timeline overview for sent reports")
    return figL


def performer(my_list):
    performer = ""
    if my_list != None:
        for item in my_list:
            performer = item.display
    return performer

def performerCode(my_list):
    performer = None
    if my_list != None:
        for item in my_list:
            performer = item.identifier.value
    return performer

def codeCode(concept):
    code = ""
    for coding in concept.coding:
        if coding.system == "https://fhir.nwgenomics.nhs.uk/CodeSystem/IGEAP":
            code = coding.code

    return code
def codeDisplay(concept):
    code = ""
    for coding in concept.coding:
        if coding.system == "https://fhir.nwgenomics.nhs.uk/CodeSystem/IGEAP":
            code = coding.display

    return code


def issued(issued):
    if issued == None:
        return None
    return parser.parse(issued.isostring)

def serviceRequest(my_list):
    sr = None
    if my_list != None:
        for item in my_list:
            if item.reference != None:
                sr = item.reference.replace('ServiceRequest/', '')
    return sr
def specimen(my_list):
    sr = None
    if my_list != None:
        for item in my_list:
            if item.reference != None:
                sr = item.reference.replace('Specimen/', '')
    return sr
def lastUpdated(meta : meta.Meta):
    if meta == None:
        return None
    return parser.parse(meta.lastUpdated.isostring)

def requester(item):
    performer = None
    if item != None:
        performer = item.display
    return performer

def requesterCode(item):
    performer = None
    if item != None:
        performer = item.identifier.value
    return performer

def CICode(my_list):
    code = None
    if my_list != None:
        for concept in my_list:
            for coding in concept.coding:
                code = coding.code
    return code
def CIDisplay(my_list):
    code = None
    if my_list != None:
        for concept in my_list:
            for coding in concept.coding:
                code = coding.display
    return code

def getInitialData():
    print("getInitialData called")
    serviceRequests = []
    diagnosticReports = []
    specimens = []

    api_url = server + "DiagnosticReport?_include=DiagnosticReport:based-on&_include=DiagnosticReport:specimen&_lastUpdated=gt2025-12-01"

    while True:
        response = requests.get(api_url, auth=HTTPBasicAuth(fhir_username, fhir_password))
        responseInclude = response.json()

        #print(responseInclude)
        print(responseInclude['total'])
        entry = responseInclude['entry']
        print(len(entry))
        if len(entry) == 0:
            break
        for entry in responseInclude['entry']:

            if entry['resource']['resourceType'] == 'DiagnosticReport':
                report = dr.DiagnosticReport(entry['resource'])
                diagnosticReports.append(report)
            if entry['resource']['resourceType'] == 'ServiceRequest':
                request = sr.ServiceRequest(entry['resource'])
                serviceRequests.append(request)
            if entry['resource']['resourceType'] == 'Specimen':
                specimen_resource = sp.Specimen(entry['resource'])
                specimens.append(specimen_resource)

        print("ServiceRequest = " + str(len(serviceRequests)))
        print("DiagnosticReport = " + str(len(diagnosticReports)))
        print("Specimen = " + str(len(specimens)))

        found = False
        for link in responseInclude['link']:
            if link['relation'] == 'next':
                api_url = link['url']
                found = True
                print(api_url)
        if found == False:
            break

    print(len(diagnosticReports))
    dfDR = pd.DataFrame([vars(s) for s in diagnosticReports])

    dfDR['performerDisplay'] = dfDR['performer'].apply(performer)
    dfDR['performerCode'] = dfDR['performer'].apply(performerCode)
    dfDR['codingCode'] = dfDR['code'].apply(codeCode)
    dfDR['codingDisplay'] = dfDR['code'].apply(codeDisplay)
    dfDR['ReportLastUpdatedDate'] = dfDR['meta'].apply(lastUpdated)
    dfDR['ReportIssuedDate'] = dfDR['issued'].apply(issued)
    dfDR['ReportEffectiveDate'] = dfDR['effectiveDateTime'].apply(issued)
    dfDR['serviceRequestId'] = dfDR['basedOn'].apply(serviceRequest)
    dfDR['specimenId'] = dfDR['specimen'].apply(specimen)

    dfDiagnosticReport = dfDR[['id','performerDisplay','performerCode','codingCode', 'codingDisplay', 'ReportLastUpdatedDate','ReportIssuedDate', 'ReportEffectiveDate', 'serviceRequestId','specimenId']]

    print(len(specimens))
    dfSP = pd.DataFrame([vars(s) for s in specimens])
    dfSP['SpecimenReceivedDate'] = dfSP['receivedTime'].apply(issued)


    dfSpecimen = dfSP[['id','SpecimenReceivedDate']]

    dfSR = pd.DataFrame([vars(s) for s in serviceRequests])
    dfSR['requesterDisplay'] = dfSR['requester'].apply(requester)
    dfSR['requesterCode'] = dfSR['requester'].apply(requesterCode)
    dfSR['OrderDate'] = dfSR['authoredOn'].apply(issued)
    dfSR['CICode'] = dfSR['reasonCode'].apply(CICode)
    dfSR['CIDisplay'] = dfSR['reasonCode'].apply(CIDisplay)

    dfServiceRequest = dfSR[['id','requesterDisplay','requesterCode','OrderDate','CICode','CIDisplay']]

    df = pd.merge(
        dfDiagnosticReport,
        dfServiceRequest,
        left_on='serviceRequestId',
        right_on='id',
        how="left",
        indicator=True,
        suffixes=('_dr', '_sr')
    )
    df = df.drop(columns=['_merge'])
    df = pd.merge(
        df,
        dfSpecimen,
        left_on='specimenId',
        right_on='id',
        how="left",
        indicator=True,
        suffixes=('_dr', '_sp')
    )


    df['ReportIssuedDate'] = pd.to_datetime(df['ReportIssuedDate'], utc=True).dt.tz_localize(None)
    df['OrderDate'] = pd.to_datetime(df['OrderDate'], utc=True).dt.tz_localize(None)
    df['ReportLastUpdatedDate'] = pd.to_datetime(df['ReportLastUpdatedDate'], utc=True).dt.tz_localize(None)
    df['SpecimenReceivedDate'] = pd.to_datetime(df['SpecimenReceivedDate'], utc=True).dt.tz_localize(None)

    df['requestedDuration'] = (df['ReportIssuedDate'] - df['OrderDate']).dt.days

    df['releaseDuration'] = (df['ReportLastUpdatedDate'] - df['ReportIssuedDate']).dt.days
    df['releaseDurationMin'] = (df['ReportLastUpdatedDate'] - df['ReportIssuedDate']).dt.total_seconds() / 60
    df['testingDuration'] = (df['ReportIssuedDate'] - df['SpecimenReceivedDate']).dt.days
    df['testingDurationMinutes'] = (df['ReportIssuedDate'] - df['SpecimenReceivedDate']).dt.total_seconds() / 60
    df['OrderToSpecimenReceivedDuration'] = (df['SpecimenReceivedDate'] - df['OrderDate']).dt.days

    #df['releaseDuration'] = df['releaseDuration'].fillna(-1)
    #df['requestedDuration'] = df['requestedDuration'].fillna(-1)
    df['OrderToSpecimenReceivedDuration'] = df['OrderToSpecimenReceivedDuration'].fillna(-1)

    dti = pd.date_range("2025-10-01", periods=100, freq="d").to_frame(index=False, name="date")
    dti['date'] = dti['date'].dt.date

    df['ReportSentDT'] = df['ReportLastUpdatedDate'].dt.date
    df['ReportIssuedDT'] = df['ReportIssuedDate'].dt.date
    df['OrderAuthoredDT'] = df['OrderDate'].dt.date
    df['SpecimenReceivedDT'] = df['SpecimenReceivedDate'].dt.date

    dfReports = df.groupby(['requesterCode', 'codingCode']).size().reset_index(name='count')



    df['ReportSentDT'] = df['ReportLastUpdatedDate'].dt.date
    df['ReportIssuedDT'] = df['ReportIssuedDate'].dt.date
    df['OrderAuthoredDT'] = df['OrderDate'].dt.date
    df['SpecimenReceivedDT'] = df['SpecimenReceivedDate'].dt.date
    return df


