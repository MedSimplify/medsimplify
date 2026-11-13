
import streamlit as st
import sqlite3
from pathlib import Path
import html
import os
import hmac
import uuid
import hashlib
import secrets

# ==================================================
# 1. CONFIGURACION
# ==================================================

st.set_page_config(
    page_title="MedSimplify | Fast learning",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path(__file__).parent
ASSETS = BASE / "assets"
STORAGE = BASE / "private_storage"
DATABASE = BASE / "medsimplify.db"
LOGO = ASSETS / "logo.png.png"


ASSETS.mkdir(exist_ok=True)
STORAGE.mkdir(exist_ok=True)

EMAIL = "medsimplify2@gmail.com"

CATEGORIES = [
    "Fichas de estudio",
    "Resúmenes",
    "Cuestionarios y simulacros",
    "Libros y documentos",
    "Material académico",
    "Infografías y fichas visuales"
]

ICONS = {
    "Fichas de estudio": "📚",
    "Resúmenes": "🧠",
    "Cuestionarios y simulacros": "📝",
    "Libros y documentos": "📖",
    "Material académico": "🔬",
    "Infografías y fichas visuales": "🩺"
}

# ==================================================
# 2. BASE DE DATOS
# ==================================================

def initialize_database():
    with sqlite3.connect(DATABASE) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                image_path TEXT,
                pdf_path TEXT,
                active INTEGER DEFAULT 1
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.commit()


def get_products(category=None):
    with sqlite3.connect(DATABASE) as con:
        if category:
            return con.execute("""
                SELECT * FROM products
                WHERE active = 1 AND category = ?
                ORDER BY id DESC
            """, (category,)).fetchall()

        return con.execute("""
            SELECT * FROM products
            WHERE active = 1
            ORDER BY id DESC
        """).fetchall()


def get_product(product_id):
    with sqlite3.connect(DATABASE) as con:
        return con.execute("""
            SELECT * FROM products
            WHERE id = ? AND active = 1
        """, (product_id,)).fetchone()


initialize_database()

# ==================================================
# 3. ESTILO VISUAL
# ==================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #FFFFFF;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* PANEL LATERAL */

[data-testid="stSidebar"] {
    background-color: #102B4C;
    min-width: 260px;
}

[data-testid="stSidebar"] > div:first-child {
    background-color: #102B4C;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

[data-testid="stSidebar"] hr {
    border-color: #405A75;
}

[data-testid="stSidebar"] button {
    background-color: transparent;
    color: #FFFFFF;
    border: 1px solid transparent;
    border-radius: 9px;
    text-align: left;
    width: 100%;
    min-height: 43px;
    transition: 0.2s;
}

[data-testid="stSidebar"] button:hover {
    background-color: #24496E;
    border: 1px solid #52789D;
    color: #FFFFFF;
}

[data-testid="stSidebar"] button p {
    color: #FFFFFF;
    font-weight: 500;
}

/* TITULOS */

h1, h2, h3 {
    color: #17365D;
}

.section-title {
    color: #17365D;
    font-size: 27px;
    font-weight: 750;
    margin-top: 25px;
}

.muted {
    color: #718096;
}

/* BIENVENIDA */

.hero {
    background: linear-gradient(
        120deg,
        #102B4C,
        #245C91
    );
    border-radius: 18px;
    padding: 45px 40px;
    margin-top: 20px;
    margin-bottom: 35px;
}

.hero h1 {
    color: #FFFFFF;
    font-size: 37px;
    line-height: 1.25;
    font-weight: 800;
}

.hero p {
    color: #E5EFFB;
    font-size: 16px;
    line-height: 1.8;
}

/* CATEGORIAS Y PRODUCTOS */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #E2EAF2;
    border-radius: 13px;
}

.price {
    color: #245C91;
    font-size: 23px;
    font-weight: 750;
}

.product-description {
    color: #64748B;
    font-size: 14px;
    line-height: 1.6;
}

/* BOTONES PRINCIPALES */

.stButton > button {
    background-color: #17365D;
    color: #FFFFFF;
    border: 1px solid #17365D;
    border-radius: 9px;
    font-weight: 600;
    min-height: 42px;
}

.stButton > button:hover {
    background-color: #3976B9;
    color: #FFFFFF;
    border-color: #3976B9;
}

/* PIE DE PAGINA */

.footer {
    text-align: center;
    color: #718096;
    border-top: 1px solid #E2EAF2;
    padding: 25px 10px;
    margin-top: 50px;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 4. ESTADO DE NAVEGACION
# ==================================================

if "page" not in st.session_state:
    st.session_state.page = "Inicio"

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

if "customer_email" not in st.session_state:
    st.session_state.customer_email = None

if "customer_name" not in st.session_state:
    st.session_state.customer_name = None


def navigate(page):
    st.session_state.page = page
    st.rerun()


# ==================================================
# 5. PANEL LATERAL
# ==================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center; padding:15px 0 8px;">
            <div style="
                font-size:25px;
                font-weight:800;
                letter-spacing:-1px;">
                MedSimplify
            </div>
            <div style="
                color:#BDD3E8;
                font-size:11px;
                letter-spacing:1px;">
                Fast learning · Real understanding
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        "<p style='font-size:11px;letter-spacing:1.5px;"
        "font-weight:700;color:#BDD3E8;'>MENÚ PRINCIPAL</p>",
        unsafe_allow_html=True
    )

    if st.button("⌂   Inicio", use_container_width=True):
        navigate("Inicio")

    if st.button("▦   Categorías", use_container_width=True):
        navigate("Categorías")

    if st.button("✉   Contáctanos", use_container_width=True):
        navigate("Contáctanos")

    if st.button("▣   Tus compras", use_container_width=True):
        navigate("Tus compras")

    if st.button("♙   Mi cuenta", use_container_width=True):
        navigate("Mi cuenta")

    if st.session_state.get("customer_email"):
        st.caption(
            "Sesión: " + st.session_state.get("customer_name", "Cliente")
        )

    st.divider()

    st.markdown(
        "<p style='font-size:11px;letter-spacing:1.5px;"
        "font-weight:700;color:#BDD3E8;'>GESTIÓN</p>",
        unsafe_allow_html=True
    )

    if st.button("⚙   Administración", use_container_width=True):
        navigate("Administración")

    st.divider()

    st.markdown(
        """
        <div style="
            color:#BDD3E8;
            font-size:12px;
            text-align:center;
            padding:15px 0;">
            Aprende a tu ritmo.<br>
            Comprende con claridad.<br><br>
            <b>MedSimplify © 2026</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==================================================
# 6. LOGOTIPO
# ==================================================

def show_logo(home=False):

    if LOGO.exists():

        st.image(
            str(LOGO),
            width=580 if home else 230
        )

    else:

        st.markdown("""
        <div style="text-align:center;">
            <h1 style="
                color:#17365D;
                font-size:42px;
                margin-bottom:0;">
                MedSimplify
            </h1>
            <p style="
                color:#3976B9;
                letter-spacing:2px;">
                Fast learning · Real understanding
            </p>
        </div>
        """, unsafe_allow_html=True)


# ==================================================
# 7. PAGINA DE INICIO
# ==================================================

def show_home():

    # Centrar el logo usando una columna central de Streamlit.
    left_space, center_logo, right_space = st.columns([1, 2, 1])
    with center_logo:
        show_logo(home=True)

    st.markdown("""
    <div style="
        text-align:center;
        margin-top:12px;
        color:#3976B9;
        font-size:13px;
        letter-spacing:2px;
        font-weight:600;">
        FAST LEARNING · REAL UNDERSTANDING
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero">
       
        El conocimiento transforma.<br>
        Comprenderlo lo hace extraordinario.

        La medicina es un mundo fascinante.
        Con los recursos adecuados, cada concepto
        puede convertirse en una oportunidad para
        aprender, descubrir y crecer.
       
        Aprende a tu ritmo. Comprende con claridad.
        Crece con conocimiento.
        
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "Explorar nuestros productos  →",
        use_container_width=True
    ):
        navigate("Categorías")

    st.markdown(
        '<div class="section-title">Descubre nuestras categorías</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="muted">Encuentra el recurso que necesitas para aprender.</p>',
        unsafe_allow_html=True
    )

    columns = st.columns(3)

    for i, category in enumerate(CATEGORIES):

        with columns[i % 3]:

            with st.container(border=True):

                st.markdown(
                    f"### {ICONS[category]}",
                    unsafe_allow_html=True
                )

                st.markdown(f"**{category}**")

                st.caption(
                    "Explora nuestros recursos educativos."
                )

                if st.button(
                    "Explorar →",
                    key=f"home_cat_{i}",
                    use_container_width=True
                ):
                    st.session_state.selected_category = category
                    navigate("Productos")


# ==================================================
# 8. PAGINA DE CATEGORIAS
# ==================================================

def show_categories():

    st.title("Explora nuestras categorías")

    st.write(
        "Selecciona una categoría para descubrir "
        "los documentos disponibles."
    )

    columns = st.columns(3)

    for i, category in enumerate(CATEGORIES):

        with columns[i % 3]:

            with st.container(border=True):

                st.markdown(f"## {ICONS[category]}")

                st.subheader(category)

                if st.button(
                    "Ver productos →",
                    key=f"cat_{i}",
                    use_container_width=True
                ):
                    st.session_state.selected_category = category
                    navigate("Productos")


# ==================================================
# 9. CATALOGO DE PRODUCTOS
# ==================================================

def show_products():

    category = st.session_state.selected_category

    if category:
        st.title(category)
    else:
        st.title("Todos nuestros productos")

    if st.button("← Volver a categorías"):
        navigate("Categorías")

    products = get_products(category)

    if not products:

        st.info(
            "Todavía no hay documentos publicados en "
            "esta categoría. Pronto encontrarás nuevos recursos."
        )

        return

    columns = st.columns(3)

    for i, product in enumerate(products):

        with columns[i % 3]:

            with st.container(border=True):

                image_path = product[5]

                if image_path and Path(image_path).is_file():
                    st.image(
                        image_path,
                        use_container_width=True
                    )
                else:
                    st.markdown(
                        f"## {ICONS.get(product[2], '📘')}"
                    )

                st.subheader(product[1])

                st.caption(product[2])

                st.markdown(
                    f'<div class="product-description">'
                    f'{html.escape(product[3])}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="price">'
                    f'${product[4]:.2f} USD</div>',
                    unsafe_allow_html=True
                )

                if st.button(
                    "Ver detalles",
                    key=f"product_{product[0]}",
                    use_container_width=True
                ):

                    st.session_state.selected_product = product[0]
                    navigate("Detalle")


# ==================================================
# 10. DETALLES DEL PRODUCTO
# ==================================================

def show_product_detail():

    product_id = st.session_state.selected_product
    product = get_product(product_id) if product_id else None

    if not product:

        st.warning("No se ha seleccionado ningún producto.")

        if st.button("Volver a categorías"):
            navigate("Categorías")

        return

    if st.button("← Volver al catálogo"):
        navigate("Productos")

    st.title(product[1])

    col1, col2 = st.columns([1, 1])

    with col1:

        image_path = product[5]

        if image_path and Path(image_path).is_file():
            st.image(image_path, use_container_width=True)
        else:
            st.info("Imagen del producto próximamente.")

    with col2:

        st.subheader("Descripción del documento")

        st.write(product[3])

        st.caption(f"Categoría: {product[2]}")

        st.markdown(
            f'<div class="price">${product[4]:.2f} USD</div>',
            unsafe_allow_html=True
        )

        st.divider()

        st.info(
            "Los pagos electrónicos se habilitarán "
            "cuando conectemos la pasarela de pago."
        )

        st.button(
            "Comprar ahora",
            disabled=True,
            use_container_width=True
        )

    st.divider()

    st.subheader("Vista previa")

    st.write(
        "Aquí mostraremos las páginas de muestra "
        "que la administradora seleccione para este documento."
    )


# ==================================================
# 11. CONTACTO
# ==================================================

def show_contact():

    st.title("Contáctanos")

    st.markdown("""
    ¿Tienes alguna pregunta o necesitas ayuda?

    En MedSimplify queremos acompañarte en tu
    experiencia de aprendizaje.
    """)

    with st.container(border=True):

        st.markdown("### ✉ Nuestro correo electrónico")

        st.markdown(
            f"**{EMAIL}**"
        )

        st.link_button(
            "Enviar un correo electrónico",
            f"mailto:{EMAIL}",
            use_container_width=True
        )

    st.write(
        "Estaremos encantados de atender tus consultas."
    )


# ==================================================
# 12. TUS COMPRAS
# ==================================================

def show_purchases():

    st.title("Tus compras")

    st.write(
        "Aquí podrás consultar los productos digitales "
        "que hayas adquirido en MedSimplify."
    )

    st.info(
        "El historial de compras estará disponible "
        "cuando conectemos el registro de clientes "
        "y el sistema de pagos."
    )

    st.write(
        "Podrás consultar tus documentos, fechas "
        "de compra y enlaces de descarga."
    )


# ==================================================
# 13. MI CUENTA
# ==================================================

def create_password_hash(password):
    """Genera un hash seguro de contraseña con salt individual."""
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 200_000
    )
    return salt.hex() + "$" + derived.hex()


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 200_000
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def register_customer(full_name, email, password):
    password_hash = create_password_hash(password)
    with sqlite3.connect(DATABASE) as con:
        con.execute(
            """
            INSERT INTO customers (full_name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (full_name.strip(), email.strip().lower(), password_hash)
        )
        con.commit()


def authenticate_customer(email, password):
    with sqlite3.connect(DATABASE) as con:
        customer = con.execute(
            """
            SELECT id, full_name, email, password_hash
            FROM customers
            WHERE email = ?
            """,
            (email.strip().lower(),)
        ).fetchone()

    if customer and verify_password(password, customer[3]):
        return customer
    return None


def show_account():

    customer_email = st.session_state.get("customer_email")

    if customer_email:
        with sqlite3.connect(DATABASE) as con:
            customer = con.execute(
                "SELECT id, full_name, email FROM customers WHERE email = ?",
                (customer_email,)
            ).fetchone()

        if not customer:
            st.session_state.pop("customer_email", None)
            st.session_state.pop("customer_name", None)
            st.rerun()

        st.title("Mi cuenta")
        st.success(f"Has iniciado sesión como {customer[1]}.")
        st.write(f"**Correo electrónico:** {customer[2]}")
        st.info(
            "Tu cuenta ya está creada. El historial y la descarga de compras "
            "se habilitarán al integrar el sistema de pagos."
        )

        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.pop("customer_email", None)
            st.session_state.pop("customer_name", None)
            st.session_state.page = "Inicio"
            st.rerun()
        return

    st.title("Mi cuenta")
    st.write(
        "Inicia sesión para acceder a tu cuenta de MedSimplify "
        "o crea una cuenta nueva."
    )

    login_tab, register_tab = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with login_tab:
        st.subheader("Bienvenido de nuevo")
        with st.form("customer_login_form"):
            login_email = st.text_input(
                "Correo electrónico",
                placeholder="tucorreo@ejemplo.com"
            )
            login_password = st.text_input("Contraseña", type="password")
            login_submit = st.form_submit_button(
                "Iniciar sesión", use_container_width=True
            )

        if login_submit:
            if not login_email.strip() or not login_password:
                st.error("Escribe tu correo y contraseña.")
            else:
                customer = authenticate_customer(login_email, login_password)
                if customer:
                    st.session_state.customer_email = customer[2]
                    st.session_state.customer_name = customer[1]
                    st.success("¡Inicio de sesión correcto!")
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")

    with register_tab:
        st.subheader("Crear una cuenta")
        with st.form("customer_register_form"):
            full_name = st.text_input("Nombre completo")
            register_email = st.text_input(
                "Correo electrónico",
                placeholder="tucorreo@ejemplo.com"
            )
            register_password = st.text_input(
                "Crear contraseña", type="password",
                help="Usa al menos 8 caracteres."
            )
            confirm_password = st.text_input(
                "Confirmar contraseña", type="password"
            )
            register_submit = st.form_submit_button(
                "Crear mi cuenta", use_container_width=True
            )

        if register_submit:
            if not full_name.strip() or not register_email.strip():
                st.error("Completa tu nombre y correo electrónico.")
            elif "@" not in register_email or "." not in register_email.split("@")[-1]:
                st.error("Escribe un correo electrónico válido.")
            elif len(register_password) < 8:
                st.error("La contraseña debe tener al menos 8 caracteres.")
            elif register_password != confirm_password:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    register_customer(full_name, register_email, register_password)
                    st.success(
                        "¡Tu cuenta fue creada! Ahora puedes iniciar sesión."
                    )
                except sqlite3.IntegrityError:
                    st.error(
                        "Ya existe una cuenta con ese correo electrónico. "
                        "Prueba iniciar sesión."
                    )


# 14. ENCABEZADO DE LAS PAGINAS INTERNAS
# ==================================================

def internal_header():

    col1, col2 = st.columns([1, 3])

    with col1:

        if LOGO.exists():
            st.image(str(LOGO), width=200)
        else:
            st.markdown("### MedSimplify")

    with col2:
        st.markdown(
            """
            <div style="
                text-align:right;
                padding-top:25px;
                color:#3976B9;
                font-size:13px;
                font-weight:600;">
                Fast learning · Real understanding
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()


# ==================================================

# ==================================================
# AREA DE ADMINISTRACION
# ==================================================

def save_uploaded_file(uploaded_file, allowed_extensions):
    if uploaded_file is None:
        return None
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in allowed_extensions:
        raise ValueError("Formato de archivo no permitido.")
    filename = f"{uuid.uuid4().hex}{extension}"
    destination = STORAGE / filename
    destination.write_bytes(uploaded_file.getvalue())
    return str(destination)


def get_all_products():
    with sqlite3.connect(DATABASE) as con:
        return con.execute(
            "SELECT * FROM products ORDER BY id DESC"
        ).fetchall()


def show_admin():
    try:
        admin_password = st.secrets.get("admin_password", "")
    except Exception:
        admin_password = ""

    if not admin_password:
        admin_password = os.getenv("MEDSIMPLIFY_ADMIN_PASSWORD", "")
    st.title("⚙️ Administración de MedSimplify")
    st.caption("Panel privado para gestionar los documentos de tu tienda.")

    if not admin_password:
        st.error(
            "Falta configurar la contraseña. Crea "
            ".streamlit/secrets.toml y agrega: "
            'admin_password = "TU_CONTRASEÑA".'
        )
        st.info("No coloques tu contraseña directamente dentro de app.py.")
        return

    if not st.session_state.get("admin_authenticated", False):
        st.subheader("Acceso de administradora")
        with st.form("admin_login_form"):
            entered_password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button(
                "Iniciar sesión", use_container_width=True
            )
        if submitted:
            if hmac.compare_digest(entered_password, admin_password):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        return

    left, right = st.columns([4, 1])
    left.success("Sesión de administración iniciada")
    if right.button("Cerrar sesión", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.rerun()

    products = get_all_products()
    active = sum(1 for p in products if p[7] == 1)
    archived = len(products) - active
    m1, m2, m3 = st.columns(3)
    m1.metric("Productos registrados", len(products))
    m2.metric("Productos publicados", active)
    m3.metric("Productos archivados", archived)

    add_tab, manage_tab = st.tabs(["＋ Subir producto", "▦ Gestionar productos"])

    with add_tab:
        st.subheader("Agregar un nuevo producto")
        with st.form("add_product_form", clear_on_submit=True):
            title = st.text_input("Nombre del producto")
            category = st.selectbox("Categoría", CATEGORIES)
            description = st.text_area("Descripción")
            price = st.number_input(
                "Precio en USD", min_value=0.0, value=1.0,
                step=0.5, format="%.2f"
            )
            image_file = st.file_uploader(
                "Portada (opcional)", type=["png", "jpg", "jpeg", "webp"]
            )
            pdf_file = st.file_uploader("Documento PDF", type=["pdf"])
            publish = st.checkbox("Publicar inmediatamente", value=True)
            submitted = st.form_submit_button(
                "Guardar producto", use_container_width=True
            )

        if submitted:
            if not title.strip() or not description.strip():
                st.error("Completa el nombre y la descripción.")
            elif pdf_file is None:
                st.error("Selecciona el documento PDF.")
            else:
                try:
                    image_path = save_uploaded_file(
                        image_file, {".png", ".jpg", ".jpeg", ".webp"}
                    )
                    pdf_path = save_uploaded_file(pdf_file, {".pdf"})
                    with sqlite3.connect(DATABASE) as con:
                        con.execute(
                            """INSERT INTO products
                            (title, category, description, price,
                             image_path, pdf_path, active)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (title.strip(), category, description.strip(),
                             float(price), image_path, pdf_path,
                             1 if publish else 0)
                        )
                        con.commit()
                    st.success("Producto guardado correctamente.")
                    st.rerun()
                except Exception as error:
                    st.error(f"No se pudo guardar el producto: {error}")

    with manage_tab:
        st.subheader("Productos registrados")
        products = get_all_products()
        if not products:
            st.info("Todavía no has agregado productos.")
        else:
            options = {
                f"#{p[0]} · {p[1]} ({'Publicado' if p[7] == 1 else 'Archivado'})": p
                for p in products
            }
            selected_label = st.selectbox(
                "Selecciona un producto", list(options.keys())
            )
            selected = options[selected_label]
            product_id = selected[0]

            with st.form(f"edit_product_{product_id}"):
                edit_title = st.text_input("Nombre", value=selected[1] or "")
                cat_index = CATEGORIES.index(selected[2]) if selected[2] in CATEGORIES else 0
                edit_category = st.selectbox(
                    "Categoría", CATEGORIES, index=cat_index
                )
                edit_description = st.text_area(
                    "Descripción", value=selected[3] or ""
                )
                edit_price = st.number_input(
                    "Precio en USD", min_value=0.0,
                    value=float(selected[4] or 0), step=0.5,
                    format="%.2f"
                )
                new_image = st.file_uploader(
                    "Cambiar portada (opcional)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"image_{product_id}"
                )
                new_pdf = st.file_uploader(
                    "Reemplazar PDF (opcional)", type=["pdf"],
                    key=f"pdf_{product_id}"
                )
                is_active = st.checkbox(
                    "Producto visible en la tienda",
                    value=bool(selected[7])
                )
                save = st.form_submit_button(
                    "Guardar cambios", use_container_width=True
                )

            if save:
                if not edit_title.strip() or not edit_description.strip():
                    st.error("El nombre y la descripción son obligatorios.")
                else:
                    try:
                        image_path = selected[5]
                        pdf_path = selected[6]
                        if new_image is not None:
                            image_path = save_uploaded_file(
                                new_image, {".png", ".jpg", ".jpeg", ".webp"}
                            )
                        if new_pdf is not None:
                            pdf_path = save_uploaded_file(new_pdf, {".pdf"})
                        with sqlite3.connect(DATABASE) as con:
                            con.execute(
                                """UPDATE products
                                SET title=?, category=?, description=?, price=?,
                                    image_path=?, pdf_path=?, active=?
                                WHERE id=?""",
                                (edit_title.strip(), edit_category,
                                 edit_description.strip(), float(edit_price),
                                 image_path, pdf_path, 1 if is_active else 0,
                                 product_id)
                            )
                            con.commit()
                        st.success("Cambios guardados.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"No se pudieron guardar los cambios: {error}")

            st.caption(
                "Para retirar un producto de la tienda, desmarca "
                "'Producto visible en la tienda' y guarda los cambios. "
                "El registro se conserva en la base de datos."
            )


# 15. CONTROL PRINCIPAL DE PAGINAS
# ==================================================

page = st.session_state.page

if page == "Inicio":

    show_home()

elif page == "Categorías":

    internal_header()
    show_categories()

elif page == "Productos":

    internal_header()
    show_products()

elif page == "Detalle":

    internal_header()
    show_product_detail()

elif page == "Contáctanos":

    internal_header()
    show_contact()

elif page == "Tus compras":

    internal_header()
    show_purchases()

elif page == "Mi cuenta":

    internal_header()
    show_account()

elif page == "Administración":

    show_admin()


# ==================================================
# 16. PIE DE PAGINA
# ==================================================

st.markdown("""
<div class="footer">
    <b>MedSimplify</b><br>
    Fast learning · Real understanding<br>
    El conocimiento transforma. Comprenderlo
    lo hace extraordinario.<br><br>
    © 2026 MedSimplify. Todos los derechos reservados.
</div>
""", unsafe_allow_html=True)
