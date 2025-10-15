import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash
from db_setup import User, Store, Product, Order

conn = st.connection("marketplace_db", type="sql")


def set_password(password):
    return generate_password_hash(password)


def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.cart = []


def show_login_signup():
    st.title("Welcome to the Armory Exchange!")
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login Section")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                with conn.session as session:
                    user = session.query(User).filter_by(username=username).first()
                if user and check_password(user.password_hash, password):
                    st.success(f"Welcome back, {username}!")
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    elif choice == "Sign Up":
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                with conn.session as session:
                    existing_user = session.query(User).filter_by(username=new_username).first()
                    if existing_user:
                        st.warning("Username already exists.")
                    else:
                        hashed_password = set_password(new_password)
                        new_user = User(username=new_username, password_hash=hashed_password)
                        session.add(new_user)
                        session.commit()
                        st.success("Account created! Please login.")


def show_marketplace():
    st.title("Marketplace")
    with conn.session as session:
        stores = session.query(Store).all()
        if not stores:
            st.info("There are no stores available yet.")
            return

        store_names = [store.name for store in stores]
        selected_store_name = st.selectbox("Select a store to browse:", store_names)

        if selected_store_name:
            selected_store = session.query(Store).filter_by(name=selected_store_name).first()
            st.header(f"Products in {selected_store.name}")
            products = selected_store.products
            if not products:
                st.write("This store has no products yet.")
            else:
                for product in products:
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        st.subheader(product.name)
                        st.write(product.description)
                    with col2:
                        st.write(f"${product.price:,}")
                    with col3:
                        quantity_to_buy = st.number_input("Quantity", min_value=1, key=f"qty_{product.id}", step=1)
                        if st.button("Add to Cart", key=f"add_{product.id}"):
                            st.session_state.cart.append({'product_id': product.id, 'name': product.name, 'quantity': quantity_to_buy, 'price': product.price})
                            st.success(f"Added {quantity_to_buy} of {product.name} to your cart.")


def show_my_store():
    st.title("My Store")
    with conn.session as session:
        user_store = session.query(Store).filter_by(user_id=st.session_state.user_id).first()
        if not user_store:
            st.info("You don't have a store yet. Create one below!")
            with st.form("create_store_form"):
                store_name = st.text_input("Your New Store Name")
                submitted = st.form_submit_button("Create Store")
                if submitted:
                    new_store = Store(name=store_name, user_id=st.session_state.user_id)
                    session.add(new_store)
                    session.commit()
                    st.success(f"Your store '{store_name}' has been created!")
                    st.rerun()
        else:
            st.header(f"Manage Your Store: {user_store.name}")
            with st.expander("Add a New Product"):
                with st.form("add_product_form", clear_on_submit=True):
                    product_name = st.text_input("Product Name")
                    product_desc = st.text_area("Product Description")
                    product_price = st.number_input("Price ($)", min_value=1, step=1, format="%d")
                    submitted = st.form_submit_button("Add Product")
                    if submitted:
                        new_product = Product(name=product_name, description=product_desc, price=product_price, store_id=user_store.id)
                        session.add(new_product)
                        session.commit()
                        st.success(f"Added '{product_name}' to your store.")
                        st.rerun()
            st.markdown("---")
            st.header("Manage Existing Products")
            products = user_store.products
            if not products:
                st.write("You haven't added any products yet.")
            else:
                product_names = [p.name for p in products]
                product_names.insert(0, "<Select a Product>")
                selected_product_name = st.selectbox("Select a product to edit or delete", options=product_names, index=0)
                selected_product = next((p for p in products if p.name == selected_product_name), None)
                if selected_product:
                    with st.form(key=f"edit_form_{selected_product.id}"):
                        st.subheader(f"Editing: {selected_product.name}")
                        new_name = st.text_input("Product Name", value=selected_product.name)
                        new_desc = st.text_area("Description", value=selected_product.description)
                        new_price = st.number_input("Price ($)", min_value=1, step=1, format="%d", value=selected_product.price)
                        if st.form_submit_button("Save Changes"):
                            product_to_update = session.query(Product).get(selected_product.id)
                            product_to_update.name = new_name
                            product_to_update.description = new_desc
                            product_to_update.price = new_price
                            session.commit()
                            st.success(f"Successfully updated '{new_name}'.")
                            st.rerun()
                    st.markdown("---")
                    st.subheader("Delete Product")
                    st.warning(f"**Warning:** This will permanently delete **{selected_product.name}**.")
                    if st.button("DELETE THIS PRODUCT", key=f"delete_{selected_product.id}", type="primary"):
                        product_to_delete = session.query(Product).get(selected_product.id)
                        session.delete(product_to_delete)
                        session.commit()
                        st.success(f"Successfully deleted {selected_product.name}.")
                        st.rerun()


def show_cart():
    st.title("Your Shopping Cart")
    if not st.session_state.cart:
        st.info("Your cart is empty.")
        return
    total_price = 0
    for i, item in enumerate(st.session_state.cart):
        st.write(f"{item['quantity']} x **{item['name']}** @ ${item['price']:,} each")
        total_price += item['quantity'] * item['price']
        if st.button("Remove", key=f"remove_{i}"):
            st.session_state.cart.pop(i)
            st.rerun()
    st.markdown("---")
    st.header(f"Total: ${total_price:,}")
    if st.button("Checkout", use_container_width=True):
        # MODIFIED
        with conn.session as session:
            try:
                for item in st.session_state.cart:
                    new_order = Order(user_id=st.session_state.user_id, product_id=item['product_id'], quantity_purchased=item['quantity'], total_price=item['quantity'] * item['price'])
                    session.add(new_order)
                session.commit()
                st.success("Purchase successful! Your order has been placed.")
                st.session_state.cart = []
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"An error occurred: {e}")


def show_my_orders():
    st.title("My Past Orders")
    with conn.session as session:
        orders = session.query(Order).filter_by(user_id=st.session_state.user_id).order_by(Order.timestamp.desc()).all()
        if not orders:
            st.info("You haven't placed any orders yet.")
        else:
            for order in orders:
                product = session.query(Product).get(order.product_id)
                st.write(f"**Order #{order.id}** - {order.timestamp.strftime('%Y-%m-%d %H:%M')}: {order.quantity_purchased} x **{product.name}** for ${order.total_price:,}")


if not st.session_state.logged_in:
    show_login_signup()
else:
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    app_mode = st.sidebar.radio("Navigate", ["Marketplace", "My Store", "My Orders", "Shopping Cart"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.cart = []
        st.rerun()
    if app_mode == "Marketplace":
        show_marketplace()
    elif app_mode == "My Store":
        show_my_store()
    elif app_mode == "Shopping Cart":
        show_cart()
    elif app_mode == "My Orders":
        show_my_orders()
