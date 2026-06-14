Pré-requisitos: Ter o Python 3.9+ instalado.
Criar e ativar um ambiente virtual (Opcional, mas recomendado):
bash
python -m venv venv
# No Windows: venv\Scripts\activate
# No Linux/Mac: source venv/bin/activate

Instalar dependências:
bash
pip install streamlit pandas altair

Rodar a aplicação:
bash
streamlit run app.py

(O banco de dados financeiro.db será gerado automaticamente na primeira execução).
