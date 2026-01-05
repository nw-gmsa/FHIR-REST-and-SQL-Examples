import dash
from dash import html, dcc, callback, Input, Output, ALL
import plotly.express as px

from dash_app.data.rest import dfReports, df, dfmelt
import dash_bootstrap_components as dbc


# convert to share data between callbacks https://dash.plotly.com/sharing-data-between-callbacks

dash.register_page(__name__,title="Reports", name="Reports REST", path="/")


@callback(
    Output('reportsByRequester', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def reportsByRequester(_value):
    dfReports.sort_values('count', inplace=True, ascending=False)

    fig = px.bar(dfReports, x="requesterCode", y="count", color="codingCode", title="Report Sent by NHS Trust")

    return fig

@callback(
    Output('reportsByTestCode', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def reportsByTestCode(_value):
    figTC = px.bar(dfReports, x="codingCode", y="count", color="requesterCode", title="Report Sent by Test Code")
    return figTC

@callback(
    Output('durations', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def durations(_value):
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

@callback(
    Output('specimens', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def specimensByNHS(_value):
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

@callback(
    Output('specimensByCode', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def specimensByCode(_value):
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

@callback(
    Output('release', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def release(_value):
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
    Output('lines', 'figure'),
    Input({"type": "control", "id": ALL}, "value")
)
def lines(_value):

    figL = px.bar(dfmelt,x="date", y="Count", color="DateType",  title="Timeline overview for sent reports")
    return figL




fig1 = reportsByRequester("")
fig3 = reportsByTestCode("")
fig2 = durations("")
fig4 = lines("")
fig51 = specimensByNHS("")
fig52 = specimensByCode("")
fig6 = release("")

layout = html.Div([
    html.H1("NW Genomic HIE Dashboard"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='lines', figure=fig4),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='specimens',figure=fig51),
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
