import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from dateutil import parser
import plotly.express as px
import pandas as pd

import requests
from requests.auth import HTTPBasicAuth

import fhirclient.models.meta as meta
from fhirclient.models.fhirinstant import FHIRInstant
import fhirclient.models.servicerequest as sr
import fhirclient.models.specimen as sp
import fhirclient.models.diagnosticreport as dr


from dotenv import load_dotenv
load_dotenv()
import os

# Initialize the Dash app (no longer need JupyterDash)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


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
        code = coding.code

    return code
def codeDisplay(concept):
    code = ""
    for coding in concept.coding:
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


@app.callback(
    Output('reportsByRequester', 'figure')
)
def reportsByRequester():
    dfReports.sort_values('count', inplace=True, ascending=False)

    fig = px.bar(dfReports, x="requesterCode", y="count", color="codingCode", title="Report Sent by NHS Trust")

    return fig

@app.callback(
    Output('reportsByTestCode', 'figure')
)
def reportsByTestCode():
    figTC = px.bar(dfReports, x="codingCode", y="count", color="requesterCode", title="Report Sent by Test Code")
    return figTC

@app.callback(
    Output('durations', 'figure')
)
def durations():
    dfS = df[['SpecimenReceivedDate', 'testingDuration', 'codingCode']]
    dfS = dfS.dropna(subset=['SpecimenReceivedDate'])
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

@app.callback(
    Output('specimens', 'figure')
)
def specimensByNHS():
    dfS = df[['OrderAuthoredOnDate', 'OrderToSpecimenReceivedDuration', 'requesterCode']]
    dfS = dfS.dropna(subset=['OrderAuthoredOnDate'])
    dfS = dfS.groupby(['OrderAuthoredOnDate', 'OrderToSpecimenReceivedDuration', 'requesterCode']).size().reset_index(name='counts')

    # Now the scatter plot will work as expected
    figD = px.bar(
        dfS,
        x="OrderToSpecimenReceivedDuration",
        y="counts",
        color="requesterCode",
        title="Time from Order from NHS Trust to Specimen Received"
    )

    return figD

@app.callback(
    Output('specimensByCode', 'figure')
)
def specimensByCode():
    dfS = df[['OrderAuthoredOnDate', 'OrderToSpecimenReceivedDuration', 'codingCode']]
    dfS = dfS.dropna(subset=['OrderAuthoredOnDate'])
    dfS = dfS.groupby(['OrderAuthoredOnDate', 'OrderToSpecimenReceivedDuration', 'codingCode']).size().reset_index(name='counts')

    # Now the scatter plot will work as expected
    figD = px.bar(
        dfS,
        x="OrderToSpecimenReceivedDuration",
        y="counts",
        color="codingCode",
        title="Time from Order to Specimen Received by Test Code"
    )

    return figD

@app.callback(
    Output('release', 'figure')
)
def release():
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

@app.callback(
    Output('lines', 'figure')
)
def lines():

    figL = px.bar(dfmelt,x="date", y="Count", color="DateType",  title="Timeline overview for sent reports")
    return figL


fhir_password = os.getenv("FHIR_PASSWORD")
fhir_username = os.getenv("FHIR_USERNAME")
#server = "https://gen-tie-test.nwgenomics.nhs.uk/dataplatform/cdr/fhir/r4/"
server = os.getenv("FHIR_SERVER")

api_url = server + "metadata"
print(api_url)
response = requests.get(api_url)

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
dfSR['OrderAuthoredOnDate'] = dfSR['authoredOn'].apply(issued)

dfServiceRequest = dfSR[['id','requesterDisplay','requesterCode','OrderAuthoredOnDate']]

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
df['OrderAuthoredOnDate'] = pd.to_datetime(df['OrderAuthoredOnDate'], utc=True).dt.tz_localize(None)
df['ReportLastUpdatedDate'] = pd.to_datetime(df['ReportLastUpdatedDate'], utc=True).dt.tz_localize(None)

df['requestedDuration'] = (df['ReportIssuedDate'] - df['OrderAuthoredOnDate']).dt.days

df['releaseDuration'] = (df['ReportLastUpdatedDate'] - df['ReportIssuedDate']).dt.days
df['testingDuration'] = (df['ReportIssuedDate'] - df['SpecimenReceivedDate']).dt.days
df['OrderToSpecimenReceivedDuration'] = (df['SpecimenReceivedDate'] - df['OrderAuthoredOnDate']).dt.days

#df['releaseDuration'] = df['releaseDuration'].fillna(-1)
#df['requestedDuration'] = df['requestedDuration'].fillna(-1)
df['OrderToSpecimenReceivedDuration'] = df['OrderToSpecimenReceivedDuration'].fillna(-1)

dti = pd.date_range("2025-10-01", periods=100, freq="d").to_frame(index=False, name="date")
dti['date'] = dti['date'].dt.date

df['ReportSentDT'] = df['ReportLastUpdatedDate'].dt.date
df['ReportIssuedDT'] = df['ReportIssuedDate'].dt.date
df['OrderAuthoredDT'] = df['OrderAuthoredOnDate'].dt.date
df['SpecimenReceivedDT'] = df['SpecimenReceivedDate'].dt.date

dfReports = df.groupby(['requesterCode', 'codingCode']).size().reset_index(name='count')

dti = pd.date_range("2025-10-01", periods=100, freq="d").to_frame(index=False, name="date")
dti['date'] = dti['date'].dt.date

df['ReportSentDT'] = df['ReportLastUpdatedDate'].dt.date
df['ReportIssuedDT'] = df['ReportIssuedDate'].dt.date
df['OrderAuthoredDT'] = df['OrderAuthoredOnDate'].dt.date
df['SpecimenReceivedDT'] = df['SpecimenReceivedDate'].dt.date

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


fig1 = reportsByRequester()
fig3 = reportsByTestCode()
fig2 = durations()
fig4 = lines()
fig51 = specimensByNHS()
fig52 = specimensByCode()
fig6 = release()

app.layout = html.Div([
    html.H1("NW Genomic HIE Dashboard"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='lines', figure=fig4),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='specimens', figure=fig51),
        ]),
        dbc.Col([
            dcc.Graph(id='specimensByCode', figure=fig52),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='durations', figure=fig2)
        ]),
        dbc.Col([
            dcc.Graph(id='release', figure=fig6),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='reportsByRequester', figure=fig1),
        ]),
        dbc.Col([
            dcc.Graph(id='reportByTestCode', figure=fig3),
        ])

    ])
])



if __name__ == '__main__':
    # Use app.run with jupyter_mode instead of JupyterDash's run_server
    app.run( port=8052)
