#!/usr/bin/python3
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas
from dash.dependencies import Input, Output


# data URL
consegne = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/consegne-vaccini-latest.csv'
somministrazioni = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv'
decessi_contagi = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
decessi_contagi_regioni = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'
fascia_anagrafica = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-statistici-riferimento/popolazione-istat-regione-range.csv'
population = 0

last_update = ''  # last update
max_prima_f = ''  # max first dose in 1day
tot_janssen = ''  # tot only 1 dose
month_last_day_vaccine = ''  # 70% population vaccine date
pandas.options.mode.chained_assignment = None  # default='warn'

# read csv for url and get date
dc = pandas.read_csv(consegne)
ds = pandas.read_csv(somministrazioni)
ddc = pandas.read_csv(decessi_contagi)
ddcr = pandas.read_csv(decessi_contagi_regioni)
dfe = pandas.read_csv(fascia_anagrafica)
regions = ds['nome_area'].drop_duplicates().tolist()  # all regions

plotly_js_minified = ['https://cdn.plot.ly/plotly-basic-latest.min.js']
app = dash.Dash(__name__, external_scripts=plotly_js_minified,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=0.8, maximum-scale=1.2, minimum-scale=0.5'}],
                requests_pathname_prefix='/vaccine/',
                routes_pathname_prefix='/vaccine/')
app.title = 'Dashboard Vaccini'
server = app.server

# chart config
chart_config = {'displaylogo': False, 'displayModeBar': False, 'responsive': True}

# slider buttons (1m, 3m, 6m, all)
slider_button = list([
    dict(count=1,
         label="1m",
         step="month",
         stepmode="backward"),
    dict(count=3,
         label="3m",
         step="month",
         stepmode="backward"),
    dict(count=6,
         label="6m",
         step="month",
         stepmode="backward"),
    dict(step="all")
])

# refresh data
def refresh_data():
    global today, last_update, max_prima_f
    global dc, ds, dfa, ddc, dfe, ds_dosi
    global tot_prima_dose, tot_seconda_dose, tot_prima, tot_seconda
    # read csv for url and get date
    dc = pandas.read_csv(consegne)
    ds = pandas.read_csv(somministrazioni)
    ddc = pandas.read_csv(decessi_contagi)
    dfe = pandas.read_csv(fascia_anagrafica)
    today = date.today()

    # doses delivered
    dc = dc.groupby('data_consegna').agg({'numero_dosi': 'sum'}).reset_index()
    # doses administered
    ds_dosi = ds.groupby('data_somministrazione').agg(
        {'prima_dose': 'sum', 'seconda_dose': 'sum', 'categoria_operatori_sanitari_sociosanitari': 'sum',
         'categoria_personale_non_sanitario': 'sum', 'categoria_ospiti_rsa': 'sum', 'categoria_over80': 'sum',
         'categoria_forze_armate': 'sum', 'categoria_personale_scolastico': 'sum',
         'categoria_altro': 'sum'}).reset_index()

    ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
    if len(ds_prime_dosi) == 0:
        last_update = date.today()
    else:
        last_update = date.today() - timedelta(days=1)

    # max first
    max_prima = int(max(ds_dosi['prima_dose']))
    max_prima_f = '{:,}'.format(max_prima).replace(',', '.')  # format max first dose

    # first dose from the start
    tot_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['prima_dose']].sum()
    tot_prima_dose = '{:,}'.format(int(tot_prima)).replace(',', '.')
    # second dose from the start
    tot_seconda = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['seconda_dose']].sum()
    tot_seconda_dose = '{:,}'.format(int(tot_seconda)).replace(',', '.')
    # age
    dfa = ds.groupby('fascia_anagrafica').agg({'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    dfe = dfe.groupby('range_eta').agg({'totale_generale': 'sum'}).reset_index()
    dfe = dfe[1:]  # remove 0-15


# dropdown
def get_dropdown_data():
    selections = []
    selections.append(dict(label='Dato Nazionale', value='Dato Nazionale'))
    for reg in regions:
        selections.append(dict(label=reg, value=reg))
    return selections


# total vaccine status
def vaccine_update():
    refresh_data()
    global tot_janssen
    # percentage
    janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg({'prima_dose': 'sum'}).reset_index()
    tot_janssen = janssen.loc[janssen['data_somministrazione'].between('2021-04-05', str(today)), ['prima_dose']].sum()
    prima = int(tot_prima) - int(tot_janssen)
    # percentage
    primadose = round((int(tot_prima)/60360000)*100, 2)
    secondadose = round((int(tot_seconda)/60360000)*100, 2)
    tjanssen = round((int(tot_janssen) / 60360000) * 100, 2)
    # formating
    tot_prima_dose = '{:,}'.format(int(prima)).replace(',', '.')
    tot_janssen = '{:,}'.format(int(tot_janssen)).replace(',', '.')
    return html.Div([
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Prima dose', style={'font-size': '14px'}),
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1(tot_prima_dose, style={'color': '#F5C05F', 'font-size': '45px'})
                    ),
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        '' + str(primadose) + '% della popolazione',
                        style={'color': '#F5C05F', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3'),
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Persone Vaccinate', style={'font-size': '14px'})
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1(tot_seconda_dose, style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        ''+str(secondadose)+'% della popolazione', style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3'),
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Vaccino monodose', style={'font-size': '14px'}),
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1(tot_janssen, style={'color': '#E83A8E', 'font-size': '45px'})
                    ),
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        '' + str(tjanssen) + '% della popolazione', style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3')
    ], className='container-1')


def vaccine_update_bar():
    refresh_data()
    return html.Div([
        html.Div([
            dcc.Graph(
                figure={
                    'data': [go.Bar(x=[60360000, 50773718, int(tot_prima), int(tot_seconda)],
                                    y=['Popolazione', 'Platea', 'Prima dose', 'Vaccinati'],
                                    orientation='h',
                                    marker_color=['#6181E8', '#5EAEFF', '#F5C05F', '#E83A8E'])
                             ],
                    'layout': {
                        'height': 250,  # px
                        'xaxis': dict(
                            rangeslider=dict(visible=False),
                            type=''
                        )
                    },
                },
                config=chart_config
            )
        ], className='bar')
    ], className='container-1')


# dropdown select
def dropdown_vaccine_daily():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_vaccine_daily',
                                     options=get_dropdown_data(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Dato Nazionale'
                                     ), style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5,
                        className='mt-2')
                ])
            ])
        ])
    ])


# vaccine horozzonatal bar
@app.callback(
    Output('vaccine_daily', 'children'),
    [Input('dropdown_vaccine_daily', 'value')])
def vaccine_daily(regione):
    # total data
    if regione == 'Dato Nazionale':
        refresh_data()
        tot_consegne = dc.loc[dc['data_consegna'].between('2020-12-27', str(today)), ['numero_dosi']].sum()
        tot_vaccini = int(tot_prima) + int(tot_seconda)
        # today data
        dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(today), 'numero_dosi']
        ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
        ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'seconda_dose']

        # check today data
        if len(dc_dosi_consegnate) == 0 and len(ds_prime_dosi) == 0 and len(ds_seconde_dosi) == 0:
            dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(date.today() - timedelta(days=1)), 'numero_dosi']
            ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'prima_dose']
            ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'seconda_dose']
    else:
        dc1 = pandas.read_csv(consegne)
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        ds_dosi1 = reg_ds1.copy().groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        tot_prima1 = ds_dosi1.loc[ds_dosi1['data_somministrazione'].between('2020-12-27', str(today)), ['prima_dose']].sum()
        tot_seconda1 = ds_dosi1.loc[ds_dosi1['data_somministrazione'].between('2020-12-27', str(today)), ['seconda_dose']].sum()
        reg_dc1 = dc1.loc[dc1['nome_area'] == regione]
        dc_dosi1 = reg_dc1.copy().groupby('data_consegna').agg({'numero_dosi': 'sum'}).reset_index()

        # data
        tot_consegne = dc_dosi1.loc[dc_dosi1['data_consegna'].between('2020-12-27', str(today)), ['numero_dosi']].sum()
        tot_vaccini = int(tot_prima1) + int(tot_seconda1)
        # today data
        dc_dosi_consegnate = dc_dosi1.loc[dc_dosi1['data_consegna'] == str(today), 'numero_dosi']
        ds_prime_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(today), 'prima_dose']
        ds_seconde_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(today), 'seconda_dose']

        # check today data
        if len(dc_dosi_consegnate) == 0 and len(ds_prime_dosi) == 0 and len(ds_seconde_dosi) == 0:
            dc_dosi_consegnate = dc1.loc[dc1['data_consegna'] == str(date.today() - timedelta(days=1)), 'numero_dosi']
            ds_prime_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'prima_dose']
            ds_seconde_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'seconda_dose']

    ds_dosi_totali = 0
    tot_consegne = '{:,}'.format(int(tot_consegne)).replace(',', '.')
    tot_vaccini = '{:,}'.format(int(tot_vaccini)).replace(',', '.')

    # formatting data
    if len(dc_dosi_consegnate) == 0:
        dc_dosi_consegnate = 0
    else:
        dc_dosi_consegnate = '{:,}'.format(int(dc_dosi_consegnate)).replace(',', '.')
    if len(ds_prime_dosi) == 0:
        ds_prime_dosi = 0
        ds_dosi_totali = int(ds_prime_dosi)
    else:
        ds_dosi_totali = int(ds_prime_dosi)
        ds_prime_dosi = '{:,}'.format(int(ds_prime_dosi)).replace(',', '.')
    if len(ds_seconde_dosi) == 0:
        ds_seconde_dosi = 0
        ds_dosi_totali = ds_dosi_totali + int(ds_seconde_dosi)
    else:
        ds_dosi_totali = ds_dosi_totali + int(ds_seconde_dosi)
        ds_seconde_dosi = '{:,}'.format(int(ds_seconde_dosi)).replace(',', '.')

    if ds_dosi_totali != 0:
        ds_dosi_totali = '{:,}'.format(int(ds_dosi_totali)).replace(',', '.')

    return html.Div([
        # vaccine
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Vaccini Consegnati', style={'font-size': '14px'}),
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1('+ '+str(dc_dosi_consegnate)+'', style={'color': '#29CF8A', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B(
                        'Totali: '+str(tot_consegne), style={'color': '#29CF8A', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # doses
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Dosi Somministrate', style={'font-size': '14px'}),
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_dosi_totali) + '', style={'color': '#376FDB', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_vaccini), style={'color': '#376FDB', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # first doses
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Prime Dosi', style={'font-size': '14px'}),
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_prime_dosi) + '', style={'color': '#F5C05F', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_prima_dose), style={'color': '#F5C05F', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # vaccine
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Persone Vaccinate (Due Dosi)', style={'font-size': '14px'})
                ]),
                # Body
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_seconde_dosi) + '',
                                style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_seconda_dose), style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4')
    ], className='container-1')


# vaccine horozzonatal bar
@app.callback(
    Output('vaccine_graph', 'children'),
    [Input('dropdown_vaccine_daily', 'value')])
# vaccine and doses graph
def vaccine_graph(regione):
    if regione == 'Dato Nazionale':
        refresh_data()
        # vaccine
        ds_pfizer = ds.loc[ds['fornitore'] == 'Pfizer/BioNTech'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_moderna = ds.loc[ds['fornitore'] == 'Moderna'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_astra = ds.loc[ds['fornitore'] == 'Vaxzevria (AstraZeneca)'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    else:
        # vaccine
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        ds_dosi1 = reg_ds1.copy().groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'fornitore': 'last'}).reset_index()
        ds_pfizer = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Pfizer/BioNTech'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_moderna = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Moderna'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_astra = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Vaxzevria (AstraZeneca)'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        ds_janssen = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_pfizer['data_somministrazione'],
                                 'y': ds_pfizer['prima_dose'] + ds_pfizer['seconda_dose'],
                                 'type': 'bar',
                                 'name': 'Pfizer',
                                 'marker': dict(color='#95A9DE')},
                                {'x': ds_moderna['data_somministrazione'],
                                 'y': ds_moderna['prima_dose'] + ds_moderna['seconda_dose'],
                                 'type': 'bar',
                                 'name': 'Moderna',
                                 'marker': dict(color='#395499')},
                                {'x': ds_astra['data_somministrazione'],
                                 'y': ds_astra['prima_dose'] + ds_astra['seconda_dose'], 'type': 'bar',
                                 'name': 'AstraZeneca',
                                 'marker': dict(color='#537BE0')},
                                {'x': ds_janssen['data_somministrazione'],
                                 'y': ds_janssen['prima_dose'] + ds_janssen['seconda_dose'],
                                 'type': 'bar',
                                 'name': 'Janssen',
                                 'marker': dict(color='#243561')},
                            ],
                            'layout': {
                                'barmode': 'stack',
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5,
                                    y=-0.2
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    ], className='container-2')


# vaccine horozzonatal bar
@app.callback(
    Output('dosi_graph', 'children'),
    [Input('dropdown_vaccine_daily', 'value')])
# vaccine and doses graph
def dosi_graph(regione):
    if regione == 'Dato Nazionale':
        refresh_data()
        prima_seconda = ds.groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    else:
        # vaccine
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        prima_seconda = reg_ds1.copy().groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
    return html.Div([
            dbc.Container([
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            figure={
                                'data': [
                                    {'x': prima_seconda['data_somministrazione'], 'y': prima_seconda['prima_dose'],
                                     'type': 'bar',
                                     'name': 'Prima Dose',
                                     'marker': dict(color='#F5C05F')},
                                    {'x': prima_seconda['data_somministrazione'], 'y': prima_seconda['seconda_dose'],
                                     'type': 'bar',
                                     'name': 'Seconda Dose',
                                     'marker': dict(color='#78F5B3')},
                                ],
                                'layout': {
                                    'barmode': 'stack',
                                    'xaxis': dict(
                                        rangeselector=dict(buttons=slider_button),
                                        rangeslider=dict(visible=False),
                                        type='date'
                                    ),
                                    'legend': dict(
                                        orientation="h",
                                        xanchor="center",
                                        x=0.5,
                                        y=-0.2
                                    )
                                }
                            },
                            config=chart_config
                        )
                    )
                )
            ])
        ], className='container-2')


# category
def category():
    refresh_data()
    # total data
    # sanitari
    tot_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_operatori_sanitari_sociosanitari']].sum()
    tot_sanitario = '{:,}'.format(int(tot_sanitario)).replace(',', '.')
    # non sanitari
    tot_non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_personale_non_sanitario']].sum()
    tot_non_sanitario = '{:,}'.format(int(tot_non_sanitario)).replace(',', '.')
    # rsa
    tot_rsa = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_ospiti_rsa']].sum()
    tot_rsa = '{:,}'.format(int(tot_rsa)).replace(',', '.')
    # over 80
    tot_over80 = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_over80']].sum()
    tot_over80 = '{:,}'.format(int(tot_over80)).replace(',', '.')
    # forze armate
    tot_forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_forze_armate']].sum()
    tot_forze_armate = '{:,}'.format(int(tot_forze_armate)).replace(',', '.')
    # scuola
    tot_scuola = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_personale_scolastico']].sum()
    tot_scuola = '{:,}'.format(int(tot_scuola)).replace(',', '.')
    # altro
    tot_altro = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['categoria_altro']].sum()
    tot_altro = '{:,}'.format(int(tot_altro)).replace(',', '.')

    # today data
    sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_operatori_sanitari_sociosanitari']
    non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_personale_non_sanitario']
    rsa = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_ospiti_rsa']
    over80 = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_over80']
    forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_forze_armate']
    scuola = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_personale_scolastico']
    altro = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'categoria_altro']

    # check today data
    if len(sanitario) == 0 and len(non_sanitario) == 0 and len(rsa) == 0 and len(over80) == 0 and len(forze_armate) == 0 and len(scuola) == 0 and len(altro) == 0:
        sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_operatori_sanitari_sociosanitari']
        non_sanitario = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_personale_non_sanitario']
        rsa = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_ospiti_rsa']
        over80 = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_over80']
        forze_armate = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_forze_armate']
        scuola = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_personale_scolastico']
        altro = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'categoria_altro']

    # formatting data
    if len(sanitario) == 0:
        sanitario = 0
    else:
        sanitario = '{:,}'.format(int(sanitario)).replace(',', '.')
    if len(non_sanitario) == 0:
        non_sanitario = 0
    else:
        non_sanitario = '{:,}'.format(int(non_sanitario)).replace(',', '.')
    if len(rsa) == 0:
        rsa = 0
    else:
        rsa = '{:,}'.format(int(rsa)).replace(',', '.')
    if len(over80) == 0:
        over80 = 0
    else:
        over80 = '{:,}'.format(int(over80)).replace(',', '.')
    if len(forze_armate) == 0:
        forze_armate = 0
    else:
        forze_armate = '{:,}'.format(int(forze_armate)).replace(',', '.')
    if len(scuola) == 0:
        scuola = 0
    else:
        scuola = '{:,}'.format(int(scuola)).replace(',', '.')
    if len(altro) == 0:
        altro = 0
    else:
        altro = '{:,}'.format(int(altro)).replace(',', '.')

    return html.Div([
        # Sanitari
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Operatori Sanitari', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(sanitario) + '', style={'color': '#FF4272', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_sanitario), style={'color': '#FF4272', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # Non Sanitari
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Operatori non Sanitari', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(non_sanitario) + '', style={'color': '#F2665C', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_non_sanitario), style={'color': '#F2665C', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # RSA
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('RSA', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(rsa) + '', style={'color': '#DBAF48', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_rsa), style={'color': '#DBAF48', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # Over 80
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Over 80', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(over80) + '', style={'color': '#50DE8B', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_over80), style={'color': '#50DE8B', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-4'),

        # Forze Armate
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Forze Armate', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(forze_armate) + '', style={'color': '#4B8CDE', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_forze_armate), style={'color': '#4B8CDE', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3'),

        # Personale Scolastico
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Personale Scolastico', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(scuola) + '', style={'color': '#68D8DE', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_scuola), style={'color': '#68D8DE', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3'),

        # Altro
        html.Div([
            html.Table([
                # Header
                html.Tr([
                    html.Td('Altro', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(altro) + '', style={'color': '#844BDB', 'font-size': '45px'})
                    )
                ]),
                # Total
                html.Tr([
                    html.Td(html.B(
                        'Totali: ' + str(tot_altro), style={'color': '#844BDB', 'font-size': '14px'}
                    ))
                ])
            ], className='table')
        ], className='container-3')
    ], className='container-1')



# graph tot category
def category_global():
    refresh_data()
    return html.Div(  # main div
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_operatori_sanitari_sociosanitari'],
                                 'type': 'bar',
                                 'name': 'Operatori Sanitari',
                                 'marker': dict(color='#FF4272')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_personale_non_sanitario'],
                                 'type': 'bar',
                                 'name': 'Operatori non Sanitari',
                                 'marker': dict(color='#F2665C')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_ospiti_rsa'],
                                 'type': 'bar',
                                 'name': 'RSA',
                                 'marker': dict(color='#DBAF48')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_over80'],
                                 'type': 'bar',
                                 'name': 'Over 80',
                                 'marker': dict(color='#50DE8B')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_forze_armate'],
                                 'type': 'bar',
                                 'name': 'Forze Armate',
                                 'marker': dict(color='#4B8CDE')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_personale_scolastico'],
                                 'type': 'bar',
                                 'name': 'Personale Scolastico',
                                 'marker': dict(color='#68D8DE')},
                                {'x': ds_dosi['data_somministrazione'], 'y': ds_dosi['categoria_altro'],
                                 'type': 'bar',
                                 'name': 'Altro',
                                 'marker': dict(color='#844BDB')},
                            ],
                            'layout': {
                                'barmode': 'stack',  # stack data
                                # 'showlegend': False,
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5,
                                    y=-0.2
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    )


# dropdown select
def dropdown_vaccine_age_bar():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_vaccine_age_bar',
                                     options=get_dropdown_data(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Dato Nazionale'
                                     ), style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5,
                        className='mt-2')
                ])
            ])
        ])
    ])


# vaccine # age
@app.callback(
    Output('vaccine_age_bar', 'children'),
    [Input('dropdown_vaccine_age_bar', 'value')])
def vaccine_age_bar(regione):
    if regione == 'Dato Nazionale':
        refresh_data()
        figure_age = {
            'data': [go.Bar(x=[int(dfa['prima_dose'][0])-int(dfa['seconda_dose'][0]), int(dfa['prima_dose'][1])-int(dfa['seconda_dose'][1]),
                               int(dfa['prima_dose'][2])-int(dfa['seconda_dose'][2]), int(dfa['prima_dose'][3])-int(dfa['seconda_dose'][3]),
                               int(dfa['prima_dose'][4])-int(dfa['seconda_dose'][4]), int(dfa['prima_dose'][5])-int(dfa['seconda_dose'][5]),
                               int(dfa['prima_dose'][6])-int(dfa['seconda_dose'][6]), int(dfa['prima_dose'][7])-int(dfa['seconda_dose'][7]),
                               int(dfa['prima_dose'][8])-int(dfa['seconda_dose'][8])],
                            y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                            orientation='h',
                            marker_color='#F5C05F',
                            name='Prima Dose'
                            ),
                     go.Bar(x=[dfa['seconda_dose'][0], dfa['seconda_dose'][1], dfa['seconda_dose'][2],
                               dfa['seconda_dose'][3], dfa['seconda_dose'][4], dfa['seconda_dose'][5],
                               dfa['seconda_dose'][6], dfa['seconda_dose'][7], dfa['seconda_dose'][8]],
                            y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                            orientation='h',
                            marker_color='#E83A8E',
                            name='Seconda Dose'
                            ),
                     go.Bar(x=[int(dfe.loc[dfe.index[0], 'totale_generale']) - int(dfa['prima_dose'][0]),
                               int(dfe.loc[dfe.index[1], 'totale_generale']) - int(dfa['prima_dose'][1]),
                               int(dfe.loc[dfe.index[2], 'totale_generale']) - int(dfa['prima_dose'][2]),
                               int(dfe.loc[dfe.index[3], 'totale_generale']) - int(dfa['prima_dose'][3]),
                               int(dfe.loc[dfe.index[4], 'totale_generale']) - int(dfa['prima_dose'][4]),
                               int(dfe.loc[dfe.index[5], 'totale_generale']) - int(dfa['prima_dose'][5]),
                               int(dfe.loc[dfe.index[6], 'totale_generale']) - int(dfa['prima_dose'][6]),
                               int(dfe.loc[dfe.index[7], 'totale_generale']) - int(dfa['prima_dose'][7]),
                               int(dfe.loc[dfe.index[8], 'totale_generale']) - int(dfa['prima_dose'][8])],
                            y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                            orientation='h',
                            marker_color='#6181E8',
                            name='Non vaccinati'
                            )
                     ],
            'layout': {
                'barmode': 'stack',  # stack data
                'height': 340,  # px
                'xaxis': dict(
                    rangeslider=dict(visible=False),
                    type=''
                ),
                'legend': dict(
                    orientation="h",
                    xanchor="center",
                    x=0.5,
                    y=-0.2
                )
            },
        }
    else:
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds['nome_area'] == regione]
        dfa1 = reg_ds1.copy().groupby('fascia_anagrafica').agg({'prima_dose': 'sum', 'seconda_dose': 'sum'}).reset_index()
        figure_age = {
            'data': [go.Bar(x=[dfa1['prima_dose'][0], dfa1['prima_dose'][1], dfa1['prima_dose'][2], dfa1['prima_dose'][3],
                               dfa1['prima_dose'][4], dfa1['prima_dose'][5], dfa1['prima_dose'][6], dfa1['prima_dose'][7],
                               dfa1['prima_dose'][8]],
                            y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                            orientation='h',
                            marker_color='#F5C05F',
                            name='Prima Dose'
                            ),
                     go.Bar(x=[dfa1['seconda_dose'][0], dfa1['seconda_dose'][1], dfa1['seconda_dose'][2],
                               dfa1['seconda_dose'][3], dfa1['seconda_dose'][4], dfa1['seconda_dose'][5],
                               dfa1['seconda_dose'][6], dfa1['seconda_dose'][7], dfa1['seconda_dose'][8]],
                            y=['16-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90+'],
                            orientation='h',
                            marker_color='#E83A8E',
                            name='Seconda Dose'
                            ),
                     ],
            'layout': {
                'barmode': 'stack',  # stack data
                'height': 340,  # px
                'xaxis': dict(
                    rangeslider=dict(visible=False),
                    type=''
                ),
                'legend': dict(
                    orientation="h",
                    xanchor="center",
                    x=0.5,
                    y=-0.2
                )
            },
        }
    return html.Div([
        dcc.Graph(
            figure=figure_age,
            config=chart_config
        )
    ], className='bar')

# forecast
def previsione():
    refresh_data()
    global month_last_day_vaccine
    date_format = "%Y-%m-%d"  # date format
    ora = datetime.strptime(str(today), date_format)

    # best day
    l = len(ds_dosi['data_somministrazione'])  # total vaccine day
    best_day = (60360000 - int(tot_prima)) / int(max(ds_dosi['prima_dose']))
    best_last_day = str(ora + timedelta(days=best_day))[:10]
    # 80%
    best_day_80 = (48288000 - int(tot_prima)) / int(max(ds_dosi['prima_dose']))
    best_last_day_80 = str(ora + timedelta(days=best_day_80))[:10]

    # month
    month_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between(str(ora-relativedelta(months=1))[:10], str(ora)[:10]), ['prima_dose']].sum()
    month_day_passati = (ora - (ora-relativedelta(months=1))).days
    month_day = (60360000 / int(month_prima)) * month_day_passati
    month_last_day = str(ora + timedelta(days=month_day))[:10]
    # 80%
    month_day_80 = (48288000 / int(month_prima)) * month_day_passati
    month_last_day_80 = str(ora + timedelta(days=month_day_80))[:10]
    # 70%
    month_day_70 = (42252000 / int(month_prima)) * month_day_passati
    month_last_day_70 = str(ora + timedelta(days=month_day_70))[:10]
    # 60%
    month_day_60 = (36216000 / int(month_prima)) * month_day_passati
    month_last_day_60 = str(ora + timedelta(days=month_day_60))[:10]

    month_last_day_vaccine = month_last_day_70  # last day 70% vaccine

    return html.Div(  # main div
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_dosi['data_somministrazione'], 'y': (ds_dosi['prima_dose'].cumsum())/60360000, 'type': 'bar', 'name': 'Incremento Prime Dosi'},
                                go.Scatter(x=[ds_dosi['data_somministrazione'][0], '2021-10-30'],
                                           y=[0, 1],
                                           mode='lines',
                                           name='Previsione del Governo',
                                           line=go.scatter.Line(color="#FA5541")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l-1], month_last_day_60, month_last_day_70, month_last_day_80, month_last_day],
                                           y=[int(tot_prima)/60360000, 0.6, 0.7, 0.8, 1],
                                           type='scatter',
                                           name='Previsione Mensile',
                                           line=go.scatter.Line(color="#FA924E")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l-1], best_last_day_80, best_last_day],
                                           y=[int(tot_prima)/60360000, 0.8, 1],
                                           type='scatter',
                                           name='Previsione Migliore*',
                                           line=go.scatter.Line(color="#FAC35A"))
                            ],
                            'layout': {
                                'xaxis': dict(
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'yaxis': dict(
                                    tickformat=',.0%',  # percentage on y axis
                                    range=[0, 1]
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5,
                                    y=-0.2
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    )


# dropdown select
def dropdown_effetti_decessi_contagi_graph():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_effetti_decessi_contagi_graph',
                                     options=get_dropdown_data(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Dato Nazionale'
                                     ), style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5,
                        className='mt-2')
                ])
            ])
        ])
    ])


# effect contagi
@app.callback(
    Output('effetti_contagi_graph', 'children'),
    [Input('dropdown_effetti_decessi_contagi_graph', 'value')])
def effetti_contagi_graph(regione):
    if regione == 'Dato Nazionale':
        refresh_data()
        dec = ddc
        dec['nuovi_positivi_avg'] = ddc['nuovi_positivi'].rolling(30).mean()
    else:
        # edit regions
        if regione == 'Friuli-Venezia Giulia': regione = 'Friuli Venezia Giulia'
        elif regione == 'Provincia Autonoma Bolzano / Bozen': regione = 'P.A. Bolzano'
        elif regione == 'Provincia Autonoma Trento': regione = 'P.A. Trento'
        elif regione == "Valle d'Aosta / Vallée d'Aoste": regione = "Valle d'Aosta"
        ddcr = pandas.read_csv(decessi_contagi_regioni)
        reg_ddcr = ddcr.loc[ddcr['denominazione_regione'] == regione]
        dec = reg_ddcr.copy()
        dec['nuovi_positivi_avg'] = dec['nuovi_positivi'].rolling(30).mean()
    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': dec['data'], 'y': dec['nuovi_positivi'], 'type': 'bar', 'name': 'Nuovi Positivi',
                                 'marker': dict(color='#D9615D')},
                                # avg 30 day
                                {'x': dec['data'], 'y': dec['nuovi_positivi_avg'], 'type': 'scatter',
                                 'name': 'Media 30g',
                                 'marker': dict(color='#FF726E')},
                                # line start vaccine
                                go.Scatter(x=['2020-12-27', '2020-12-27'],
                                           y=[0, max(dec['nuovi_positivi'])],
                                           mode='lines',
                                           name='Inizio Vaccini',
                                           hoverinfo='none',
                                           line=go.scatter.Line(color="#4F4747"))
                            ],
                            'layout': {
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5,
                                    y=-0.2
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    ], className='container-2')


# effect contagi
@app.callback(
    Output('effetti_decessi_graph', 'children'),
    [Input('dropdown_effetti_decessi_contagi_graph', 'value')])
def effetti_decessi_graph(regione):
    if regione == 'Dato Nazionale':
        refresh_data()
        ded = ddc
        ded['nuovi_decessi'] = ded.deceduti.diff().fillna(ded.deceduti)
        ded['nuovi_decessi'].iloc[121] = 31  # error -31
        # avg
        ded['nuovi_decessi_avg'] = ded['nuovi_decessi'].rolling(30).mean()
    else:
        # edit regions
        if regione == 'Friuli-Venezia Giulia': regione = 'Friuli Venezia Giulia'
        elif regione == 'Provincia Autonoma Bolzano / Bozen': regione = 'P.A. Bolzano'
        elif regione == 'Provincia Autonoma Trento': regione = 'P.A. Trento'
        elif regione == "Valle d'Aosta / Vallée d'Aoste": regione = "Valle d'Aosta"
        ddcr = pandas.read_csv(decessi_contagi_regioni)
        reg_ddcr = ddcr.loc[ddcr['denominazione_regione'] == regione]
        ded = reg_ddcr.copy()
        ded['nuovi_decessi'] = ded.deceduti.diff().fillna(ded.deceduti)
        ded['nuovi_decessi_avg'] = ded['nuovi_decessi'].rolling(30).mean()
    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ded['data'], 'y': ded['nuovi_decessi'], 'type': 'bar', 'name': 'Decessi',
                                 'marker': dict(color='#756B6B')},
                                # avg 30 day
                                {'x': ded['data'], 'y': ded['nuovi_decessi_avg'], 'type': 'scatter', 'name': 'Media 30g',
                                 'marker': dict(color='#C2B0B0')},
                                # line start vaccine
                                go.Scatter(x=['2020-12-27', '2020-12-27'],
                                           y=[0, max(ded['nuovi_decessi'])],
                                           mode='lines',
                                           name='Inizio Vaccini',
                                           hoverinfo='none',
                                           line=go.scatter.Line(color="#1F1C1C"))
                            ],
                            'layout': {
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5,
                                    y=-0.2
                                )
                            }
                        },
                        config=chart_config
                    )
                )
            )
        ])
    ], className='container-2')


def layout():
    refresh_data()
    return html.Div([
        html.Link(rel="stylesheet", media="screen and (min-width: 900px)", href="./assets/big.css"),
        html.Link(rel="stylesheet", media="screen and (max-width: 900px)", href="./assets/small.css"),
        html.Div([html.Br(), html.Br(), html.Center(html.H1('Vaccini')), html.Br(), html.Br()]),
        html.Div([vaccine_update()]),
        html.Div([vaccine_update_bar()]),
        html.Div(html.Center(html.I([html.Br(), "L'obiettivo della campagna di vaccinazione della popolazione è prevenire le morti da COVID-19 e raggiungere al più presto l'immunità di gregge per il SARS-CoV2", html.Br(), "La campagna è partita il ", html.B("27 dicembre"), ", vista l'approvazione da parte dell'EMA (European Medicines Agency) del primo vaccino anti COVID-19.", html.Br(), "Dopo una fase iniziale, che dovrà essere limitata, per il numero di dosi consegnate, essa si svilupperà in continuo crescendo.", html.Br(), "I vaccini saranno offerti a tutta la popolazione, secondo un ordine di priorità, che tiene conto del rischio di malattia, dei tipi di vaccino e della loro disponibilità."], style={'font-size': 'large'}))),
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Dati del Giorno')), html.Center(html.I('dati aggionati del '+str(last_update), style={'font-size': '14px'})), html.Br()]),
        html.Div([dropdown_vaccine_daily(), html.Br()]),
        html.Div(id='vaccine_daily'),
        html.Div([html.Br(), html.Br(), html.Center(html.H2('Vaccini & Dosi'))]),
        html.Div([html.Div(id='vaccine_graph'), html.Div(id='dosi_graph')], className='container-1'),
        html.Div([html.Br(), html.Center(html.H2('Categorie')), html.Center(html.I('I dati sono calcolati sulle somministrazioni delle prime dosi', style={'font-size': '14px'})), html.Br(), html.Br()]),
        html.Div([category()]),
        html.Div([category_global()]),
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Vaccini per fascia di età')), html.Center(html.I('I dati sono calcolati sulle somministrazioni delle prime dosi', style={'font-size': '14px'}))]),
        html.Div([dropdown_vaccine_age_bar()]),
        html.Div(id='vaccine_age_bar'),
        html.Div([html.Div(id='category_global')], className='container-1'),
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Previsioni')), html.Center(html.I('Il modello utilizza i dati giornalieri sulle somministrazioni delle prime dosi', style={'font-size': '14px'})), html.Center(html.I('*Media basata sul valore massimo di prime dosi fatte in un giorno, ad ora '+str(max_prima_f), style={'font-size': '14px'}))]),
        html.Div([previsione()]),
        html.Div(html.Center([html.Br(), "Nell’ultimo ", html.B("mese"), " sono state somministrate ", html.Mark([html.B(str(max_prima_f)), " prime dosi"], style={'background-color': '#F5C05F'}),
             " in ", html.B("Italia"), " di cui ", html.Mark([html.B(str(tot_janssen)), " monodose"], style={'background-color': '#F5C05F'}), html.Br(),
             "A questo ritmo il ", html.B("70% della popolazione"), " sarà vaccinata entro il ", html.Mark([str(month_last_day_vaccine)], style={'background-color': '#F5C05F'})])),
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Effetti dei Vaccini nel Tempo')), html.Br()]),
        html.Div([dropdown_effetti_decessi_contagi_graph(), html.Br()]),
        html.Div([html.Div(id='effetti_contagi_graph'), html.Div(id='effetti_decessi_graph')], className='container-1')
    ])


app.layout = layout

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
