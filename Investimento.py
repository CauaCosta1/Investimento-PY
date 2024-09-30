import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Função para pegar os dados do Yahoo Finance
@st.cache_data
def pegar_dados_yahoo(tickers):
    dados = {}
    for ticker in tickers:
        try:
            dados[ticker] = yf.download(ticker, period="1y")  # Pegando 1 ano de dados
            if dados[ticker].empty:
                st.warning(f"Nenhum dado encontrado para {ticker} no Yahoo Finance.")
        except Exception as e:
            st.error(f"Erro ao baixar dados para {ticker} no Yahoo Finance: {e}")
    return dados

# Função para calcular métricas
def calcular_metricas(df):
    # Calcular Retorno Diário e Retorno Acumulado
    df['Retorno_Diario'] = df['Adj Close'].pct_change()
    df['Retorno_Acumulado'] = (1 + df['Retorno_Diario']).cumprod() - 1

    # Calcular médias móveis
    df['Media_Movel_50'] = df['Adj Close'].rolling(window=50).mean()
    df['Media_Movel_200'] = df['Adj Close'].rolling(window=200).mean()

    # Calcular volatilidade anualizada (30 dias)
    df['Volatilidade'] = df['Retorno_Diario'].rolling(window=30).std() * np.sqrt(252)

    return df

# Função para determinar a tendência de crescimento e os percentuais de crescimento/queda
def analisar_tendencia(df):
    if df['Media_Movel_50'].iloc[-1] > df['Media_Movel_200'].iloc[-1]:
        crescimento_percentual = (df['Media_Movel_50'].iloc[-1] / df['Media_Movel_200'].iloc[-1] - 1) * 100
        return "Crescimento", "⬆️", crescimento_percentual
    else:
        queda_percentual = (1 - df['Media_Movel_50'].iloc[-1] / df['Media_Movel_200'].iloc[-1]) * 100
        return "Queda", "⬇️", queda_percentual

# Função para calcular o crescimento projetado
def calcular_projecao_crescimento(df):
    # Taxa de crescimento baseada na inclinação da média móvel de 50 dias
    momento_crescimento = (df['Media_Movel_50'].iloc[-1] - df['Media_Movel_50'].iloc[-5]) / 5
    
    # Ajustando pelo risco (volatilidade)
    crescimento_projetado = momento_crescimento * (1 - df['Volatilidade'].iloc[-1])
    
    # Garantir que a projeção não seja negativa
    if crescimento_projetado < 0:
        crescimento_projetado = 0

    return crescimento_projetado * 100  # Retorna em percentual

# Função para exibir gráficos interativos com explicações
def exibir_graficos(ticker, df):
    st.subheader(f"Análise de {ticker}")

    # Gráfico de Preço Ajustado com Médias Móveis e explicações
    fig = go.Figure()

    # Preço Ajustado
    fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], mode='lines', name='Preço Ajustado',
                             hovertemplate='O preço ajustado é o preço do ativo após ajustes, como dividendos e splits.',
                             line=dict(color='blue')))

    # Média Móvel de 50 dias
    fig.add_trace(go.Scatter(x=df.index, y=df['Media_Movel_50'], mode='lines', name='Média Móvel 50 dias',
                             hovertemplate='A média móvel de 50 dias mostra a média dos preços ajustados dos últimos 50 dias. É usada para indicar tendências de curto prazo.',
                             line=dict(color='orange')))

    # Média Móvel de 200 dias
    fig.add_trace(go.Scatter(x=df.index, y=df['Media_Movel_200'], mode='lines', name='Média Móvel 200 dias',
                             hovertemplate='A média móvel de 200 dias mostra a média dos preços ajustados dos últimos 200 dias. É usada para indicar a tendência de longo prazo.',
                             line=dict(color='green')))

    fig.update_layout(title=f'Preço Ajustado e Médias Móveis - {ticker}', xaxis_title='Data', yaxis_title='Preço Ajustado')
    st.plotly_chart(fig)

    # Gráfico de Retorno Acumulado
    fig_retorno = go.Figure()
    fig_retorno.add_trace(go.Scatter(x=df.index, y=df['Retorno_Acumulado'], mode='lines', name='Retorno Acumulado',
                                     hovertemplate='O retorno acumulado mostra o ganho ou perda percentual desde o início do período.',
                                     line=dict(color='purple')))
    fig_retorno.update_layout(title=f'Retorno Acumulado - {ticker}', xaxis_title='Data', yaxis_title='Retorno Acumulado')
    st.plotly_chart(fig_retorno)

    # Gráfico de Volatilidade
    fig_volatilidade = go.Figure()
    fig_volatilidade.add_trace(go.Scatter(x=df.index, y=df['Volatilidade'], mode='lines', name='Volatilidade (Anualizada)',
                                          hovertemplate='A volatilidade mede o risco, ou a variação nos preços, anualizada para facilitar comparações.',
                                          line=dict(color='red')))
    fig_volatilidade.update_layout(title=f'Volatilidade (Anualizada) - {ticker}', xaxis_title='Data', yaxis_title='Volatilidade')
    st.plotly_chart(fig_volatilidade)

# Função para recomendar a compra ou não e exibir a projeção de crescimento a longo prazo
def recomendar_compra_e_projecao(ticker, df):
    # Exibir o preço mais recente
    ultimo_preco = df['Adj Close'].iloc[-1]
    st.write(f"**Preço mais recente de {ticker}:** ${ultimo_preco:.2f}")
    
    # Determina a tendência e exibe a recomendação
    tendencia, seta, percentual = analisar_tendencia(df)
    
    if tendencia == "Crescimento":
        st.success(f"{seta} **Recomendação:** {ticker} está em **Crescimento** ({percentual:.2f}% de crescimento). Bom para compra a longo prazo.")
    else:
        st.error(f"{seta} **Recomendação:** {ticker} está em **Queda** ({percentual:.2f}% de queda). Melhor evitar no longo prazo.")

    # Cálculo de projeção de crescimento
    crescimento_projetado = calcular_projecao_crescimento(df)
    st.write(f"**Crescimento projetado para o longo prazo**: {crescimento_projetado:.2f}%")

# Função principal para montar a interface no Streamlit
def main():
    st.set_page_config(page_title="Análise de Investimentos", layout="wide")

    st.title("Análise de Investimentos com Projeção de Crescimento")
    st.markdown("""
    Esta aplicação fornece uma análise de crescimento ou queda de ações e criptomoedas, com base em dados do Yahoo Finance. 
    Agora, também calculamos uma **projeção de crescimento a longo prazo** baseada no momento atual de crescimento e volatilidade.
    """)

    # Lista de empresas para escolha
    tickers_lista = [
        'SANB11', 'PETR4', 'IFCM3', 'OSXB3', 'MGHT11', 'BRKM6', 'SNSY5',
        'NIO', 'SQ', 'PLTR', 'DKNG', 'ROKU', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'JNJ'
    ]
    
    # Caixa de seleção para escolher os ativos pré-definidos
    tickers_acoes = st.sidebar.multiselect("Selecione os códigos de ações", tickers_lista, default=tickers_lista)

    # Campo de pesquisa para qualquer ação ou criptomoeda
    ticker_personalizado = st.sidebar.text_input("Digite o código de qualquer ação ou criptomoeda", "")
    
    if ticker_personalizado:
        tickers_acoes.append(ticker_personalizado.upper())

    # Pegar os dados das ações ou criptomoedas
    if st.sidebar.button("Analisar"):
        st.title("Análise das Ações Selecionadas")

        # Pega os dados do Yahoo Finance
        dados_yahoo = pegar_dados_yahoo(tickers_acoes)

        for ticker in tickers_acoes:
            df = dados_yahoo.get(ticker, pd.DataFrame())
            
            if df.empty:
                st.warning(f"Não foi possível encontrar dados para {ticker}.")
                continue

            # Calcula métricas e exibe gráficos
            df = calcular_metricas(df)

            # Exibe os gráficos com explicações
            exibir_graficos(ticker, df)

            # Recomendação de compra e projeção de crescimento a longo prazo
            recomendar_compra_e_projecao(ticker, df)

# Rodando a aplicação no Streamlit
if __name__ == '__main__':
    main()