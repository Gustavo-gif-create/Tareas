import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Ideas & Tareas Hub (Google Sheets)",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    try:
        df = conn.read(worksheet=worksheet, ttl="0s")
        expected_cols = ["ID", "Titulo", "Estado", "Prioridad", "Fecha", "Fecha_Creacion"]
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"Error al leer la hoja '{worksheet}': {e}")
        return pd.DataFrame(columns=["ID", "Titulo", "Estado", "Prioridad", "Fecha", "Fecha_Creacion"])

def save_data(worksheet, df):
    conn.update(worksheet=worksheet, data=df)

def get_task_status(status):
    return status == "Completada"

# --- NAVEGACIÓN Y SIDEBAR ---
st.sidebar.title("📌 Navegación")
menu = st.sidebar.radio("Ir a", ["✅ Gestor de Tareas", "💡 Banco de Ideas"])

st.sidebar.markdown("---")
st.sidebar.success("🟢 Conectado exitosamente con Google Sheets. Tus datos están 100% seguros y respaldados.")

# ==========================================
# SECCIÓN: GESTOR DE TAREAS
# ==========================================
if menu == "✅ Gestor de Tareas":
    st.title("✅ Gestor de Tareas")
    st.write("Organiza tus pendientes diarios y guárdalos en Google Sheets.")

    tasks_df = get_data("Tareas")

    # Formulario para agregar tarea
    with st.expander("➕ Crear Nueva Tarea", expanded=True):
        with st.form("new_task_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                title = st.text_input("Título de la tarea", placeholder="Ej. Enviar informe mensual...")
            with col2:
                priority = st.selectbox("Prioridad", ["Baja", "Media", "Alta"], index=1)
            with col3:
                due_date = st.date_input("Vencimiento", value=date.today())
            
            submitted = st.form_submit_button("Guardar Tarea", use_container_width=True)
            if submitted:
                if title.strip():
                    new_id = int(datetime.now().timestamp())
                    new_row = pd.DataFrame([{
                        "ID": new_id,
                        "Titulo": title.strip(),
                        "Estado": "Pendiente",
                        "Prioridad": priority,
                        "Fecha": str(due_date),
                        "Fecha_Creacion": str(date.today())
                    }])
                    updated_df = pd.concat([tasks_df, new_row], ignore_index=True)
                    save_data("Tareas", updated_df)
                    st.success("¡Tarea guardada en Google Sheets!")
                    st.rerun()
                else:
                    st.warning("El título no puede estar vacío.")

    st.markdown("---")

    if tasks_df.empty:
        st.info("No tienes tareas registradas por el momento.")
    else:
        filter_status = st.segmented_control(
            "Filtrar por estado", 
            options=["Todas", "Pendientes", "Completadas"], 
            default="Pendientes"
        )

        for index, row in tasks_df.iterrows():
            t_id = row["ID"]
            t_title = row["Titulo"]
            t_status = row["Estado"]
            t_priority = row["Prioridad"]
            t_due = row["Fecha"]

            if filter_status == "Pendientes" and get_task_status(t_status):
                continue
            if filter_status == "Completadas" and not get_task_status(t_status):
                continue

            col_check, col_info, col_del = st.columns([0.5, 4, 0.5])

            is_completed = get_task_status(t_status)

            with col_check:
                checked = st.checkbox("", value=is_completed, key=f"check_{t_id}_{index}")
                if checked != is_completed:
                    tasks_df.at[index, "Estado"] = "Completada" if checked else "Pendiente"
                    save_data("Tareas", tasks_df)
                    st.rerun()

            with col_info:
                if is_completed:
                    st.markdown(f"~~**{t_title}**~~")
                else:
                    st.markdown(f"**{t_title}**")
                
                p_color = "🟢" if t_priority == "Baja" else "🟡" if t_priority == "Media" else "🔴"
                st.caption(f"{p_color} Prioridad: {t_priority} | 📅 Vencimiento: {t_due}")

            with col_del:
                if st.button("🗑️", key=f"del_{t_id}_{index}"):
                    updated_df = tasks_df.drop(index)
                    save_data("Tareas", updated_df)
                    st.rerun()

            st.divider()

# ==========================================
# SECCIÓN: BANCO DE IDEAS
# ==========================================
elif menu == "💡 Banco de Ideas":
    st.title("💡 Banco de Ideas y Notas")
    st.write("Anota proyectos o reflexiones y conviértelos en tareas cuando quieras.")

    ideas_df = get_data("Ideas")

    # Formulario para agregar idea
    with st.expander("📝 Registrar Nueva Idea", expanded=False):
        with st.form("new_idea_form", clear_on_submit=True):
            col_t, col_c = st.columns([3, 1])
            with col_t:
                i_title = st.text_input("Título de la idea", placeholder="Ej. Crear canal de podcast...")
            with col_c:
                i_category = st.selectbox("Categoría", ["General", "Proyecto", "Personal", "Trabajo"])
            
            i_content = st.text_area("Detalles / Notas", placeholder="Escribe detalles adicionales...", key="idea_content")

            submitted = st.form_submit_button("Guardar Idea", use_container_width=True)
            if submitted:
                if i_title.strip():
                    new_id = int(datetime.now().timestamp())
                    new_row = pd.DataFrame([{
                        "ID": new_id,
                        "Titulo": i_title.strip(),
                        "Estado": "Pendiente",
                        "Prioridad": "Media",
                        "Fecha": str(date.today()),
                        "Fecha_Creacion": str(date.today())
                    }])
                    updated_df = pd.concat([ideas_df, new_row], ignore_index=True)
                    save_data("Ideas", updated_df)
                    st.success("¡Idea guardada en Google Sheets!")
                    st.rerun()
                else:
                    st.warning("Escribe al menos un título para la idea.")

    st.markdown("---")

    if ideas_df.empty:
        st.info("No tienes ideas guardadas aún.")
    else:
        cols = st.columns(2)
        for index, row in ideas_df.iterrows():
            col = cols[index % 2]
            
            i_id = row["ID"]
            i_title = row["Titulo"]
            i_content = row["Fecha"]
            i_cat = row["Categoria"]

            with col:
                with st.container(border=True):
                    st.subheader(f"💡 {i_title}")
                    st.caption(f"🏷️ Categoría: **{i_cat}**")
                    if pd.notna(i_content) and i_content:
                        st.write(i_content)

                    act_col1, act_col2 = st.columns([2, 1])
                    with act_col1:
                        if st.button("➡️ Convertir en Tarea", key=f"conv_{i_id}_{index}"):
                            # 1. Agregar a Tareas
                            tasks_df = get_data("Tareas")
                            new_task_row = pd.DataFrame([{
                                "ID": int(datetime.now().timestamp()),
                                "Titulo": i_title,
                                "Estado": "Pendiente",
                                "Prioridad": "Media",
                                "Fecha": str(date.today()),
                                "Fecha_Creacion": str(date.today())
                            }])
                            updated_tasks = pd.concat([tasks_df, new_task_row], ignore_index=True)
                            save_data("Tareas", updated_tasks)
                            st.toast("¡Idea convertida en tarea!", icon="✅")
                    
                    with act_col2:
                        if st.button("Eliminar", key=f"del_idea_{i_id}_{index}"):
                            updated_ideas = ideas_df.drop(index)
                            save_data("Ideas", updated_ideas)
                            st.rerun()
