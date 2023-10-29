import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pandas_datareader.data as pdr
import yfinance as yf
from datetime import datetime, timedelta, date
from workalendar.america import Brazil


yf.pdr_override()
st.set_page_config(
    page_title='Dashboard',
    layout='wide',
    page_icon=':bar_chart:',
    initial_sidebar_state='collapsed'
)

cal = Brazil()

CSV_FILE = 'registro.csv'
DATA_ATUAL = datetime.today()
DATA_INICIAL = DATA_ATUAL - timedelta(days=5 * 365)
DATA_ANTERIOR = date.today() - timedelta(days=1)


@st.cache_data
def carregar_dados(dados):
    try:
        dados = pd.read_csv(dados)
    except FileNotFoundError:
        dados = pd.DataFrame({
            'Data': [],
            'Operacao': [],
            'Ticker': [],
            'Classe': [],
            'Quantidade': [],
            'Preco': [],
            'Valor Total': []
        })
    return dados


def mostrar_registros():
    existing_df = carregar_dados(CSV_FILE)
    st.dataframe(existing_df)

    for index, row in existing_df.iterrows():
        if st.button(f"Remover {index}", key=f"remover_{index}"):
            existing_df = existing_df.drop(index)
            existing_df.to_csv(CSV_FILE, index=False)


def menu_sidebar():
    st.title("Formulário de Registro")
    data = st.date_input("Data", format='DD/MM/YYYY')
    operacao = st.selectbox("Operacao", ["COMPRA", "VENDA"])
    ticker = st.text_input("Ticker").upper()
    classe = st.selectbox("Classe", ['AÇÃO', 'FII', 'CDB|RDB'])
    quant = st.number_input("Quantidade", min_value=1)
    preco = st.number_input("Preco")
    valor_total = quant * preco

    if st.button("Registrar"):
        df = pd.DataFrame({
            'Data': [data],
            'Operacao': [operacao],
            'Ticker': [ticker+'.SA'],
            'Classe': [classe],
            'Quantidade': [quant],
            'Preco': [preco],
            'Valor Total': [valor_total]
        })
        try:
            existing_df = pd.read_csv(CSV_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
        except FileNotFoundError:
            pass

        df.to_csv(CSV_FILE, index=False)
        st.success("Registro salvo com sucesso!")

    if st.checkbox("Mostrar Registros"):
        mostrar_registros()


def obter_preco_acao(acao):
    try:       
        acao_info = pdr.get_data_yahoo(acao, DATA_INICIAL, DATA_ATUAL)
        preco_atual = acao_info['Adj Close'].iloc[-1]
        
        return preco_atual
    except Exception as e:
        st.error(e)
        return None


def obter_dados_acoes(dados, data_inicial=None, data_final=None):
    acoes = dados['Ticker'].unique().tolist()

    dados_acoes = {}

    for acao in acoes:
        quantidade = dados[dados['Ticker'] == acao]['Quantidade'].sum()
        # Verifica se o preço atual da ação já foi calculado
        try:
            if acao not in dados_acoes:
                # Calcula o preço atual da ação
                preco_atual = obter_preco_acao(acao)
                
                if preco_atual is not None:
                    dados_acoes[acao] = {
                        'Data': data_final.strftime('%d-%m-%Y'),
                        'Quantidade': quantidade,
                        'Preco Atual': preco_atual,
                        'Preco Total': quantidade * preco_atual
                    }
                else:
                    dados_acoes[acao] = {
                        'Data': data_final.strftime('%d-%m-%Y'),
                        'Quantidade': quantidade,
                        'Preco Atual': "Erro na obtenção de preço",
                        'Preco Total': "Erro na obtenção de preço"
                    }
        except Exception as e:
            if 'No price data found':
                acao_info = pdr.get_data_yahoo(acao, DATA_ANTERIOR, DATA_ANTERIOR)
                preco_atual = acao_info['Adj Close'].iloc[-1]
                dados_acoes[acao] = {
                    'Data': DATA_ANTERIOR.strftime('%d-%m-%Y'),
                    'Quantidade': quantidade,
                    'Preco Atual': preco_atual,
                    'Preco Total': quantidade * preco_atual
                }
            else:
                st.write(f"Erro ao obter informações para {acao}: {e}")

    return pd.DataFrame.from_dict(dados_acoes, orient='index', columns=['Data', 'Quantidade', 'Preco Atual', 'Preco Total'])


def mostrar_grafico(dados_ticker, dados_qtd):
    st.header(":pushpin: :green[INVESTIMENTOS]")
    fig = go.Figure(data=go.Pie(labels=dados_ticker, values=dados_qtd, hole=0.5))
    fig.update_layout(
        legend=dict(x=0.75, y=0.5, traceorder="normal", font=dict(family="sans-serif", size=13, color="black")),
        margin=dict(t=80)
    )
    return st.plotly_chart(fig)


if __name__ == '__main__':

    dados_csv = carregar_dados(CSV_FILE)
    
    with st.sidebar:
      menu_sidebar()

    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        mostrar_grafico(dados_csv['Ticker'], dados_csv['Quantidade'])

    with col2:
        st.header(":chart_with_upwards_trend: MEUS :blue[INVESTIMENTOS]")
        st.markdown('#')
        st.dataframe(dados_csv, use_container_width=True)
#.st-emotion-cache-5rimss > p
    st.divider()
    st.markdown(""" <style> #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi4 > div:nth-child(1) > div > div:nth-child(5) > div.st-emotion-cache-j5r0tf.e1f1d6gn1 > div:nth-child(1) > div { 
    color: black; background-color:white;} 
    </style> """, unsafe_allow_html=True)
    col3, col4, col5 = st.columns([0.3, 0.5, 0.2])

    with st.spinner('CARREGANDO...'):
        
        with col3:
            
            novo_df = obter_dados_acoes(dados_csv, DATA_ATUAL, DATA_ATUAL)
            st.header(':moneybag: :orange[VALOR ATUAL]')
            st.write(novo_df)

        with col4:
            acao = dados_csv['Ticker'].unique().tolist()
            dados_ac = pdr.get_data_yahoo(acao, DATA_INICIAL, DATA_ATUAL)['Adj Close']
            normalizado = dados_ac / dados_ac.iloc[0]
            st.header(':bar_chart: :blue[RENDIMENTO PERÍODO 5 ANOS]')
            st.line_chart(normalizado)

        with col5:
                vendas = dados_csv[dados_csv['Operacao'] == "VENDA"].sum()['Valor Total']
            
                st.header(':flag-br: :green[GANHO/PERCA]')
                st.metric(label=":white_check_mark: :green[TOTAL INVESTIDO]", value=f"R${dados_csv['Valor Total'].sum() - vendas:.2f}")
                st.metric(label=":white_check_mark: :green[VALOR ATUAL]", value=f"R${novo_df['Preco Total'].sum() - vendas:.2f}")             
                
                retorno = dados_csv['Valor Total'].sum() - novo_df['Preco Total'].sum()
                
                if retorno < 0:
                    st.metric(label=":white_check_mark: :green[RETORNO DIA]", value=f"R$-{retorno:.2f}")
                else:
                    st.metric(label=":white_check_mark: :green[RETORNO DIA]", value=f"R$-{retorno:.2f}")
