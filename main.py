import streamlit as st
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# Import the models
from db_setup import User, Store, Product, Order, Category

# --- Database Connection managed by Streamlit ---
conn = st.connection("marketplace_db", type="sql")


# --- Password Hashing & Session State (unchanged) ---
def set_password(password):
    return generate_password_hash(password)


def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.cart = []


# --- show_login_signup (unchanged) ---
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


# --- show_marketplace (unchanged) ---
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

            categories = selected_store.categories
            category_names = ["All"] + [c.name for c in categories]
            selected_category_name = st.radio("Filter by Category:", category_names, horizontal=True)

            if selected_category_name == "All":
                products_to_display = selected_store.products
            else:
                selected_category = next(c for c in categories if c.name == selected_category_name)
                products_to_display = [p for p in selected_store.products if p.category_id == selected_category.id]

            if not products_to_display:
                st.write("This category has no products yet.")
            else:
                for product in products_to_display:
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        st.subheader(product.name)
                        st.write(product.description)
                    with col2:
                        st.write(f"${product.price:,}")
                    with col3:
                        quantity_to_buy = st.number_input("Quantity", min_value=1, key=f"qty_{product.id}", step=1)
                        if st.button("Add to Cart", key=f"add_{product.id}"):
                            st.session_state.cart.append(
                                {'product_id': product.id, 'name': product.name, 'quantity': quantity_to_buy,
                                 'price': product.price})
                            st.success(f"Added {quantity_to_buy} of {product.name} to your cart.")


# --- show_my_store (unchanged) ---
def show_my_store():
    st.title("My Store")
    with conn.session as session:
        user_store = session.query(Store).filter_by(user_id=st.session_state.user_id).first()
        if not user_store:
            st.info("You don't have a store yet. Create one below!")
            with st.form("create_store_form"):
                store_name = st.text_input("Your New Store Name")
                if st.form_submit_button("Create Store"):
                    new_store = Store(name=store_name, user_id=st.session_state.user_id)
                    session.add(new_store)
                    session.commit()
                    st.success(f"Your store '{store_name}' has been created!")
                    st.rerun()
        else:
            st.header(f"Manage Your Store: {user_store.name}")
            with st.expander("Manage Categories"):
                st.subheader("Add a Category")
                with st.form("add_category_form", clear_on_submit=True):
                    category_name = st.text_input("New Category Name")
                    if st.form_submit_button("Add Category"):
                        new_category = Category(name=category_name, store_id=user_store.id)
                        session.add(new_category)
                        session.commit()
                        st.success(f"Category '{category_name}' added.")
                        st.rerun()
                st.subheader("Existing Categories")
                categories = user_store.categories
                if not categories:
                    st.write("You have no categories yet.")
                for category in categories:
                    c1, c2 = st.columns([3, 1])
                    c1.write(category.name)
                    if c2.button("Delete", key=f"del_cat_{category.id}"):
                        session.delete(category)
                        session.commit()
                        st.rerun()
            categories = user_store.categories
            category_map = {cat.name: cat.id for cat in categories}
            category_names = ["Uncategorized"] + list(category_map.keys())
            with st.expander("Add a New Product"):
                with st.form("add_product_form", clear_on_submit=True):
                    product_name = st.text_input("Product Name")
                    product_desc = st.text_area("Product Description")
                    product_price = st.number_input("Price ($)", min_value=1, step=1, format="%d")
                    chosen_category_name = st.selectbox("Category", options=category_names)
                    if st.form_submit_button("Add Product"):
                        cat_id = category_map.get(chosen_category_name)
                        new_product = Product(name=product_name, description=product_desc, price=product_price,
                                              store_id=user_store.id, category_id=cat_id)
                        session.add(new_product)
                        session.commit()
                        st.rerun()
            st.markdown("---")
            st.header("Manage Existing Products")
            products = user_store.products
            if not products:
                st.write("You haven't added any products yet.")
            else:
                product_names = ["<Select a Product>"] + [p.name for p in products]
                selected_product_name = st.selectbox("Select a product to edit or delete", options=product_names,
                                                     index=0)
                selected_product = next((p for p in products if p.name == selected_product_name), None)
                if selected_product:
                    current_cat_name = "Uncategorized"
                    if selected_product.category_id:
                        current_cat_name = next(
                            (name for name, id in category_map.items() if id == selected_product.category_id),
                            "Uncategorized")
                    with st.form(key=f"edit_form_{selected_product.id}"):
                        st.subheader(f"Editing: {selected_product.name}")
                        new_name = st.text_input("Product Name", value=selected_product.name)
                        new_desc = st.text_area("Description", value=selected_product.description)
                        new_price = st.number_input("Price ($)", min_value=1, step=1, format="%d",
                                                    value=selected_product.price)
                        edited_cat_name = st.selectbox("Category", options=category_names,
                                                       index=category_names.index(current_cat_name))
                        if st.form_submit_button("Save Changes"):
                            product_to_update = session.query(Product).get(selected_product.id)
                            product_to_update.name = new_name
                            product_to_update.description = new_desc
                            product_to_update.price = new_price
                            product_to_update.category_id = category_map.get(edited_cat_name)
                            session.commit()
                            st.rerun()
                    st.markdown("---")
                    st.subheader("Delete Product")
                    st.warning(f"**Warning:** This will permanently delete **{selected_product.name}**.")
                    if st.button("DELETE THIS PRODUCT", key=f"delete_{selected_product.id}", type="primary"):
                        product_to_delete = session.query(Product).get(selected_product.id)
                        session.delete(product_to_delete)
                        session.commit()
                        st.rerun()


# --- NEW FUNCTION: show_store_sales ---
def show_store_sales():
    st.title("Store Sales History")
    with conn.session as session:
        # First, find the current user's store
        user_store = session.query(Store).filter_by(user_id=st.session_state.user_id).first()

        if not user_store:
            st.info("You must create a store before you can view sales.")
            return

        # Query to get all sales for products in the user's store
        sales = session.query(
            Order.timestamp,
            User.username,  # The buyer's username
            Product.name,  # The product name
            Order.quantity_purchased,
            Order.total_price
        ).join(
            Product, Order.product_id == Product.id  # Join Order to Product
        ).join(
            User, Order.user_id == User.id  # Join Order to User (the buyer)
        ).filter(
            Product.store_id == user_store.id  # Filter for products in our store
        ).order_by(
            Order.timestamp.desc()  # Show most recent first
        ).all()

        if not sales:
            st.info("Your store has not made any sales yet.")
            return

        for sale in sales:
            st.markdown("---")
            st.subheader(f"Sale on {sale.timestamp.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Buyer:** {sale.username}")
            st.write(f"**Product:** {sale.name}")
            st.write(f"**Quantity:** {sale.quantity_purchased}")
            st.write(f"**Total Price:** ${sale.total_price:,}")


# --- show_cart & show_my_orders (unchanged) ---
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
        with conn.session as session:
            try:
                for item in st.session_state.cart:
                    new_order = Order(user_id=st.session_state.user_id, product_id=item['product_id'],
                                      quantity_purchased=item['quantity'], total_price=item['quantity'] * item['price'])
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
                st.write(
                    f"**Order #{order.id}** - {order.timestamp.strftime('%Y-%m-%d %H:%M')}: {order.quantity_purchased} x **{product.name}** for ${order.total_price:,}")


# --- Main App Logic (MODIFIED) ---
if not st.session_state.logged_in:
    show_login_signup()
else:
    st.sidebar.title(f"Welcome, {st.session_state.username}")

    # MODIFIED: Added "Store Sales" to the navigation options
    app_mode = st.sidebar.radio(
        "Navigate",
        ["Marketplace", "My Store", "Store Sales", "My Orders", "Shopping Cart"]
    )

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
    # MODIFIED: Added the elif block to call the new function
    elif app_mode == "Store Sales":
        show_store_sales()
    elif app_mode == "Shopping Cart":
        show_cart()
    elif app_mode == "My Orders":
        show_my_orders()