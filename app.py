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
fascia_anagrafica = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/platea.csv'
somministrazioni = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv'
decessi_contagi = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
decessi_contagi_regioni = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'
population = 0

last_update = ''  # last update
max_prima_f = ''  # max first dose in 1day
tot_janssenf = ''  # tot only 1 dose format
tot_janssen = ''  # tot only 1 dose
month_last_day_vaccine = ''  # 90% population vaccine date
percent_mese = ''  # percentage
percent_mese_vaccine = ''
percent_mese_death = ''  # percentage death
percent_mese_vaccine_death = ''
primadose = 0
secondadose = 0
terzadose = 0  #dose_addizionale_booster
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
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=0.8, maximum-scale=1.2, minimum-scale=0.5'}],
                requests_pathname_prefix='/vaccine/',
                routes_pathname_prefix='/vaccine/')
app.title = 'Dashboard Vaccini'
server = app.server
# chart config
chart_config = {'displaylogo': False, 'displayModeBar': False, 'responsive': True}
# slider buttons (1m, 3m, 6m, all)
slider_button = list([
    dict(count=1, label="1m", step="month", stepmode="backward"),
    dict(count=3, label="3m", step="month", stepmode="backward"),
    dict(count=6, label="6m", step="month", stepmode="backward"),
    dict(step="all")
])

# refresh data
def refresh_data():
    global today, last_update, max_prima_f
    global dc, ds, dfa, ddc, dfe, tot_dfe, ds_dosi
    global tot_prima_dose, tot_seconda_dose, tot_terza_dose, tot_prima, tot_seconda, tot_terza, tot_covid, tot_with_covid
    global percent_mese_death, percent_mese
    # read csv for url and get date
    dc = pandas.read_csv(consegne)
    ds = pandas.read_csv(somministrazioni)
    ddc = pandas.read_csv(decessi_contagi)
    dfe = pandas.read_csv(fascia_anagrafica)
    today = date.today()

    # doses delivered
    dc = dc.groupby('data_consegna').agg({'numero_dosi': 'sum'}).reset_index()
    # doses administered
    ds_dosi = ds.groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'pregressa_infezione': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()

    #last update date
    ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
    if len(ds_prime_dosi) == 0: last_update = date.today()
    else: last_update = date.today() - timedelta(days=1)
    # max first
    max_prima = int(max(ds_dosi['prima_dose']))
    max_prima_f = '{:,}'.format(max_prima).replace(',', '.')  # format max first dose
    # percentage death-positive
    date_format = "%Y-%m-%d"  # date format
    ora = datetime.strptime(str(today), date_format)
    mese = ora - relativedelta(months=1)
    # positive
    month_prima_p = ddc.loc[ddc['data'].between(str(mese)[:10], str(ora)[:10]), ['nuovi_positivi']].sum()
    month_pprima_p = ddc.loc[ddc['data'].between(str(mese - relativedelta(months=1))[:10], str(mese)[:10]), ['nuovi_positivi']].sum()
    percent_mese = round((int(month_prima_p) / month_pprima_p) * 100, 2)
    # death
    ddc['nuovi_decessi'] = ddc.deceduti.diff().fillna(ddc.deceduti)
    month_prima_d = ddc.loc[ddc['data'].between(str(mese)[:10], str(ora)[:10]), ['nuovi_decessi']].sum()
    month_pprima_d = ddc.loc[ddc['data'].between(str(mese - relativedelta(months=1))[:10], str(mese)[:10]), ['nuovi_decessi']].sum()
    percent_mese_death = round((int(month_prima_d) / month_pprima_d) * 100, 2)
    # first dose from the start
    tot_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['prima_dose']].sum()
    tot_prima_dose = '{:,}'.format(int(tot_prima)).replace(',', '.')
    # second dose from the start
    tot_seconda = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['seconda_dose']].sum()
    tot_seconda_dose = '{:,}'.format(int(tot_seconda)).replace(',', '.')
    # third dose from the start
    tot_terza = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2021-09-15', str(today)), ['dose_addizionale_booster']].sum()
    tot_terza_dose = '{:,}'.format(int(tot_terza)).replace(',', '.')
    # with covid
    tot_covid = ds_dosi.loc[ds_dosi['data_somministrazione'].between('2020-12-27', str(today)), ['pregressa_infezione']].sum()
    tot_with_covid = '{:,}'.format(int(tot_covid)).replace(',', '.')
    # age
    dfa = ds.groupby('fascia_anagrafica').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
    tot_dfe = dfe.groupby('fascia_anagrafica').agg({'totale_popolazione': 'sum'}).reset_index()


# dropdown
def get_dropdown_data():
    selections = []
    selections.append(dict(label='Dato Nazionale', value='Dato Nazionale'))
    for reg in regions:
        selections.append(dict(label=reg, value=reg))
    return selections


# total vaccine status
def vaccine_update():
    global primadose, secondadose, terzadose
    janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg({'prima_dose': 'sum'}).reset_index()
    tot_janssen = janssen.loc[janssen['data_somministrazione'].between('2021-04-05', str(today)), ['prima_dose']].sum()
    # percentage
    prima = int(tot_prima) - int(tot_janssen)
    primadose = round((int(prima) / 60360000) * 100, 2)
    t_secondadose = int(tot_seconda) + int(tot_janssen) + int(tot_covid)  # add only 1 doses and whit covid
    secondadose = round((int(t_secondadose)/60360000)*100, 2)
    terza = int(tot_terza)
    terzadose = round((int(terza) / 60360000) * 100, 2)
    # percentage platea
    p_primadose = round((int(prima) / 50773718) * 100, 2)
    p_secondadose = round((int(t_secondadose) / 50773718) * 100, 2)
    p_terzadose = round((int(terza) / 50773718) * 100, 2)
    # formating
    tot_prima_dose = '{:,}'.format(int(prima)).replace(',', '.')
    tot_seconda_dose = '{:,}'.format(int(t_secondadose)).replace(',', '.')
    tot_terza_dose = '{:,}'.format(int(terza)).replace(',', '.')

    return html.Div([
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Prima dose', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1(tot_prima_dose, style={'color': '#F5C05F', 'font-size': '45px'})
                    ),
                ]),
                # Percentage platea
                html.Tr([
                    html.Td(html.B(
                        str(p_primadose) + '% della platea', style={'color': '#F5C05F', 'font-size': '14px'}
                    ))
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        str(primadose) + '% della popolazione', style={'color': '#F5C05F', 'font-size': '14px'}
                    ))
                ]),
            ], className='table')
        ], className='container-3'),
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Vaccinati', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1(tot_seconda_dose, style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Percentage platea
                html.Tr([
                    html.Td(html.B(
                        str(p_secondadose) + '% della platea', style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        str(secondadose) + '% della popolazione', style={'color': '#E83A8E', 'font-size': '14px'}
                    ))
                ]),
            ], className='table')
        ], className='container-3'),
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Terza dose', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1(tot_terza_dose, style={'color': '#B768FE', 'font-size': '45px'})
                    ),
                ]),
                # Percentage platea
                html.Tr([
                    html.Td(html.B(
                        str(p_terzadose) + '% della platea', style={'color': '#B768FE', 'font-size': '14px'}
                    ))
                ]),
                # Percentage
                html.Tr([
                    html.Td(html.B(
                        str(terzadose) + '% della popolazione', style={'color': '#B768FE', 'font-size': '14px'}
                    ))
                ]),
            ], className='table')
        ], className='container-3')
    ], className='container-1')


# total vaccine status
def vaccine_update_mono():
    global tot_janssen, tot_janssenf, primadose, secondadose
    # percentage
    janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg({'prima_dose': 'sum'}).reset_index()
    tot_janssen = janssen.loc[janssen['data_somministrazione'].between('2021-04-05', str(today)), ['prima_dose']].sum()
    tjanssen = round((int(tot_janssen) / 60360000) * 100, 2)
    covid = round((int(tot_covid) / 60360000) * 100, 2)
    # percentage platea
    p_tjanssen = round((int(tot_janssen) / 50773718) * 100, 2)
    p_covid = round((int(tot_covid) / 50773718) * 100, 2)
    # formating
    tot_janssenf = '{:,}'.format(int(tot_janssen)).replace(',', '.')
    tot_covid_dosi = '{:,}'.format(int(tot_covid)).replace(',', '.')
    return html.Div([
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Di cui con vaccino monodose', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1(tot_janssenf, style={'color': '#C93E7F', 'font-size': '30px'})
                    ),
                ]),
                html.Tr([
                    html.Td(
                        html.B('' + str(p_tjanssen) + '% della platea e ' + str(tjanssen) + '% della popolazione', style={'color': '#C93E7F', 'font-size': '12px'})
                    )
                ]),
            ], className='table')
        ], className='container-2'),
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Di cui con pregressa infezione', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(html.H1(tot_covid_dosi, style={'color': '#B33771', 'font-size': '30px'})),
                ]),
                html.Tr([
                    html.Td(html.B('' + str(p_covid) + '% della platea e ' + str(covid) + '% della popolazione', style={'color': '#B33771', 'font-size': '12px'})
                    )
                ]),
            ], className='table')
        ], className='container-2'),
    ], className='container-1')


def vaccine_update_bar():
    return html.Div([
        html.Div([
            dcc.Graph(
                figure={
                    'data': [go.Bar(x=[60360000, 50773718, int(tot_seconda)+int(tot_janssen)+int(tot_covid), int(tot_prima)-int(tot_janssen), int(tot_terza)],
                                    y=['Popolazione', 'Platea', 'Vaccinati', 'Prima dose', 'Terza dose'],
                                    orientation='h',
                                    marker_color=['#6181E8', '#5EAEFF', '#E83A8E', '#F5C05F', '#B768FE'])
                             ],
                    'layout': {
                        'height': 270,  # px
                        'xaxis': dict(rangeslider=dict(visible=False))
                    },
                }, config=chart_config
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
                                     persistence=True, persistence_type='session', value='Dato Nazionale'),
                        style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5, className='mt-2'
                    )
                ])
            ])
        ])
    ])


# vaccine horozzonatal bar
@app.callback(
    Output('vaccine_daily', 'children'),
    [Input('dropdown_vaccine_daily', 'value')])
def vaccine_daily(regione):
    if regione == 'Dato Nazionale':
        tot_consegne = dc.loc[dc['data_consegna'].between('2020-12-27', str(today)), ['numero_dosi']].sum()
        tot_vaccini = int(tot_prima) + int(tot_seconda)
        # today data
        dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(today), 'numero_dosi']
        ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'prima_dose']
        ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'seconda_dose']
        ds_terze_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(today), 'dose_addizionale_booster']
        # check today data
        if len(dc_dosi_consegnate) == 0 and len(ds_prime_dosi) == 0 and len(ds_seconde_dosi) == 0:
            dc_dosi_consegnate = dc.loc[dc['data_consegna'] == str(date.today() - timedelta(days=1)), 'numero_dosi']
            ds_prime_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'prima_dose']
            ds_seconde_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'seconda_dose']
            ds_terze_dosi = ds_dosi.loc[ds_dosi['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'dose_addizionale_booster']
    else:
        dc1 = pandas.read_csv(consegne)
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        ds_dosi1 = reg_ds1.copy().groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
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
        ds_terze_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(today), 'dose_addizionale_booster']

        # check today data
        if len(dc_dosi_consegnate) == 0 and len(ds_prime_dosi) == 0 and len(ds_seconde_dosi) == 0:
            dc_dosi_consegnate = dc1.loc[dc1['data_consegna'] == str(date.today() - timedelta(days=1)), 'numero_dosi']
            ds_prime_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'prima_dose']
            ds_seconde_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'seconda_dose']
            ds_terze_dosi = ds_dosi1.loc[ds_dosi1['data_somministrazione'] == str(date.today() - timedelta(days=1)), 'dose_addizionale_booster']
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
    if len(ds_terze_dosi) == 0:
        ds_terze_dosi = 0
        ds_dosi_totali = ds_dosi_totali + int(ds_terze_dosi)
    else:
        ds_dosi_totali = ds_dosi_totali + int(ds_terze_dosi)
        ds_terze_dosi = '{:,}'.format(int(ds_terze_dosi)).replace(',', '.')
    if ds_dosi_totali != 0:
        ds_dosi_totali = '{:,}'.format(int(ds_dosi_totali)).replace(',', '.')

    return html.Div([
        # first doses
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Prime Dosi', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_prime_dosi) + '', style={'color': '#F5C05F', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(
                        html.B('Totali: ' + str(tot_prima_dose), style={'color': '#F5C05F', 'font-size': '14px'})
                    )
                ])
            ], className='table')
        ], className='container-3'),
        # vaccine
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Seconde Dosi', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_seconde_dosi) + '', style={'color': '#E83A8E', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(
                        html.B('Totali: ' + str(tot_seconda_dose), style={'color': '#E83A8E', 'font-size': '14px'})
                    )
                ])
            ], className='table')
        ], className='container-3'),
        # thrid doses
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Terze Dosi', style={'font-size': '14px'})
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_terze_dosi) + '', style={'color': '#B768FE', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(
                        html.B('Totali: ' + str(tot_terza_dose), style={'color': '#B768FE', 'font-size': '14px'})
                    )
                ])
            ], className='table')
        ], className='container-3'),
        # vaccine
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Vaccini Consegnati', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(dc_dosi_consegnate) + '', style={'color': '#29CF8A', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B('Totali: ' + str(tot_consegne), style={'color': '#29CF8A', 'font-size': '14px'})
                    )
                ])
            ], className='table')
        ], className='container-2'),
        # doses
        html.Div([
            html.Table([
                html.Tr([
                    html.Td('Dosi Somministrate', style={'font-size': '14px'}),
                ]),
                html.Tr([
                    html.Td(
                        html.H1('+ ' + str(ds_dosi_totali) + '', style={'color': '#376FDB', 'font-size': '45px'})
                    )
                ]),
                # Yesterday
                html.Tr([
                    html.Td(html.B('Totali: ' + str(tot_vaccini), style={'color': '#376FDB', 'font-size': '14px'})
                    )
                ])
            ], className='table')
        ], className='container-2'),
    ], className='container-1')


# vaccine horozzonatal bar
@app.callback(
    Output('vaccine_graph', 'children'),
    [Input('dropdown_vaccine_daily', 'value')])
# vaccine and doses graph
def vaccine_graph(regione):
    if regione == 'Dato Nazionale':
        # vaccine
        ds_pfizer = ds.loc[ds['fornitore'] == 'Pfizer/BioNTech'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_moderna = ds.loc[ds['fornitore'] == 'Moderna'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_astra = ds.loc[ds['fornitore'] == 'Vaxzevria (AstraZeneca)'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_janssen = ds.loc[ds['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
    else:
        # vaccine
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        ds_dosi1 = reg_ds1.copy().groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum', 'fornitore': 'last'}).reset_index()
        ds_pfizer = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Pfizer/BioNTech'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_moderna = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Moderna'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_astra = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Vaxzevria (AstraZeneca)'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        ds_janssen = ds_dosi1.loc[ds_dosi1['fornitore'] == 'Janssen'].groupby('data_somministrazione').agg(
            {'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                {'x': ds_astra['data_somministrazione'],
                                 'y': ds_astra['prima_dose'] + ds_astra['seconda_dose'] + ds_astra['dose_addizionale_booster'],
                                 'type': 'bar',
                                 'name': 'AstraZeneca',
                                 'marker': dict(color='#537BE0')},
                                {'x': ds_pfizer['data_somministrazione'],
                                 'y': ds_pfizer['prima_dose'] + ds_pfizer['seconda_dose'] + ds_pfizer['dose_addizionale_booster'],
                                 'type': 'bar',
                                 'name': 'Pfizer',
                                 'marker': dict(color='#95A9DE')},
                                {'x': ds_moderna['data_somministrazione'],
                                 'y': ds_moderna['prima_dose'] + ds_moderna['seconda_dose'] + ds_moderna['dose_addizionale_booster'],
                                 'type': 'bar',
                                 'name': 'Moderna',
                                 'marker': dict(color='#395499')},
                                {'x': ds_janssen['data_somministrazione'],
                                 'y': ds_janssen['prima_dose'] + ds_janssen['seconda_dose'] + ds_janssen['dose_addizionale_booster'],
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
                                    x=0.5, y=-0.2
                                )
                            }
                        }, config=chart_config
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
        prima_seconda = ds.groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
    else:
        ds1 = pandas.read_csv(somministrazioni)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        prima_seconda = reg_ds1.copy().groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
    return html.Div([
            dbc.Container([
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            figure={
                                'data': [
                                    go.Bar(x=prima_seconda['data_somministrazione'],
                                           y=prima_seconda['prima_dose'],
                                           name='Prima Dose', marker=dict(color='#F5C05F')),
                                    go.Bar(x=prima_seconda['data_somministrazione'],
                                           y=prima_seconda['seconda_dose'],
                                           name='Seconda Dose', marker=dict(color='#78F5B3')),
                                    go.Bar(x=prima_seconda['data_somministrazione'],
                                           y=prima_seconda['dose_addizionale_booster'],
                                           name='Terza Dose', marker=dict(color='#B768FE')),
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
                                        x=0.5, y=-0.2,
                                    )
                                }
                            }, config=chart_config
                        )
                    )
                )
            ])
        ], className='container-2')


# dropdown select
def dropdown_vaccine_age_bar():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_vaccine_age_bar',
                                     options=get_dropdown_data(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Dato Nazionale'),
                        style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5, className='mt-2'
                    )
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
        figure_age = {
            'data': [go.Bar(x=[int(dfa['prima_dose'][0])-int(int(dfa['seconda_dose'][0])-int(dfa['dose_addizionale_booster'][0])), int(dfa['prima_dose'][1])-int(int(dfa['seconda_dose'][1])-int(dfa['dose_addizionale_booster'][1])),
                               int(dfa['prima_dose'][2])-int(int(dfa['seconda_dose'][2])-int(dfa['dose_addizionale_booster'][2])), int(dfa['prima_dose'][3])-int(int(dfa['seconda_dose'][3])-int(dfa['dose_addizionale_booster'][3])),
                               int(dfa['prima_dose'][4])-int(int(dfa['seconda_dose'][4])-int(dfa['dose_addizionale_booster'][4])), int(dfa['prima_dose'][5])-int(int(dfa['seconda_dose'][5])-int(dfa['dose_addizionale_booster'][5])),
                               int(dfa['prima_dose'][6])-int(int(dfa['seconda_dose'][6])-int(dfa['dose_addizionale_booster'][6])),
                               int(int(dfa['prima_dose'][7])-int(int(dfa['seconda_dose'][7])-int(dfa['dose_addizionale_booster'][7]))) + int(int(dfa['prima_dose'][8])-(int(dfa['seconda_dose'][8])-int(dfa['dose_addizionale_booster'][8])))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#F5C05F',
                            name='Prima Dose'
                            ),
                     go.Bar(x=[int(dfa['seconda_dose'][0])-int(dfa['dose_addizionale_booster'][0]), int(dfa['seconda_dose'][1])-int(dfa['dose_addizionale_booster'][1]),
                               int(dfa['seconda_dose'][2])-int(dfa['dose_addizionale_booster'][2]), int(dfa['seconda_dose'][3])-int(dfa['dose_addizionale_booster'][3]),
                               int(dfa['seconda_dose'][4])-int(dfa['dose_addizionale_booster'][4]), int(dfa['seconda_dose'][5])-int(dfa['dose_addizionale_booster'][5]),
                               int(dfa['seconda_dose'][6])-int(dfa['dose_addizionale_booster'][6]),
                               int(int(dfa['seconda_dose'][7])-int(dfa['dose_addizionale_booster'][7]))+int(int(dfa['seconda_dose'][8])-int(dfa['dose_addizionale_booster'][8]))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#E83A8E',
                            name='Seconda Dose'
                            ),
                     go.Bar(x=[int(dfa['dose_addizionale_booster'][0]), int(dfa['dose_addizionale_booster'][1]), int(dfa['dose_addizionale_booster'][2]),
                               int(dfa['dose_addizionale_booster'][3]), int(dfa['dose_addizionale_booster'][4]), int(dfa['dose_addizionale_booster'][4]),
                               int(dfa['dose_addizionale_booster'][6]), int(dfa['dose_addizionale_booster'][8])+int(dfa['dose_addizionale_booster'][8])],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#B768FE',
                            name='Terza Dose'
                            ),
                     go.Bar(x=[int(tot_dfe.loc[tot_dfe.index[0], 'totale_popolazione']) - int(dfa['prima_dose'][0]),
                               int(tot_dfe.loc[tot_dfe.index[1], 'totale_popolazione']) - int(dfa['prima_dose'][1]),
                               int(tot_dfe.loc[tot_dfe.index[2], 'totale_popolazione']) - int(dfa['prima_dose'][2]),
                               int(tot_dfe.loc[tot_dfe.index[3], 'totale_popolazione']) - int(dfa['prima_dose'][3]),
                               int(tot_dfe.loc[tot_dfe.index[4], 'totale_popolazione']) - int(dfa['prima_dose'][4]),
                               int(tot_dfe.loc[tot_dfe.index[5], 'totale_popolazione']) - int(dfa['prima_dose'][5]),
                               int(tot_dfe.loc[tot_dfe.index[6], 'totale_popolazione']) - int(dfa['prima_dose'][6]),
                               int(int(tot_dfe.loc[tot_dfe.index[7], 'totale_popolazione'])+int(tot_dfe.loc[tot_dfe.index[8], 'totale_popolazione'])) - int(int(dfa['prima_dose'][7])+int(dfa['prima_dose'][8]))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#6181E8',
                            name='Non vaccinati'
                            )
                     ],
            'layout': {
                'barmode': 'stack',  # stack data
                'height': 340,  # px
                'xaxis': dict(rangeslider=dict(visible=False)),
                'legend': dict(
                    orientation="h",
                    xanchor="center",
                    x=0.5, y=-0.2
                )
            },
        }
    else:
        if regione == 'Provincia Autonoma Bolzano / Bozen': reg = 'P.A. Bolzano'
        elif regione == 'Provincia Autonoma Trento': reg = 'P.A. Trento'
        elif regione == "Valle d'Aosta / Vallée d'Aoste": reg = "Valle d'Aosta"
        else: reg = regione
        ds1 = pandas.read_csv(somministrazioni)
        dfe1 = pandas.read_csv(fascia_anagrafica)
        reg_ds1 = ds1.loc[ds1['nome_area'] == regione]
        dfa1 = reg_ds1.copy().groupby('fascia_anagrafica').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum'}).reset_index()
        reg_dfe1 = dfe1.loc[dfe1['nome_area'] == reg]
        figure_age = {
            'data': [go.Bar(x=[int(dfa1['prima_dose'][0])-int(int(dfa1['seconda_dose'][0])-int(dfa1['dose_addizionale_booster'][0])), int(dfa1['prima_dose'][1])-int(int(dfa1['seconda_dose'][1])-int(dfa1['dose_addizionale_booster'][1])),
                               int(dfa1['prima_dose'][2])-int(int(dfa1['seconda_dose'][2])-int(dfa1['dose_addizionale_booster'][2])), int(dfa1['prima_dose'][3])-int(int(dfa1['seconda_dose'][3])-int(dfa1['dose_addizionale_booster'][3])),
                               int(dfa1['prima_dose'][4])-int(int(dfa1['seconda_dose'][4])-int(dfa1['dose_addizionale_booster'][4])), int(dfa1['prima_dose'][5])-int(int(dfa1['seconda_dose'][5])-int(dfa1['dose_addizionale_booster'][5])),
                               int(dfa1['prima_dose'][6])-int(int(dfa1['seconda_dose'][6])-int(dfa1['dose_addizionale_booster'][6])),
                               int(int(dfa1['prima_dose'][7])-int(int(dfa1['seconda_dose'][7])-int(dfa1['dose_addizionale_booster'][7]))) + int(int(dfa1['prima_dose'][8])-(int(dfa1['seconda_dose'][8])-int(dfa1['dose_addizionale_booster'][8])))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#F5C05F',
                            name='Prima Dose'
                            ),
                     go.Bar(x=[int(dfa1['seconda_dose'][0])-int(dfa1['dose_addizionale_booster'][0]), int(dfa1['seconda_dose'][1])-int(dfa1['dose_addizionale_booster'][1]),
                               int(dfa1['seconda_dose'][2])-int(dfa1['dose_addizionale_booster'][2]), int(dfa1['seconda_dose'][3])-int(dfa1['dose_addizionale_booster'][3]),
                               int(dfa1['seconda_dose'][4])-int(dfa1['dose_addizionale_booster'][4]), int(dfa1['seconda_dose'][5])-int(dfa1['dose_addizionale_booster'][5]),
                               int(dfa1['seconda_dose'][6])-int(dfa1['dose_addizionale_booster'][6]),
                               int(int(dfa1['seconda_dose'][7])-int(dfa1['dose_addizionale_booster'][7]))+int(int(dfa1['seconda_dose'][8])-int(dfa1['dose_addizionale_booster'][8]))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#E83A8E',
                            name='Seconda Dose'
                            ),
                     go.Bar(x=[int(dfa1['dose_addizionale_booster'][0]), int(dfa1['dose_addizionale_booster'][1]), int(dfa1['dose_addizionale_booster'][2]),
                               int(dfa1['dose_addizionale_booster'][3]), int(dfa1['dose_addizionale_booster'][4]), int(dfa1['dose_addizionale_booster'][4]),
                               int(dfa1['dose_addizionale_booster'][6]), int(dfa1['dose_addizionale_booster'][8])+int(dfa1['dose_addizionale_booster'][8])],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#B768FE',
                            name='Terza Dose'
                            ),
                     go.Bar(x=[int(reg_dfe1.loc[reg_dfe1.index[0], 'totale_popolazione']) - int(dfa1['prima_dose'][0]),
                               int(reg_dfe1.loc[reg_dfe1.index[1], 'totale_popolazione']) - int(dfa1['prima_dose'][1]),
                               int(reg_dfe1.loc[reg_dfe1.index[2], 'totale_popolazione']) - int(dfa1['prima_dose'][2]),
                               int(reg_dfe1.loc[reg_dfe1.index[3], 'totale_popolazione']) - int(dfa1['prima_dose'][3]),
                               int(reg_dfe1.loc[reg_dfe1.index[4], 'totale_popolazione']) - int(dfa1['prima_dose'][4]),
                               int(reg_dfe1.loc[reg_dfe1.index[5], 'totale_popolazione']) - int(dfa1['prima_dose'][5]),
                               int(reg_dfe1.loc[reg_dfe1.index[6], 'totale_popolazione']) - int(dfa1['prima_dose'][6]),
                               int(int(reg_dfe1.loc[reg_dfe1.index[7], 'totale_popolazione'])+int(reg_dfe1.loc[reg_dfe1.index[8], 'totale_popolazione'])) - int(int(dfa1['prima_dose'][7])+int(dfa1['prima_dose'][8]))],
                            y=['12-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+'],
                            orientation='h',
                            marker_color='#6181E8',
                            name='Non vaccinati'
                            )
                     ],
            'layout': {
                'barmode': 'stack',  # stack data
                'height': 340,  # px
                'xaxis': dict(rangeslider=dict(visible=False)),
                'legend': dict(
                    orientation="h",
                    xanchor="center",
                    x=0.5, y=-0.2
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
    global month_last_day_vaccine
    date_format = "%Y-%m-%d"  # date format
    ora = datetime.strptime(str(today), date_format)
    l = len(ds_dosi['data_somministrazione'])  # total vaccine day
    sett = 42252000  #70
    settc = 45270000  #75
    ott = 48288000  #80%
    ottc= 51306000  #85%
    nov = 54324000  #90%
    # month
    month_prima = ds_dosi.loc[ds_dosi['data_somministrazione'].between(str(ora - relativedelta(months=1))[:10], str(ora)[:10]), ['prima_dose']].sum()
    month_seconda = ds_dosi.loc[ds_dosi['data_somministrazione'].between(str(ora - relativedelta(months=1))[:10], str(ora)[:10]), ['seconda_dose']].sum()
    month_terza = ds_dosi.loc[ds_dosi['data_somministrazione'].between(str(ora - relativedelta(months=1))[:10], str(ora)[:10]), ['dose_addizionale_booster']].sum()
    month_day_passati = (ora - (ora - relativedelta(months=1))).days
    # first
    month_day_p = ((60360000 - int(tot_prima)) / int(month_prima)) * month_day_passati
    month_last_day_p = str(ora + timedelta(days=month_day_p))[:10]
    month_day_90_p = ((ottc - int(tot_prima)) / int(month_prima)) * month_day_passati  # 85%
    month_last_day_90_p = str(ora + timedelta(days=month_day_90_p))[:10]
    # second
    month_day_s = ((60360000 - int(tot_seconda)) / int(month_seconda)) * month_day_passati
    month_last_day_s = str(ora + timedelta(days=month_day_s) + timedelta(days=month_day_p))[:10]
    month_day_90_s = ((ott - int(tot_seconda)) / int(month_seconda)) * month_day_passati  # 80%
    month_last_day_90_s = str(ora + timedelta(days=month_day_90_s) + timedelta(days=month_day_90_p))[:10]
    # third
    month_day_t = ((60360000 - int(tot_terza)) / int(month_terza)) * month_day_passati
    month_last_day_t = str(ora + timedelta(days=month_day_t) + timedelta(days=month_day_s) + timedelta(days=month_day_p))[:10]
    month_day_90_t = ((sett - int(tot_terza)) / int(month_terza)) * month_day_passati  # 70%
    month_last_day_90_t = str(ora + timedelta(days=month_day_90_t) + timedelta(days=month_day_90_s) + timedelta(days=month_day_90_p))[:10]
    # last day 90% vaccine
    month_last_day_vaccine = month_last_day_90_p

    return html.Div(  # main div
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': [
                                go.Bar(x=ds_dosi['data_somministrazione'],
                                       y=((ds_dosi['dose_addizionale_booster'].cumsum()) / 60360000),
                                       name='Incremento Terze Dosi', marker=dict(color='#B768FE')),
                                go.Bar(x=ds_dosi['data_somministrazione'],
                                       y=((ds_dosi['seconda_dose'].cumsum()) / 60360000) - ((ds_dosi['dose_addizionale_booster'].cumsum()) / 60360000),
                                       text=(((ds_dosi['seconda_dose'].cumsum()) / 60360000) * 100).tolist(),
                                       name='Incremento Seconde Dosi', marker=dict(color='#78F5B3'),
                                       hovertemplate='%{text:.0f}' + '%'),
                                go.Bar(x=ds_dosi['data_somministrazione'],
                                       y=((ds_dosi['prima_dose'].cumsum()) / 60360000) - ((ds_dosi['seconda_dose'].cumsum()) / 60360000),
                                       text=(((ds_dosi['prima_dose'].cumsum()) / 60360000) * 100).tolist(),
                                       name='Incremento Prime Dosi', marker=dict(color='#F5C05F'),
                                       hovertemplate='%{text:.0f}' + '%'),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][0], '2021-10-30'],
                                           y=[0, 1],
                                           mode='lines',
                                           name='Previsione del Governo Vaccinati',
                                           line=go.scatter.Line(color="#FA5541")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l - 1], month_last_day_90_p, month_last_day_p],
                                           y=[int(tot_prima) / 60360000, 0.85, 1],
                                           type='scatter',
                                           name='Previsione Mensile 1ª Dose',
                                           line=go.scatter.Line(color="#F5C05F")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l - 1], month_last_day_90_s, month_last_day_s],
                                           y=[int(tot_seconda) / 60360000, 0.8, 1],
                                           type='scatter',
                                           name='Previsione Mensile 2ª Dose',
                                           line=go.scatter.Line(color="#78F5B3")),
                                go.Scatter(x=[ds_dosi['data_somministrazione'][l - 1], month_last_day_90_t, month_last_day_t],
                                           y=[int(tot_terza) / 60360000, 0.7, 1],
                                           type='scatter',
                                           name='Previsione Mensile 3ª Dose',
                                           line=go.scatter.Line(color="#B768FE")),
                            ],
                            'layout': {
                                'barmode': 'stack',
                                'xaxis': dict(
                                    rangeslider=dict(visible=False),
                                    type='date',
                                    range=['2020-12-27', '2023-04-01']
                                ),
                                'yaxis': dict(
                                    tickformat=',.0%',  # percentage on y axis
                                    range=[0, 1]
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.1, y=-0.2,
                                    itemclick=False, itemdoubleclick=False
                                )
                            }
                        }, config=chart_config
                    )
                )
            )
        ])
    )

# dropdown
def get_dropdown_data2():
    selections = []
    for reg in regions:
        selections.append(dict(label=reg, value=reg))
    return selections

def dropdown_velocity_dosi_graph():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_velocity_dosi_graph', multi=True,
                                     options=get_dropdown_data2(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Lombardia'),
                        style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5, className='mt-2'
                    )
                ])
            ])
        ])
    ])

# effect contagi
@app.callback(
    Output('velocity_dosi_graph', 'children'),
    [Input('dropdown_velocity_dosi_graph', 'value')])
def velocity_dosi_graph(regione):
    ds1 = pandas.read_csv(somministrazioni)
    data = ['']
    traces = ['']
    if type(regione) == str:
        regione = [regione]
    for reg in regione:
        ds2 = ds1[ds1['nome_area'] == reg]
        ds_dosi_velocity = ds2.groupby('data_somministrazione').agg({'prima_dose': 'sum', 'seconda_dose': 'sum', 'dose_addizionale_booster': 'sum', 'nome_area': 'last'}).reset_index()
        data.append(ds_dosi_velocity)
    data.pop(0)
    for dati in data:
        traces.append(go.Scatter({'x': dati['data_somministrazione'], 'y': dati['prima_dose']+dati['seconda_dose']+dati['dose_addizionale_booster'], 'mode': 'lines',
                                  'name': f"{dati['nome_area'].iloc[0]}"}))
    traces.pop(0)

    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': traces,
                            'layout': {
                                'xaxis': dict(
                                    rangeselector=dict(buttons=slider_button),
                                    rangeslider=dict(visible=False),
                                    type='date'
                                ),
                                'legend': dict(
                                    orientation="h",
                                    xanchor="center",
                                    x=0.5, y=-0.2
                                )
                            }
                        }, config=chart_config
                    )
                )
            )
        ])
    ], className='container-1')


# dropdown select
def dropdown_effetti_decessi_contagi_graph():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_effetti_decessi_contagi_graph',
                                     options=get_dropdown_data(), clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Dato Nazionale'),
                        style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5, className='mt-2'
                    )
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
                                    x=0.5, y=-0.2
                                )
                            }
                        }, config=chart_config
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
                                    x=0.5, y=-0.2
                                )
                            }
                        }, config=chart_config
                    )
                )
            )
        ])
    ], className='container-2')


# dropdown select
def dropdown_riduzione_graph():
    return html.Div([
        html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(id='dropdown_riduzione_graph',
                                     options=[
                                        {'label': 'Nuovi Positivi', 'value': 'Nuovi Positivi'},
                                        {'label': 'Ospedalizzati', 'value': 'Ospedalizzati'},
                                        {'label': 'Terapia Intensiva', 'value': 'Terapia Intensiva'},
                                        {'label': 'Decessi', 'value': 'Decessi'}
                                     ], clearable=False, searchable=False,
                                     persistence=True, persistence_type='session', value='Nuovi Positivi'),
                        style={'margin-left': 'auto', 'margin-right': 'auto'}, width=12, lg=5, className='mt-2'
                    )
                ])
            ])
        ])
    ])


# riduzione_graph
@app.callback(
    Output('riduzione_graph', 'children'),
    [Input('dropdown_riduzione_graph', 'value')])
def riduzione_graph(value):
    ds1 = pandas.read_csv(somministrazioni)
    ddcr = pandas.read_csv(decessi_contagi_regioni)
    date_format = "%Y-%m-%d"  # date format
    ora = datetime.strptime(str(today), date_format)
    traces = ['']

    for reg in regions:
        # contagi
        if reg == 'Friuli-Venezia Giulia': reg1 = 'Friuli Venezia Giulia'
        elif reg == 'Provincia Autonoma Bolzano / Bozen': reg1 = 'P.A. Bolzano'
        elif reg == 'Provincia Autonoma Trento': reg1 = 'P.A. Trento'
        elif reg == "Valle d'Aosta / Vallée d'Aoste": reg1 = "Valle d'Aosta"
        else: reg1 = reg
        # population
        if reg1 == 'Abruzzo': popolazione = 1312000
        elif reg1 == 'Basilicata': popolazione = 562869
        elif reg1 == 'Calabria': popolazione = 1947000
        elif reg1 == 'Campania': popolazione = 5802000
        elif reg1 == 'Emilia-Romagna': popolazione = 4459000
        elif reg1 == 'Friuli Venezia Giulia': popolazione = 1215000
        elif reg1 == 'Lazio': popolazione = 5879000
        elif reg1 == 'Liguria': popolazione = 1551000
        elif reg1 == 'Lombardia': popolazione = 10060000
        elif reg1 == 'Marche': popolazione = 1525000
        elif reg1 == 'Molise': popolazione = 305617
        elif reg1 == 'P.A. Bolzano': popolazione = 520891
        elif reg1 == 'P.A. Trento': popolazione = 538223
        elif reg1 == 'Piemonte': popolazione = 4356000
        elif reg1 == 'Puglia': popolazione = 4029000
        elif reg1 == 'Sardegna': popolazione = 1640000
        elif reg1 == 'Sicilia': popolazione = 5000000
        elif reg1 == 'Toscana': popolazione = 3730000
        elif reg1 == 'Umbria': popolazione = 882015
        elif reg1 == "Valle d'Aosta": popolazione = 125666
        elif reg1 == 'Veneto': popolazione = 4906000
        # data contagi
        ddcr2 = ddcr.loc[ddcr['denominazione_regione'] == reg1]
        ded = ddcr2
        ded['nuovi_decessi'] = ded.deceduti.diff().fillna(ded.deceduti)
        ded['nuovi_decessi'].iloc[121] = 31  # error -31
        ospd = ddcr2
        ospd['nuovi_ospedalizzati'] = ospd.totale_ospedalizzati.diff().fillna(ospd.totale_ospedalizzati)
        # contagi
        ddcr_contagi = ddcr2.loc[ddcr2['data'].between(str(ora - timedelta(days=7))[:10], str(ora)[:10]), ['nuovi_positivi']].sum()
        positive = round((int(ddcr_contagi) * 100000) / popolazione, 2)
        # ospedalizzati
        ddcr_osp = ospd.loc[ddcr2['data'].between(str(ora - timedelta(days=7))[:10], str(ora)[:10]), ['nuovi_ospedalizzati']].sum()
        osp = round((int(ddcr_osp) * 100000) / popolazione, 2)
        # TI
        ddcr_ti = ddcr2.loc[ddcr2['data'].between(str(ora - timedelta(days=7))[:10], str(ora)[:10]), ['ingressi_terapia_intensiva']].sum()
        ti = round((int(ddcr_ti) * 100000) / popolazione, 2)
        # Deceduti
        ddcr_deceduti = ded.loc[ded['data'].between(str(ora - timedelta(days=7))[:10], str(ora)[:10]), ['nuovi_decessi']].sum()
        deceduti = round((int(ddcr_deceduti) * 100000) / popolazione, 2)
        # doses
        ds2 = ds1[ds1['nome_area'] == reg]
        ds_dosi_velocity = ds2.groupby('data_somministrazione').agg({'seconda_dose': 'sum', 'nome_area': 'last'}).reset_index()
        doses = ds_dosi_velocity.loc[ds_dosi_velocity['data_somministrazione'].between('2020-12-27', str(today)), ['seconda_dose']].sum()
        doses_percent = round((int(doses) / popolazione) * 100, 2)
        # traces
        if value == 'Nuovi Positivi':
            if float(positive) < 0:
                positive = 0
            traces.append(go.Scatter({'x': [float(positive)], 'y': [float(doses_percent)], 'mode': 'markers+text', 'marker': dict(color='crimson', size=12), 'text': f"{reg1}", 'textfont': dict(color='#B01B3E'), 'textposition': 'middle right', 'name': f"{reg1}"}))
        elif value == 'Ospedalizzati':
            if float(osp) < 0:
                osp = 0
            traces.append(go.Scatter({'x': [float(osp)], 'y': [float(doses_percent)], 'mode': 'markers+text', 'marker': dict(color='#088BBD', size=12), 'text': f"{reg1}", 'textfont': dict(color='#088BBD'), 'textposition': 'middle right', 'name': f"{reg1}"}))
        elif value == 'Terapia Intensiva':
            if float(ti) < 0:
                ti = 0
            traces.append(go.Scatter({'x': [float(ti)], 'y': [float(doses_percent)], 'mode': 'markers+text', 'marker': dict(color='#C9BF30', size=12), 'text': f"{reg1}", 'textfont': dict(color='#C9BF30'), 'textposition': 'middle right', 'name': f"{reg1}"}))
        else:
            if float(deceduti) < 0:
                deceduti = 0
            traces.append(go.Scatter({'x': [float(deceduti)], 'y': [float(doses_percent)], 'mode': 'markers+text', 'marker': dict(color='#756B6B', size=12), 'text': f"{reg1}", 'textfont': dict(color='#756B6B'), 'textposition': 'middle right', 'name': f"{reg1}"}))
    traces.pop(0)

    return html.Div([
        dbc.Container([
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        figure={
                            'data': traces,
                            'layout': {
                                'xaxis': dict(rangeslider=dict(visible=False)),
                                'yaxis': {'title': 'Percentuale di Vaccinati'},
                                'xaxis': {'title': value},
                                'showlegend': False,
                            }
                        }, config=chart_config
                    )
                )
            )
        ])
    ], className='container-1')

def layout():
    refresh_data()
    return html.Div([
        # style
        html.Link(rel="stylesheet", media="screen and (min-width: 900px)", href="./assets/big.css"),
        html.Link(rel="stylesheet", media="screen and (max-width: 900px)", href="./assets/small.css"),
        # vaccine total
        html.Div([html.Br(), html.Br(), html.Center(html.H1('Vaccini')), html.Br(), html.Br()]),
        html.Div([vaccine_update()]),
        html.Div([vaccine_update_mono()]),
        html.Div([vaccine_update_bar()]),  # orizzonatl bar
        # text
        html.Div(html.Center(html.I([html.Br(), "L'obiettivo della campagna di vaccinazione della popolazione è prevenire le morti da COVID-19 e raggiungere al più presto ",
                                     html.B("l'immunità di gregge"), " per il SARS-CoV2", html.Br(), "La campagna è partita il ", html.B("27 dicembre"), ", ad oggi il ",
                                     html.B(str(primadose)+" %"), " della popolazione italiana è ", html.B("parzialmente protetto"), html.Br(), "Mentre il ", html.B(str(secondadose)+" %"),
                                     " della popolazione ha completato il ciclo vaccinale", html.Br(), "La ", html.B("terza dose"), " verrà somministrata inizialmente a trapiantati e immunodepressi"], style={'font-size': 'large'}))),
        # daily data
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Dati del Giorno')), html.Center(html.I('dati aggionati del '+str(last_update), style={'font-size': '14px'})), html.Br()]),
        html.Div([dropdown_vaccine_daily(), html.Br()]),  # dropdown
        html.Div(id='vaccine_daily'),
        # vaccine and doses
        html.Div([html.Br(), html.Br(), html.Center(html.H2('Vaccini & Dosi'))]),
        html.Div([html.Div(id='vaccine_graph'), html.Div(id='dosi_graph')], className='container-1'),
        # image
        html.Div(html.Center([html.Div([html.Img(src='./assets/ddoses.png', width="45", style={'vertical-align': 'bottom'}), html.B(' 2'), ' Dosi: ', html.I('Pfizer, Moderna e AstraZeneca', style={'font-size': '14px'})], className='container-2'), html.Div([html.Img(src='./assets/doses.png', width="30", style={'vertical-align': 'bottom'}), html.B(' 1'), ' Dose:', html.I(' Janssen', style={'font-size': '14px'})], className='container-2'),
                              html.Div([html.Br(), html.Br(), html.Br(), html.H2('Vaccini per fascia di età'), html.I('I dati sono calcolati sulle somministrazioni delle prime dosi', style={'font-size': '14px'})], className='container-1')], className='container-1')),
        html.Div([dropdown_vaccine_age_bar()]),
        html.Div(id='vaccine_age_bar'),
        html.Div([html.Div(id='category_global')], className='container-1'),
        # forecast
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H1('Previsioni')), html.Center(html.I('Il modello utilizza i dati giornalieri sulle somministrazioni delle prime dosi', style={'font-size': '14px'}))]),
        html.Div([previsione()]),
        # text forecast
        html.Div(html.Center([html.Br(), "Nell'ultimo ", html.B("mese"), " sono state somministrate ", html.Mark([html.B(str(max_prima_f)), " prime dosi"], style={'background-color': '#F5C05F'}),
             " in ", html.B("Italia"), " di cui ", html.Mark([html.B(str(tot_janssenf)), " monodose"], style={'background-color': '#F5C05F'}), html.Br(),
             "A questo ritmo l' ", html.B("80% della popolazione"), " sarà vaccinata entro il ", html.Mark([str(month_last_day_vaccine)], style={'background-color': '#F5C05F'})])),
        # velocity
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Velocità vaccinazioni')), html.Center(html.I('I dati sono calcolati con tutte le dosi', style={'font-size': '14px'}))]),
        html.Div([dropdown_velocity_dosi_graph()]),
        html.Div([html.Div(id='velocity_dosi_graph')], className='container-1'),
        # effect
        html.Div([html.Br(), html.Br(), html.Br(), html.Center(html.H2('Effetti dei Vaccini nel Tempo')), html.Br()]),
        html.Div([dropdown_effetti_decessi_contagi_graph(), html.Br()]),
        html.Div([html.Div(id='effetti_contagi_graph'), html.Div(id='effetti_decessi_graph')], className='container-1'),
        # text effect
        html.Div(html.Center([html.Div([html.Br(), "Contagi ", html.B("ultimo mese"), " in Italia: ", html.Mark([html.B("%s" %("+" if int(percent_mese) > 100 else "-")+str(float(percent_mese))+'%')], style={'background-color': '#F5C05F'})], className='container-2'),
                              html.Div([html.Br(), "Decessi ", html.B("ultimo mese"), " in Italia: ", html.Mark([html.B("%s" %("+" if int(percent_mese_death) > 100 else "-")+str(float(percent_mese_death))+'%')], style={'background-color': '#F5C05F'})], className='container-2'),
                              html.Div([html.Br(), html.Br(), html.Br(), html.H4('Quanto le vaccinazioni stanno contribuendo veramente alla riduzione dei contagi?'), html.I("I dati sono calcolati sulla percentuale di popolazione vaccinata e sull'incidenza dei contagi, (nell'ultima settimana) per 100.000 abitanti", style={'font-size': '14px'}), html.Br(), html.Br()], className='container-1')], className='container-1')),
        # text riduzione
        html.Div([dropdown_riduzione_graph()]),
        html.Div([html.Div(id='riduzione_graph')], className='container-1'),
    ])

app.layout = layout

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
