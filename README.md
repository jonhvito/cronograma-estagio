# Sistema de Cronograma de Estágio

Sistema web para gerenciamento e planejamento de horas de estágio, desenvolvido com Streamlit.

## 📋 Descrição

Aplicação que calcula automaticamente o cronograma de estágio com base em uma carga horária semanal pré-definida, permitindo o gerenciamento de feriados, dias sem expediente e observações personalizadas. Inclui visualização detalhada em formato de tabela e calendário mensal.

## 🚀 Funcionalidades

- **Cálculo Automático**: Cronograma calculado automaticamente até completar a carga horária total
- **Gerenciamento de Feriados**: Adicione e remova feriados e dias sem expediente
- **Observações Personalizadas**: Adicione anotações para datas específicas
- **Visualização em Calendário**: Visualize o cronograma em formato de calendário mensal com código de cores
- **Visualização em Tabela**: Cronograma detalhado com horas diárias e acumuladas
- **Exportação**: Exporte o cronograma completo em formato CSV
- **Temas**: Compatível com modo claro e escuro

## 🛠️ Tecnologias

- Python 3.8+
- Streamlit
- Pandas

## 📦 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd estagio
```

2. Crie um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ▶️ Execução

Execute o aplicativo com o comando:

```bash
streamlit run app.py
```

O aplicativo será aberto automaticamente no navegador em `http://localhost:8501`

## ⚙️ Configuração

As configurações padrão podem ser ajustadas no início do arquivo `app.py`:

- `TOTAL_HOURS`: Carga horária total do estágio (padrão: 240 horas)
- `START_DATE`: Data de início do estágio
- `HOURS_PER_WEEKDAY`: Distribuição de horas por dia da semana

## 📊 Estrutura de Dados

O sistema utiliza dois arquivos CSV para persistência de dados:

- `feriados.csv`: Armazena feriados e dias sem expediente
- `observacoes.csv`: Armazena observações personalizadas por data

## 📄 Licença

Este projeto é de uso educacional e profissional.
