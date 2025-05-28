import streamlit as st
import requests
import pandas as pd
import time


@st.cache_data
def converte_csv(df):
    return df.to_csv(index = False).encode('utf-8')

def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso', icon = '✅')
    time.sleep(5)
    sucesso.empty()

st.set_page_config(layout='wide') # Define o layout da página para largo

st.title('Dados Brutos Interativos 📊')

# Carregamento dos dados com tratamento de erro básico
try:
    url = 'https://labdados.com/produtos'
    response = requests.get(url)
    response.raise_for_status()  # Verifica se houve erro na requisição (4xx ou 5xx)
    dados_json = response.json()
    dados = pd.DataFrame.from_dict(dados_json)
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')
except requests.exceptions.RequestException as e:
    st.error(f"Erro ao buscar dados da URL: {e}")
    st.stop()
except (ValueError, KeyError) as e: # Erros comuns ao processar JSON ou criar DataFrame
    st.error(f"Erro ao processar os dados recebidos: {e}")
    st.stop()

# Se o DataFrame estiver vazio após o carregamento, interrompe.
if dados.empty:
    st.warning("Nenhum dado foi carregado. Verifique a fonte de dados.")
    st.stop()

# --- Seletor de Colunas Visíveis ---
st.subheader('Seleção de Colunas para Visualização')
with st.expander('Escolha as colunas'):
    # Garante que 'colunas_disponiveis' não esteja vazio e seleciona todas por padrão
    colunas_disponiveis = list(dados.columns)
    if not colunas_disponiveis:
        st.warning("Não há colunas disponíveis nos dados carregados.")
        st.stop()
    colunas_selecionadas = st.multiselect('Selecione as colunas para exibir',
                                          options=colunas_disponiveis,
                                          default=colunas_disponiveis)

# --- Filtros na Barra Lateral ---
st.sidebar.title('Filtros Aplicáveis 🔎')

with st.sidebar.expander('Produto'):
    produtos_unicos = dados['Produto'].unique()
    produtos_filtrar = st.multiselect('Selecione os produtos',
                                      options=produtos_unicos,
                                      default=produtos_unicos)

with st.sidebar.expander('Categoria do Produto'):
    categorias_unicas = dados['Categoria do Produto'].unique()
    categoria_filtrar = st.multiselect('Selecione as categorias',
                                       options=categorias_unicas,
                                       default=categorias_unicas)

with st.sidebar.expander('Preço do Produto'):
    # Usar min/max dos dados para o slider se apropriado, ou manter fixo
    min_preco, max_preco = int(dados['Preço'].min()), int(dados['Preço'].max())
    preco_filtrar = st.slider('Selecione a faixa de preço',
                              min_value=min_preco,
                              max_value=max_preco,
                              value=(min_preco, max_preco))

with st.sidebar.expander('Frete da Venda'):
    min_frete, max_frete = int(dados['Frete'].min()), int(dados['Frete'].max())
    frete_filtrar = st.slider('Selecione a faixa de frete',
                              min_value=min_frete,
                              max_value=max_frete,
                              value=(min_frete, max_frete))

with st.sidebar.expander('Data da Compra'):
    # st.date_input retorna uma tupla de datetime.date
    data_compra_filtrar = st.date_input('Selecione o período',
                                        value=(dados['Data da Compra'].min().date(), dados['Data da Compra'].max().date()),
                                        min_value=dados['Data da Compra'].min().date(),
                                        max_value=dados['Data da Compra'].max().date())

with st.sidebar.expander('Vendedor'):
    vendedores_unicos = dados['Vendedor'].unique()
    vendedores_filtrar = st.multiselect('Selecione os vendedores',
                                        options=vendedores_unicos,
                                        default=vendedores_unicos)

with st.sidebar.expander('Local da Compra'):
    locais_unicos = dados['Local da compra'].unique()
    local_compra_filtrar = st.multiselect('Selecione o local da compra',
                                          options=locais_unicos,
                                          default=locais_unicos)

with st.sidebar.expander('Avaliação da Compra'):
    avaliacao_filtrar = st.slider('Selecione a faixa de avaliação',
                                  min_value=1,
                                  max_value=5,
                                  value=(1, 5))

with st.sidebar.expander('Tipo de Pagamento'):
    tipos_pagamento_unicos = dados['Tipo de pagamento'].unique()
    tipo_pagamento_filtrar = st.multiselect('Selecione o tipo de pagamento',
                                            options=tipos_pagamento_unicos,
                                            default=tipos_pagamento_unicos)

with st.sidebar.expander('Quantidade de Parcelas'):
    min_parcelas, max_parcelas = int(dados['Quantidade de parcelas'].min()), int(dados['Quantidade de parcelas'].max())
    qtd_parcelas_filtrar = st.slider('Selecione a quantidade de parcelas',
                                     min_value=min_parcelas,
                                     max_value=max_parcelas,
                                     value=(min_parcelas, max_parcelas))

# --- Aplicação dos Filtros ---
dados_filtrados = dados.copy() # Começa com uma cópia para não alterar o original

# Multiselect filters: Só aplica se a lista de seleção não for idêntica a todas as opções únicas
# (ou seja, se o usuário de fato fez uma seleção restritiva ou limpou o filtro).
# Melhor: se a lista de seleção for diferente de todas as opções, filtre. Ou sempre filtre.
# Para multiselect, o default é mostrar tudo. Se o usuário desmarcar algo, a lista muda.
# Se a lista de selecionados não estiver vazia, aplica o filtro.
# Se o usuário desmarcar TODOS os itens de um multiselect que tinha todos por padrão,
# a lista de selecionados fica vazia. Nesse caso, nenhum item daquela categoria deve aparecer.

if produtos_filtrar:
    dados_filtrados = dados_filtrados[dados_filtrados['Produto'].isin(produtos_filtrar)]
else: # Se a lista de produtos a filtrar for vazia, mostra um DataFrame vazio para essa condição
    dados_filtrados = dados_filtrados[dados_filtrados['Produto'].isin([])]


if categoria_filtrar:
    dados_filtrados = dados_filtrados[dados_filtrados['Categoria do Produto'].isin(categoria_filtrar)]
else:
    dados_filtrados = dados_filtrados[dados_filtrados['Categoria do Produto'].isin([])]


# Slider filters (sempre aplicados com base no range)
dados_filtrados = dados_filtrados[dados_filtrados['Preço'].between(preco_filtrar[0], preco_filtrar[1])]
dados_filtrados = dados_filtrados[dados_filtrados['Frete'].between(frete_filtrar[0], frete_filtrar[1])]

# Date filter
if len(data_compra_filtrar) == 2: # Garante que temos um início e fim de data
    start_date = pd.to_datetime(data_compra_filtrar[0])
    end_date = pd.to_datetime(data_compra_filtrar[1])
    dados_filtrados = dados_filtrados[dados_filtrados['Data da Compra'].between(start_date, end_date)]

if vendedores_filtrar:
    dados_filtrados = dados_filtrados[dados_filtrados['Vendedor'].isin(vendedores_filtrar)]
else:
    dados_filtrados = dados_filtrados[dados_filtrados['Vendedor'].isin([])]

if local_compra_filtrar:
    dados_filtrados = dados_filtrados[dados_filtrados['Local da compra'].isin(local_compra_filtrar)]
else:
    dados_filtrados = dados_filtrados[dados_filtrados['Local da compra'].isin([])]

dados_filtrados = dados_filtrados[dados_filtrados['Avaliação da compra'].between(avaliacao_filtrar[0], avaliacao_filtrar[1])]

if tipo_pagamento_filtrar:
    dados_filtrados = dados_filtrados[dados_filtrados['Tipo de pagamento'].isin(tipo_pagamento_filtrar)]
else:
    dados_filtrados = dados_filtrados[dados_filtrados['Tipo de pagamento'].isin([])]

dados_filtrados = dados_filtrados[dados_filtrados['Quantidade de parcelas'].between(qtd_parcelas_filtrar[0], qtd_parcelas_filtrar[1])]


# --- Exibição do DataFrame ---
st.subheader('Tabela de Dados Filtrados')
if not colunas_selecionadas: # Se nenhuma coluna for selecionada para exibição
    st.warning("Nenhuma coluna selecionada para exibição.")
elif dados_filtrados.empty:
    st.warning("Nenhum dado corresponde aos filtros aplicados.")
else:
    st.dataframe(dados_filtrados[colunas_selecionadas])

st.write(f"Mostrando {dados_filtrados.shape[0]} linhas e {len(colunas_selecionadas)} colunas.")


st.markdown('Escreva um nome para o arquivo')
coluna1, coluna2 = st.columns(2)
with coluna1:
    nome_arquivo = st.text_input('', label_visibility = 'collapsed', value = 'dados')
    nome_arquivo += '.csv'
with coluna2:
    st.download_button('Fazer o download da tabela em csv', data= converte_csv(dados_filtrados), file_name = nome_arquivo, mime = 'text/csv', on_click = mensagem_sucesso)


















































