import dash
from dash import dcc, html

# 🧱 Inicializa o aplicativo Dash
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,  # permite usar callbacks com páginas e componentes que ainda não estão renderizados
    title="Dashboard Imobiliário"
)

server = app.server  # Necessário para deploy (Heroku, Render, etc.)

# 🧹 ESTRUTURA BASE (ainda sem dados):
# Esse layout inicial serve como esqueleto do dashboard.
# Ele será preenchido quando os dados tratados estiverem prontos.

app.layout = html.Div([
    html.H1("🏡 Dashboard de Preços Imobiliários", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Escolha o tipo de dado:"),
        dcc.Dropdown(
            id='tipo_dado',
            options=[
                {'label': 'Venda', 'value': 'venda'},
                {'label': 'Locação', 'value': 'locacao'}
            ],
            value='venda',
            clearable=False,
            style={'width': '50%'}
        ),
    ], style={'padding': '20px'}),

    dcc.Graph(
        id='grafico-linha',
        figure={}  # será preenchido com os dados futuramente
    ),

    html.Div("⚠️ Aguardando dados tratados para exibir os gráficos.", style={'textAlign': 'center', 'color': 'gray'})
])

# 🚀 Executa o servidor local
if __name__ == '__main__':
    app.run_server(debug=True)
