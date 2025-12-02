import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import calendar
import os

# --- Configurações Iniciais ---
TOTAL_HOURS = 240
START_DATE = date(2025, 11, 14)
HOURS_PER_WEEKDAY = {
    0: 4,  # Segunda-feira
    1: 0,  # Terça-feira
    2: 4,  # Quarta-feira
    3: 8,  # Quinta-feira
    4: 4,  # Sexta-feira
    5: 0,  # Sábado
    6: 0   # Domingo
}
HOLIDAYS_CSV = 'feriados.csv'
OBSERVATIONS_CSV = 'observacoes.csv'

# --- Funções de Lógica de Negócio ---

def get_weekday_name(weekday_index):
    """Converte o índice do dia da semana (0=Seg, 6=Dom) para o nome em português."""
    names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    return names[weekday_index]

def generate_calendar_view(df_schedule, start_date, end_date):
    """
    Gera uma visualização em formato de calendário mensal.
    Retorna um dicionário onde a chave é o mês/ano e o valor é HTML do calendário.
    """
    if end_date is None:
        return {}
    
    # Cria um dicionário de dados por data para busca rápida
    schedule_dict = {}
    for _, row in df_schedule.iterrows():
        schedule_dict[row['Data']] = {
            'hours': row['Horas no dia'],
            'accumulated': row['Horas acumuladas'],
            'obs': row['Observação']
        }
    
    calendars_html = {}
    current = start_date.replace(day=1)
    end_month = end_date.replace(day=1)
    
    while current <= end_month:
        year = current.year
        month = current.month
        
        # Nome do mês em português
        month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        month_name = month_names[month - 1]
        
        # Gera o calendário do mês
        cal = calendar.monthcalendar(year, month)
        
        # Constrói HTML do calendário
        html = f"<div style='margin-bottom: 2rem;'>"
        html += f"<h4 style='text-align: center; margin-bottom: 1rem;'>{month_name} {year}</h4>"
        html += "<table style='width: 100%; border-collapse: collapse; text-align: center;'>"
        
        # Cabeçalho dos dias da semana
        html += "<tr>"
        for day in ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']:
            html += f"<th style='padding: 8px; background-color: rgba(128, 128, 128, 0.2); border: 1px solid rgba(128, 128, 128, 0.3);'>{day}</th>"
        html += "</tr>"
        
        # Linhas do calendário
        for week in cal:
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td style='padding: 8px; border: 1px solid rgba(128, 128, 128, 0.3); opacity: 0.3;'></td>"
                else:
                    current_date = date(year, month, day)
                    cell_style = "padding: 8px; border: 1px solid rgba(128, 128, 128, 0.3);"
                    
                    # Verifica se a data está no cronograma
                    if current_date in schedule_dict:
                        data = schedule_dict[current_date]
                        hours = data['hours']
                        
                        # Define cor baseada nas horas (cores compatíveis com dark/light mode)
                        if hours == 0:
                            bg_color = "rgba(128, 128, 128, 0.15)"  # Cinza para dias sem horas
                            text_color = ""
                        elif hours <= 4:
                            bg_color = "rgba(33, 150, 243, 0.3)"  # Azul
                            text_color = ""
                        else:
                            bg_color = "rgba(76, 175, 80, 0.3)"  # Verde
                            text_color = ""
                        
                        cell_style += f" background-color: {bg_color};"
                        if text_color:
                            cell_style += f" color: {text_color};"
                        
                        # Tooltip com informações
                        title = f"Horas: {hours}h"
                        has_detailed_obs = False
                        if data['obs']:
                            # Limita o tamanho da observação no tooltip
                            obs_preview = data['obs'][:100] + "..." if len(data['obs']) > 100 else data['obs']
                            obs_preview = obs_preview.replace('\n', ' ').replace('"', "'")
                            title += f" | {obs_preview}"
                            # Verifica se é uma observação válida (não é padrão de feriado/sobreaviso)
                            if data['obs'].strip() not in ['Feriado/Dia sem estágio', 'Sobreaviso', '']:
                                has_detailed_obs = True
                        
                        html += f"<td style='{cell_style}' title='{title}'>"
                        html += f"<strong>{day}</strong>"
                        if has_detailed_obs:
                            html += f" 📝"  # Indicador de observação detalhada
                        html += f"<br>"
                        html += f"<small>{hours}h</small>"
                        html += "</td>"
                    else:
                        # Data fora do período do cronograma
                        html += f"<td style='{cell_style} opacity: 0.5;'>{day}</td>"
            html += "</tr>"
        
        html += "</table></div>"
        
        calendars_html[f"{month_name} {year}"] = html
        
        # Avança para o próximo mês
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)
    
    return calendars_html

def calculate_schedule(start_date, total_hours, hours_map, holidays, observations):
    """
    Calcula o cronograma dia a dia até atingir o total de horas.
    Retorna um DataFrame com o cronograma e a data de término.
    """
    schedule_data = []
    accumulated_hours = 0
    current_date = start_date
    end_date = None

    # Converte a lista de feriados para um set de objetos date para busca rápida
    holiday_dates = {h['date'] for h in holidays}

    while accumulated_hours < total_hours:
        weekday = current_date.weekday()
        
        # Observação personalizada ou padrão para feriados
        obs = observations.get(current_date, '')
        
        # 1. Verifica se é feriado/dia sem estágio
        if current_date in holiday_dates:
            hours_planned = 0
            # Adiciona a linha, mas sem horas
            schedule_data.append({
                'Data': current_date,
                'Dia da semana': get_weekday_name(weekday),
                'Horas no dia': hours_planned,
                'Horas acumuladas': accumulated_hours,
                'Observação': obs if obs else 'Feriado/Dia sem estágio'
            })
            current_date += timedelta(days=1)
            continue # Pula para o próximo dia

        # 2. Obtém as horas planejadas para o dia da semana
        hours_planned = hours_map.get(weekday, 0)

        if hours_planned > 0:
            # 3. Verifica se as horas planejadas excedem o total
            if accumulated_hours + hours_planned > total_hours:
                hours_planned = total_hours - accumulated_hours
            
            # 4. Atualiza as horas acumuladas
            accumulated_hours += hours_planned
            
            # 5. Registra a linha no cronograma
            schedule_data.append({
                'Data': current_date,
                'Dia da semana': get_weekday_name(weekday),
                'Horas no dia': hours_planned,
                'Horas acumuladas': accumulated_hours,
                'Observação': obs
            })
            
            # 6. Se atingiu o total, esta é a data de término
            if accumulated_hours == total_hours:
                end_date = current_date
                break # Sai do loop principal
        
        # 7. Se não houver horas planejadas (Ter/Sáb/Dom), registra com 0 horas
        else:
            schedule_data.append({
                'Data': current_date,
                'Dia da semana': get_weekday_name(weekday),
                'Horas no dia': 0,
                'Horas acumuladas': accumulated_hours,
                'Observação': obs
            })

        # Avança para o próximo dia
        current_date += timedelta(days=1)

    df_schedule = pd.DataFrame(schedule_data)
    return df_schedule, end_date

# --- Gerenciamento de Estado (Feriados) ---

def load_holidays_from_csv():
    """Carrega os feriados do arquivo CSV."""
    if os.path.exists(HOLIDAYS_CSV):
        try:
            df = pd.read_csv(HOLIDAYS_CSV)
            if not df.empty and 'date' in df.columns:
                holidays = []
                for _, row in df.iterrows():
                    holidays.append({
                        'date': pd.to_datetime(row['date']).date(),
                        'description': row['description'] if pd.notna(row['description']) else ''
                    })
                return holidays
        except Exception as e:
            st.error(f"Erro ao carregar feriados: {e}")
    return []

def save_holidays_to_csv(holidays):
    """Salva os feriados no arquivo CSV."""
    try:
        df = pd.DataFrame(holidays)
        if not df.empty:
            df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
            df.to_csv(HOLIDAYS_CSV, index=False)
        else:
            # Se não houver feriados, cria arquivo vazio com cabeçalho
            pd.DataFrame(columns=['date', 'description']).to_csv(HOLIDAYS_CSV, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar feriados: {e}")

def load_observations_from_csv():
    """Carrega as observações do arquivo CSV."""
    if os.path.exists(OBSERVATIONS_CSV):
        try:
            df = pd.read_csv(OBSERVATIONS_CSV)
            if not df.empty and 'date' in df.columns:
                observations = {}
                for _, row in df.iterrows():
                    observations[pd.to_datetime(row['date']).date()] = row['observacao'] if pd.notna(row['observacao']) else ''
                return observations
        except Exception as e:
            st.error(f"Erro ao carregar observações: {e}")
    return {}

def save_observations_to_csv(observations):
    """Salva as observações no arquivo CSV."""
    try:
        data = [{'date': k.strftime('%Y-%m-%d'), 'observacao': v} for k, v in observations.items() if v]
        df = pd.DataFrame(data)
        if not df.empty:
            df.to_csv(OBSERVATIONS_CSV, index=False)
        else:
            pd.DataFrame(columns=['date', 'observacao']).to_csv(OBSERVATIONS_CSV, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar observações: {e}")

if 'holidays' not in st.session_state:
    st.session_state.holidays = load_holidays_from_csv()

if 'observations' not in st.session_state:
    st.session_state.observations = load_observations_from_csv()

def add_holiday(holiday_date, description):
    """Adiciona um feriado à lista de feriados na session_state e salva no CSV."""
    # Evita duplicatas
    if holiday_date not in [h['date'] for h in st.session_state.holidays]:
        st.session_state.holidays.append({'date': holiday_date, 'description': description})
        st.session_state.holidays.sort(key=lambda x: x['date']) # Mantém ordenado
        save_holidays_to_csv(st.session_state.holidays)

def remove_holidays(dates_to_remove):
    """Remove feriados selecionados da lista e salva no CSV."""
    st.session_state.holidays = [h for h in st.session_state.holidays if h['date'] not in dates_to_remove]
    save_holidays_to_csv(st.session_state.holidays)
    
    # Remove também as observações padrão "Feriado/Dia sem estágio" dessas datas
    for date_to_remove in dates_to_remove:
        if date_to_remove in st.session_state.observations:
            if st.session_state.observations[date_to_remove] == 'Feriado/Dia sem estágio':
                del st.session_state.observations[date_to_remove]
    save_observations_to_csv(st.session_state.observations)

# --- Interface Streamlit ---

st.set_page_config(
    layout="wide", 
    page_title="Cronograma de Estágio",
    initial_sidebar_state="expanded"
)

# Cabeçalho
st.markdown("""
<div style='text-align: center; padding: 1rem 0 2rem 0;'>
    <h1 style='color: #1f77b4; margin-bottom: 0.5rem;'>Cronograma de Estágio</h1>
    <p style='color: #666; font-size: 1.1rem;'>Sistema de Gerenciamento de Horas</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar: Parâmetros e Feriados ---
with st.sidebar:
    st.markdown("### Parâmetros do Estágio")
    
    # Parâmetros fixos/readonly em container
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Data de Início", START_DATE.strftime('%d/%m/%Y'))
        with col2:
            st.metric("Total de Horas", f"{TOTAL_HOURS}h")
    
    st.markdown("---")
    
    # Padrão de horas
    st.markdown("### Carga Horária Semanal")
    
    dias_semana = [
        ("Segunda", HOURS_PER_WEEKDAY[0]),
        ("Terça", HOURS_PER_WEEKDAY[1]),
        ("Quarta", HOURS_PER_WEEKDAY[2]),
        ("Quinta", HOURS_PER_WEEKDAY[3]),
        ("Sexta", HOURS_PER_WEEKDAY[4]),
        ("Sábado", HOURS_PER_WEEKDAY[5]),
        ("Domingo", HOURS_PER_WEEKDAY[6])
    ]
    
    for dia, horas in dias_semana:
        if horas > 0:
            st.markdown(f"**{dia}**: `{horas}h`")
        else:
            st.markdown(f"{dia}: `{horas}h`")

    st.markdown("---")

    # Seção de Feriados
    st.markdown("### Feriados/Dias sem Estágio")
    
    with st.expander("Adicionar novo feriado", expanded=False):
        new_holiday_date = st.date_input(
            "Data", 
            value=date.today(), 
            key='new_holiday_date',
            help="Selecione a data do feriado ou dia sem estágio"
        )
        new_holiday_description = st.text_input(
            "Descrição", 
            key='new_holiday_description',
            placeholder="Ex: Feriado Nacional, Recesso, etc."
        )
        
        if st.button("Adicionar Feriado", use_container_width=True, type="primary"):
            if new_holiday_date:
                add_holiday(new_holiday_date, new_holiday_description)
                st.success(f"Feriado em {new_holiday_date.strftime('%d/%m/%Y')} adicionado com sucesso.")
                st.rerun()
            else:
                st.error("Por favor, selecione uma data.")
        
    # Tabela de Feriados Cadastrados
    if st.session_state.holidays:
        st.markdown(f"#### Feriados Cadastrados ({len(st.session_state.holidays)})")
        
        # Cria um DataFrame para exibição e seleção
        df_holidays = pd.DataFrame(st.session_state.holidays)
        df_holidays.columns = ['Data', 'Descrição']
        df_holidays['Data'] = df_holidays['Data'].apply(lambda x: x.strftime('%d/%m/%Y')) # Formata para exibição
        
        # Adiciona uma coluna de seleção
        df_holidays_with_selection = df_holidays.copy()
        df_holidays_with_selection.insert(0, 'Remover', False)
        
        # Edita a tabela para permitir seleção
        edited_df = st.data_editor(
            df_holidays_with_selection,
            hide_index=True,
            column_config={
                "Remover": st.column_config.CheckboxColumn(
                    "Remover?",
                    help="Selecione para remover o feriado",
                    default=False,
                ),
                "Data": st.column_config.Column(disabled=True),
                "Descrição": st.column_config.Column(disabled=True),
            },
            key="holidays_editor"
        )
        
        # Processa a remoção
        selected_rows = edited_df[edited_df['Remover'] == True]
        if not selected_rows.empty:
            # Converte as datas selecionadas de volta para o formato date para remoção
            dates_to_remove_str = selected_rows['Data'].tolist()
            # A data original no session_state está como date object, precisamos converter a string de volta
            dates_to_remove = [datetime.strptime(d, '%d/%m/%Y').date() for d in dates_to_remove_str]
            
            if st.button("Confirmar Remoção", key="confirm_removal_btn", type="primary", use_container_width=True):
                remove_holidays(dates_to_remove)
                st.success(f"{len(dates_to_remove)} feriado(s) removido(s) com sucesso.")
                st.rerun() # Recarrega para atualizar a lista e o cronograma
    else:
        st.info("Nenhum feriado cadastrado. Use o botão acima para adicionar.")

# --- Main: Resultados e Cronograma ---

# 1. Cálculo do Cronograma
df_schedule, end_date = calculate_schedule(
    START_DATE, 
    TOTAL_HOURS, 
    HOURS_PER_WEEKDAY, 
    st.session_state.holidays,
    st.session_state.observations
)

# 2. Resumos no Topo
if end_date:
    total_days = (end_date - START_DATE).days + 1
    # Cálculo simples de semanas úteis (aproximação)
    # Conta o número de dias de estágio no período
    working_days = df_schedule[df_schedule['Horas no dia'] > 0].shape[0]
    # Uma semana "útil" tem 4 dias de estágio (Seg, Qua, Qui, Sex)
    estimated_weeks = working_days / 4 
    
    # Cabeçalho da seção
    st.markdown("## Resumo do Cronograma")
    
    # Métricas em cards
    col_start, col_end, col_total, col_weeks = st.columns(4)
    
    with col_start:
        st.metric(
            "Data de Início", 
            START_DATE.strftime('%d/%m/%Y'),
            help="Data de início do estágio"
        )
    
    with col_end:
        delta_days = (end_date - START_DATE).days
        st.metric(
            "Data de Término", 
            end_date.strftime('%d/%m/%Y'),
            delta=f"{delta_days} dias",
            help="Data prevista para conclusão das 240 horas"
        )
    
    with col_total:
        st.metric(
            "Total de Horas", 
            f"{TOTAL_HOURS}h",
            help="Carga horária total do estágio"
        )
    
    with col_weeks:
        st.metric(
            "Semanas Estimadas", 
            f"{estimated_weeks:.1f}",
            help="Número estimado de semanas para conclusão"
        )
    
    st.markdown("---")

    # 3. Tabela do Cronograma
    st.markdown("---")
    st.markdown("## Cronograma Detalhado")
    st.markdown("*Clique na coluna 'Observação' para adicionar anotações personalizadas*")
    
    # Formatação para exibição
    df_display = df_schedule.copy()
    df_display['Data_Original'] = df_display['Data']  # Mantém a data original para referência
    df_display['Data'] = df_display['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
    
    # Editor de observações
    edited_schedule = st.data_editor(
        df_display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Data": st.column_config.Column(width="small", disabled=True),
            "Dia da semana": st.column_config.Column(width="medium", disabled=True),
            "Horas no dia": st.column_config.Column(width="small", disabled=True),
            "Horas acumuladas": st.column_config.Column(width="small", disabled=True),
            "Observação": st.column_config.TextColumn(width="large", help="Clique para adicionar/editar observações"),
            "Data_Original": None  # Oculta a coluna
        },
        disabled=["Data", "Dia da semana", "Horas no dia", "Horas acumuladas", "Data_Original"],
        key="schedule_editor",
        column_order=["Data", "Dia da semana", "Horas no dia", "Horas acumuladas", "Observação"]
    )
    
    # Detecta mudanças nas observações e salva
    if edited_schedule is not None:
        new_observations = {}
        for _, row in edited_schedule.iterrows():
            obs = row['Observação']
            if obs and obs.strip() and obs.strip() != '':  # Se houver observação não vazia
                new_observations[row['Data_Original']] = obs.strip()
        
        # Verifica se houve mudança real
        if new_observations != st.session_state.observations:
            st.session_state.observations = new_observations
            save_observations_to_csv(st.session_state.observations)
    
    # 4. Visualização em Calendário e Observações
    st.markdown("---")
    
    # Cria abas principais: Calendário e Observações
    main_tab_calendario, main_tab_observacoes = st.tabs(["📅 Calendário", "📝 Observações"])
    
    # Filtra observações válidas (para uso em ambas as abas)
    observacoes_validas = {
        k: v for k, v in st.session_state.observations.items() 
        if v and v.strip() and v.strip() != 'Feriado/Dia sem estágio' and v.strip() != 'Sobreaviso'
    }
    
    with main_tab_calendario:
        st.markdown("## Visualização em Calendário")
        
        calendars = generate_calendar_view(df_schedule, START_DATE, end_date)
        
        if calendars:
            # Cria abas para cada mês
            tabs = st.tabs(list(calendars.keys()))
            
            for i, (month_year, cal_html) in enumerate(calendars.items()):
                with tabs[i]:
                    st.markdown(cal_html, unsafe_allow_html=True)
                    
                    # Legenda
                    st.markdown("""
                    <div style='margin-top: 1rem; padding: 1rem; background-color: rgba(128, 128, 128, 0.1); border-radius: 5px; border: 1px solid rgba(128, 128, 128, 0.3);'>
                        <strong>Legenda:</strong><br>
                        <span style='display: inline-block; width: 20px; height: 20px; background-color: rgba(76, 175, 80, 0.3); border: 1px solid rgba(128, 128, 128, 0.3); margin-right: 5px;'></span> 8 horas<br>
                        <span style='display: inline-block; width: 20px; height: 20px; background-color: rgba(33, 150, 243, 0.3); border: 1px solid rgba(128, 128, 128, 0.3); margin-right: 5px;'></span> 4 horas<br>
                        <span style='display: inline-block; width: 20px; height: 20px; background-color: rgba(128, 128, 128, 0.15); border: 1px solid rgba(128, 128, 128, 0.3); margin-right: 5px;'></span> Sem horas (feriado/folga)<br>
                        <span style='margin-right: 5px;'>📝</span> Possui observação detalhada
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Filtra observações do mês atual
                    month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                                  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    month_name_atual = month_year.split()[0]
                    year_atual = int(month_year.split()[1])
                    month_num = month_names.index(month_name_atual) + 1
                    
                    obs_do_mes = {
                        k: v for k, v in observacoes_validas.items()
                        if k.month == month_num and k.year == year_atual
                    }
                    
                    if obs_do_mes:
                        st.markdown("---")
                        st.markdown("##### 📝 Observações deste mês")
                        st.markdown("*Selecione uma data para ver a observação completa:*")
                        
                        # Cria opções para o selectbox
                        opcoes = ["Selecione uma data..."]
                        datas_obs = sorted(obs_do_mes.keys())
                        for data_obs in datas_obs:
                            dia_semana = get_weekday_name(data_obs.weekday())
                            opcoes.append(f"{data_obs.strftime('%d/%m/%Y')} ({dia_semana})")
                        
                        data_selecionada = st.selectbox(
                            "Data com observação:",
                            opcoes,
                            key=f"select_obs_{month_year}",
                            label_visibility="collapsed"
                        )
                        
                        if data_selecionada != "Selecione uma data...":
                            # Extrai a data selecionada
                            data_str = data_selecionada.split(" (")[0]
                            data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                            
                            # Busca as horas trabalhadas nesse dia
                            horas_dia = 0
                            for _, row in df_schedule.iterrows():
                                if row['Data'] == data_obj:
                                    horas_dia = row['Horas no dia']
                                    break
                            
                            dia_semana = get_weekday_name(data_obj.weekday())
                            texto_obs = obs_do_mes[data_obj]
                            
                            # Exibe a observação em um card bonito
                            st.markdown(f"""
                            <div style='background-color: rgba(33, 150, 243, 0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #1f77b4;'>
                                <strong style='font-size: 1.1rem;'>📅 {dia_semana}, {data_str}</strong><br>
                                <span style='color: #888;'>⏱️ Horas trabalhadas: {horas_dia}h</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("**Relatório do dia:**")
                            st.markdown(f"""
                            <div style='background-color: rgba(128, 128, 128, 0.05); padding: 1rem; border-radius: 8px; border: 1px solid rgba(128, 128, 128, 0.2); white-space: pre-wrap; line-height: 1.6;'>
{texto_obs}
                            </div>
                            """, unsafe_allow_html=True)
    
    with main_tab_observacoes:
        st.markdown("## Observações do Estágio")
        st.markdown("*Registro detalhado das atividades realizadas em cada dia*")
        
        if observacoes_validas:
            # Ordena as observações por data (mais recente primeiro)
            observacoes_ordenadas = sorted(observacoes_validas.items(), key=lambda x: x[0], reverse=True)
            
            st.markdown(f"**Total de observações:** {len(observacoes_ordenadas)}")
            st.markdown("---")
            
            for data_obs, texto_obs in observacoes_ordenadas:
                # Formata a data para exibição
                dia_semana = get_weekday_name(data_obs.weekday())
                data_formatada = data_obs.strftime('%d/%m/%Y')
                
                # Busca as horas trabalhadas nesse dia
                horas_dia = 0
                for _, row in df_schedule.iterrows():
                    if row['Data'] == data_obs:
                        horas_dia = row['Horas no dia']
                        break
                
                # Cria um card para cada observação
                with st.expander(f"📌 {data_formatada} ({dia_semana}) - {horas_dia}h trabalhadas", expanded=False):
                    # Cabeçalho com informações da data
                    st.markdown(f"""
                    <div style='background-color: rgba(33, 150, 243, 0.1); padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #1f77b4;'>
                        <strong style='font-size: 1.1rem;'>📅 {dia_semana}, {data_formatada}</strong><br>
                        <span style='color: #888;'>⏱️ Horas trabalhadas: {horas_dia}h</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Conteúdo da observação formatado
                    st.markdown("**Relatório do dia:**")
                    st.markdown(f"""
                    <div style='background-color: rgba(128, 128, 128, 0.05); padding: 1rem; border-radius: 8px; border: 1px solid rgba(128, 128, 128, 0.2); white-space: pre-wrap; line-height: 1.6;'>
{texto_obs}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📭 Nenhuma observação detalhada cadastrada ainda.")
            st.markdown("""
            **Como adicionar observações:**
            1. Vá até a tabela do **Cronograma Detalhado** acima
            2. Clique na coluna **Observação** do dia desejado
            3. Digite seu relatório ou anotações
            4. As observações serão salvas automaticamente e aparecerão aqui
            """)
    
    # 5. Exportar Cronograma (Opcional)
    @st.cache_data
    def convert_df_to_csv(df):
        # Converte o DataFrame original (com objetos date) para CSV
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(df_schedule)

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="Exportar Cronograma para CSV",
            data=csv,
            file_name=f'cronograma_estagio_{START_DATE.strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True,
            type="secondary"
        )

else:
    st.warning("Não foi possível calcular o cronograma. Verifique os parâmetros.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem 0;'>
    <small>Sistema de Cronograma de Estágio | Gerenciamento de Horas</small>
</div>
""", unsafe_allow_html=True)