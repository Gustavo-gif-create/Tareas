import streamlit as st
import sqlite3
from datetime import datetime, date

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Ideas & Tareas Hub",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BASE DE DATOS (SQLITE) ---
DB_NAME = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de Tareas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            priority TEXT DEFAULT 'Media',
            due_date TEXT,
            status TEXT DEFAULT 'Pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de Ideas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            content TEXT,
            favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Inicializar las tablas si no existen
init_db()

# --- FUNCIONES DE BASE DE DATOS: TAREAS ---
def add_task(title, priority, due_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
        (title, priority, due_date.isoformat() if due_date else None)
    )
    conn.commit()
    conn.close()

def get_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY status ASC, due_date ASC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_task_status(task_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- FUNCIONES DE BASE DE DATOS: IDEAS ---
def add_idea(title, category, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ideas (title, category, content) VALUES (?, ?, ?)",
        (title, category, content)
    )
    conn.commit()
    conn.close()

def get_ideas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ideas ORDER BY favorite DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def toggle_favorite_idea(idea_id, current_fav):
    conn = get_connection()
    cursor = conn.cursor()
    new_fav = 0 if current_fav == 1 else 1
    cursor.execute("UPDATE ideas SET favorite = ? WHERE id = ?", (new_fav, idea_id))
    conn.commit()
    conn.close()

def delete_idea(idea_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()

def convert_idea_to_task(idea_title, idea_content):
    task_title = f"{idea_title}"
    if idea_content:
        task_title += f" ({idea_content[:40]}...)"
    add_task(task_title, "Media", date.today())

# --- NAVEGACIÓN Y SIDEBAR ---
st.sidebar.title("📌 Navegación")
menu = st.sidebar.radio("Ir a", ["✅ Gestor de Tareas", "💡 Banco de Ideas"])

st.sidebar.markdown("---")
st.sidebar.info(
    "**Sugerencia de Persistencia:**\n"
    "En Streamlit Community Cloud, la base de datos local SQLite se reiniciará al redeplegar. "
    "Para persistencia 100% permanente en la nube, conecta esta app a Supabase o Google Sheets."
)

# ==========================================
# SECCIÓN: GESTOR DE TAREAS
# ==========================================
if menu == "✅ Gestor de Tareas":
    st.title("✅ Gestor de Tareas")
    st.write("Organiza tus pendientes diarios y asigna prioridades.")

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
                    add_task(title.strip(), priority, due_date)
                    st.success("¡Tarea creada exitosamente!")
                    st.rerun()
                else:
                    st.warning("El título no puede estar vacío.")

    st.markdown("---")

    # Obtener y mostrar tareas
    tasks = get_tasks()
    
    if not tasks:
        st.info("No tienes tareas registradas por el momento.")
    else:
        # Filtros rápidos
        filter_status = st.segmented_control(
            "Filtrar por estado", 
            options=["Todas", "Pendientes", "Completadas"], 
            default="Todas"
        )

        for task in tasks:
            task_id = task["id"]
            t_title = task["title"]
            t_priority = task["priority"]
            t_due = task["due_date"]
            t_status = task["status"]

            # Aplicar filtro
            if filter_status == "Pendientes" and t_status == "Completada":
                continue
            if filter_status == "Completadas" and t_status == "Pendiente":
                continue

            # Render de card de tarea
            col_check, col_info, col_del = st.columns([0.5, 4, 0.5])

            is_completed = (t_status == "Completada")

            with col_check:
                checked = st.checkbox("", value=is_completed, key=f"check_{task_id}")
                if checked != is_completed:
                    new_st = "Completada" if checked else "Pendiente"
                    update_task_status(task_id, new_st)
                    st.rerun()

            with col_info:
                if is_completed:
                    st.markdown(f"~~**{t_title}**~~")
                else:
                    st.markdown(f"**{t_title}**")
                
                # Metadata (badges)
                p_color = "🟢" if t_priority == "Baja" else "🟡" if t_priority == "Media" else "🔴"
                st.caption(f"{p_color} Prioridad: {t_priority} | 📅 Vencimiento: {t_due if t_due else 'Sin fecha'}")

            with col_del:
                if st.button("🗑️", key=f"del_task_{task_id}"):
                    delete_task(task_id)
                    st.rerun()

            st.divider()

# ==========================================
# SECCIÓN: BANCO DE IDEAS
# ==========================================
elif menu == "💡 Banco de Ideas":
    st.title("💡 Banco de Ideas y Notas")
    st.write("Anota reflexiones, proyectos futuros y conviértelos en tareas cuando estés listo.")

    # Formulario para agregar idea
    with st.expander("📝 Registrar Nueva Idea", expanded=False):
        with st.form("new_idea_form", clear_on_submit=True):
            col_t, col_c = st.columns([3, 1])
            with col_t:
                i_title = st.text_input("Título de la idea", placeholder="Ej. Crear app de recetas...")
            with col_c:
                i_category = st.selectbox("Categoría", ["General", "Proyecto", "Personal", "Trabajo"])
            
            i_content = st.text_area("Detalles / Notas (opcional)", placeholder="Escribe más información...")

            submitted_idea = st.form_submit_button("Guardar Idea", use_container_width=True)
            if submitted_idea:
                if i_title.strip():
                    add_idea(i_title.strip(), i_category, i_content.strip())
                    st.success("¡Idea guardada!")
                    st.rerun()
                else:
                    st.warning("Escribe al menos un título para la idea.")

    st.markdown("---")

    ideas = get_ideas()

    if not ideas:
        st.info("No tienes ideas guardadas aún. ¡Anota la primera!")
    else:
        # Render de ideas en rejilla de 2 columnas
        cols = st.columns(2)
        for index, idea in enumerate(ideas):
            col = cols[index % 2]
            
            i_id = idea["id"]
            i_title = idea["title"]
            i_cat = idea["category"]
            i_content = idea["content"]
            i_fav = idea["favorite"]

            with col:
                with st.container(border=True):
                    head_col1, head_col2 = st.columns([4, 1])
                    with head_col1:
                        fav_star = "⭐ " if i_fav == 1 else ""
                        st.subheader(f"{fav_star}{i_title}")
                    with head_col2:
                        fav_btn_icon = "★" if i_fav == 1 else "☆"
                        if st.button(fav_btn_icon, key=f"fav_{i_id}"):
                            toggle_favorite_idea(i_id, i_fav)
                            st.rerun()

                    st.caption(f"🏷️ Categoría: **{i_cat}**")
                    if i_content:
                        st.write(i_content)

                    act_col1, act_col2 = st.columns([2, 1])
                    with act_col1:
                        if st.button("➡️ Convertir en Tarea", key=f"conv_{i_id}"):
                            convert_idea_to_task(i_title, i_content)
                            st.toast(f"¡Idea convertida en tarea pendiente!", icon="✅")
                    with act_col2:
                        if st.button("Eliminar", key=f"del_idea_{i_id}"):
                            delete_idea(i_id)
                            st.rerun()


