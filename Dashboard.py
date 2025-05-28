import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide',
                   initial_sidebar_state='auto')

def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'.strip()
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'.strip()

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

# Carregamento e tratamento inicial dos dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil','Centro-Oeste','Nordeste','Norte','Sudeste','Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região',regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano',2020,2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}

try:
    response = requests.get(url, params= query_string)
    response.raise_for_status()  # Verifica se houve erro na requisição HTTP
    dados = pd.DataFrame.from_dict(response.json())
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')
except requests.exceptions.RequestException as e:
    st.error(f"Erro ao buscar dados da URL: {e}")
    st.stop() # Interrompe a execução se não conseguir carregar os dados
except ValueError as e:
    st.error(f"Erro ao processar os dados JSON ou converter datas: {e}")
    st.stop()

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# --- Tabelas de Agregação ---

## Tabelas de Receita
receita_estados_sum = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados_sum, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

## Tabelas de Quantidade de Vendas
# Agrupamento e renomeação da coluna de contagem para 'Quantidade'
vendas_estados_count = dados.groupby('Local da compra')['Preço'].count().reset_index(name='Quantidade')
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estados_count, on='Local da compra').sort_values('Quantidade', ascending=False)

vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count().reset_index(name='Quantidade')
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mês'] = vendas_mensal['Data da Compra'].dt.month_name() # Corrigido de 'Mes' para 'Mês'

vendas_categorias = dados.groupby('Categoria do Produto')['Preço'].count().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False)
# Definindo 'Categoria do Produto' como índice para o gráfico de barras se comportar como esperado
vendas_categorias = vendas_categorias.set_index('Categoria do Produto')


## Tabelas Vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))
# 'sum' é a receita, 'count' é a quantidade de vendas


# --- Gráficos ---

## Gráficos de Receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mês',
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal['Preço'].max() if not receita_mensal.empty else 100), # Corrigido range_y
                             color='Ano',
                             line_dash='Ano',
                             title='Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x='Local da compra',
                             y='Preço',
                             text_auto=True,
                             title='Top 5 Estados por Receita')
fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                y='Preço', # Explicitamente define y
                                text_auto=True,
                                title='Receita por Categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')


## Gráficos de Quantidade de Vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados,
                                 lat='lat',
                                 lon='lon',
                                 scope='south america',
                                 template='seaborn',
                                 size='Quantidade', # Corrigido de 'Preço' para 'Quantidade'
                                 hover_name='Local da compra',
                                 hover_data={'lat': False, 'lon': False},
                                 title='Quantidade de Vendas por Estado')

fig_vendas_mensal = px.line(vendas_mensal,
                            x='Mês', # Corrigido de 'Mes'
                            y='Quantidade', # Corrigido de 'Preço' para 'Quantidade'
                            markers=True,
                            range_y=(0, vendas_mensal['Quantidade'].max() if not vendas_mensal.empty else 100), # Corrigido range_y e nome da coluna
                            color='Ano',
                            line_dash='Ano',
                            title='Quantidade de Vendas Mensal')
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de Vendas')

fig_vendas_estados = px.bar(vendas_estados.head(),
                            x='Local da compra',
                            y='Quantidade', # Corrigido de 'Preço' para 'Quantidade'
                            text_auto=True,
                            title='Top 5 Estados por Quantidade de Vendas')
fig_vendas_estados.update_layout(yaxis_title='Quantidade de Vendas')

fig_vendas_categorias = px.bar(vendas_categorias,
                               y='Quantidade', # Corrigido de 'Preço' (implícito) para 'Quantidade'
                               text_auto=True,
                               title='Quantidade de Vendas por Categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de Vendas')


# --- Visualização no Streamlit ---
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita Total', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Total de Vendas (Unidades)', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2: # Conteúdo da antiga aba4 movido para cá e corrigido
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        # Métrica de receita total pode ser repetida ou removida se parecer redundante com a aba1
        st.metric('Receita Total (Contexto Vendas)', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Total de Vendas (Unidades)', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', min_value=2, max_value=10, value=5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita Total (Contexto Vendedores)', formata_numero(dados['Preço'].sum(), 'R$'))
        
        # Gráfico de Receita por Vendedores
        top_receita_vendedores = vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores)
        fig_receita_vendedores = px.bar(top_receita_vendedores,
                                        x='sum',
                                        y=top_receita_vendedores.index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} Vendedores por Receita')
        fig_receita_vendedores.update_layout(xaxis_title='Receita', yaxis_title='Vendedores') # Corrigido xaxis_title
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)

    with coluna2:
        st.metric('Total de Vendas (Unidades)', formata_numero(dados.shape[0]))

        # Gráfico de Quantidade de Vendas por Vendedores
        top_vendas_vendedores = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores)
        fig_vendas_vendedores = px.bar(top_vendas_vendedores,
                                       x='count',
                                       y=top_vendas_vendedores.index,
                                       text_auto=True,
                                       title=f'Top {qtd_vendedores} Vendedores por Quantidade de Vendas')
        fig_vendas_vendedores.update_layout(xaxis_title='Quantidade de Vendas', yaxis_title='Vendedores') # Corrigido xaxis_title
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)
















































