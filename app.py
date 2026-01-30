import streamlit as st
import pandas as pd
import pdfplumber
import re
import io

# Configuração da página
st.set_page_config(page_title="Conversor Inteligente", page_icon="🧠")

# Estilo do botão
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745; color: white; border-radius: 5px; border: none; padding: 5px 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Robô com Memória Contábil")

# --- BANCO DE DADOS DE MEMÓRIA ---
# Se for a primeira vez, cria a memória vazia
if 'memoria_contas' not in st.session_state:
    st.session_state.memoria_contas = {
        "PIX RECEBIDO": "7001", # Exemplos que você pode mudar
        "TARIFA BANCARIA": "8005",
        "PAGAMENTO BOLETO": "1002"
    }

with st.expander("📖 Ver/Editar Memória de Contas"):
    st.write("Aqui o robô guarda o que aprendeu. Se o Histórico for igual, ele repete a Conta.")
    st.json(st.session_state.memoria_contas)

arquivo_pdf = st.file_uploader("Suba o PDF do extrato:", type="pdf")

if arquivo_pdf is not None:
    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        data = tem_data.group(1)
                        valor_str = tem_valor.group(1)
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                        hist = linha.replace(data, '').replace(valor_str, '').strip()[:50]
                        
                        # LOGICA DE MEMÓRIA:
                        # Se o histórico já existe na memória, ele usa. Se não, deixa vazio.
                        conta_sugerida = st.session_state.memoria_contas.get(hist, "")
                        
                        credito = abs(v_num) if v_num < 0 else 0
                        debito = v_num if v_num > 0 else 0
                        
                        transacoes.append({
                            "Data": data,
                            "Histórico": hist,
                            "Conta Contábil": conta_sugerida,
                            "Documento": "",
                            "Débito": debito,
                            "Crédito": credito
                        })

    if transacoes:
        df = pd.DataFrame(transacoes)
        
        st.write("### Ajuste as Contas na Tabela abaixo:")
        # Tabela editável: você pode preencher a conta direto no site!
        df_editado = st.data_editor(df, num_rows="dynamic")

        # BOTÃO PARA APRENDER:
        if st.button("💾 Ensinar ao Robô (Salvar Contas)"):
            for _, linha in df_editado.iterrows():
                if linha["Conta Contábil"]:
                    st.session_state.memoria_contas[linha["Histórico"]] = linha["Conta Contábil"]
            st.success("O robô aprendeu! Na próxima vez, ele preencherá essas contas sozinho.")

        # Gerar Excel com o que foi editado
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_editado.to_excel(writer, index=False)
        
        st.download_button("📥 Baixar Planilha para Sistema", output.getvalue(), "extrato_contabil.xlsx")
