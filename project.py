import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


import warnings

warnings.simplefilter(action='ignore', category=UserWarning)


current_mode = None
current_entries = {}
tree = None
chart_canvas = None
chart_container = None


current_value_lbl = None
invested_value_lbl = None
returns_lbl = None
market_cap_lbl = None
pe_lbl = None
bv_lbl = None

BG = "#F0FDF4"
DARK = "#166534"
BTN_GREEN = "#166534"
BTN_BLUE = "#1d4ed8"
BTN_RED = "#8B0000"
BTN_TEAL = "#0f766e"
FRAME_3D = "#d1d5db"
PLACEHOLDER = "#9CA3AF"
BUTTON = "#22C55E"


def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="dellenter@06",
        database="judetrade_db", port=3306
    )



def fetch_client(client_id):
    conn = get_db_connection();
    cursor = conn.cursor()
    cursor.execute(
        "SELECT client_name, mobile, email, pan, demat_acc, depository, trading_acc, nominee, nominee_pan FROM client WHERE client_id = %s",
        (client_id,))
    row = cursor.fetchone();
    conn.close()
    return row


def fetch_stock(stock_id):
    conn = get_db_connection();
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stock_name, sector, current_price, high_price, low_price, face_value, outstanding_shares FROM stock WHERE stock_id = %s",
        (stock_id,))
    row = cursor.fetchone();
    conn.close()
    return row


def get_portfolio_data(client_id):
    conn = get_db_connection()
    query = """SELECT h.stock_id, s.stock_name, s.sector, h.quantity, h.avg_buy_price, s.current_price 
               FROM holdings h JOIN stock s ON h.stock_id = s.stock_id WHERE h.client_id = %s"""
    df = pd.read_sql(query, conn, params=(client_id,));
    conn.close()
    return df


def validate_fields(field_names):
    for f in field_names:
        if not current_entries[f].get() or str(current_entries[f].get()).strip() == "": return False
    return True


def record_exists(table, key, val):
    conn = get_db_connection();
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {key}=%s", (val,))
    exists = cur.fetchone()[0] > 0;
    conn.close()
    return exists


def client_has_holdings(cid):
    conn = get_db_connection();
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM holdings WHERE client_id = %s", (cid,))
    count = cur.fetchone()[0];
    conn.close()
    return count > 0



def draw_sector_pie_chart(client_id, parent_frame):
    global chart_canvas
    if chart_canvas: chart_canvas.get_tk_widget().destroy(); chart_canvas = None
    for w in parent_frame.winfo_children(): w.destroy()

    df = get_portfolio_data(client_id)
    if df.empty:
        tk.Label(parent_frame, text="No Investments Yet", bg=BG, font=("Arial", 12)).pack(pady=50)
        return

    df['total_value'] = df['quantity'] * df['current_price']
    sector_data = df.groupby('sector')['total_value'].sum()

    fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
    fig.patch.set_facecolor(BG)
    wedges, texts, autotexts = ax.pie(sector_data, labels=sector_data.index, autopct='%1.1f%%',
                                      startangle=90, colors=['#22c55e', '#3b82f6', '#eab308', '#ef4444', '#a855f7'],
                                      textprops={'fontsize': 9})
    ax.set_title("Portfolio Allocation", fontsize=10, fontweight='bold')
    plt.tight_layout()

    chart_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill="both", expand=True)


def draw_stock_price_chart(stock_id, parent_frame):
    global chart_canvas
    if chart_canvas: chart_canvas.get_tk_widget().destroy(); chart_canvas = None
    for w in parent_frame.winfo_children(): w.destroy()

    data = fetch_stock(stock_id)
    if not data: return

    prices = [float(data[4]), float(data[2]), float(data[3])]  # Low, Current, High
    labels = ["Low", "Current", "High"]
    colors = ["#ef4444", "#3b82f6", "#22c55e"]

    fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.bar(labels, prices, color=colors, width=0.5)
    ax.set_title(f"Price Range: {data[0]}", fontsize=10, fontweight='bold')
    ax.set_ylabel("Price (₹)")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height, f'₹{int(height)}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    chart_canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill="both", expand=True)


def calculate_portfolio_metrics(client_id):
    df = get_portfolio_data(client_id)
    if df.empty:
        current_value_lbl.config(text="Current Value : ₹ 0")
        invested_value_lbl.config(text="Invested Value : ₹ 0")
        returns_lbl.config(text="Total Returns : ₹ 0")
        return

    curr = (df['quantity'] * df['current_price']).sum()
    inv = (df['quantity'] * df['avg_buy_price']).sum()
    ret = curr - inv
    color = "green" if ret >= 0 else "red"

    current_value_lbl.config(text=f"Current Value : ₹ {curr:,.2f}")
    invested_value_lbl.config(text=f"Invested Value : ₹ {inv:,.2f}")
    returns_lbl.config(text=f"Total Returns : ₹ {ret:,.2f}", fg=color)



def open_main_window():
    global tree, chart_container

    # Create NEW Main Window
    main = tk.Tk()
    main.title("JUDETRADE – Brokerage Management System")
    main.state("zoomed")
    main.configure(bg=BG)


    header = tk.Frame(main, bg=DARK, bd=8, relief="ridge")
    header.pack(side="top", fill="x")
    try:
        img = Image.open(r"c:\users\DELL\Desktop\Intern\logo.png")
        img = img.resize((450, 130))
        logo = ImageTk.PhotoImage(img)
        tk.Label(header, image=logo, bg=BG).pack(pady=10)
        header.image = logo
    except:
        tk.Label(header, text="JUDETRADE", font=("Arial", 20, "bold"), fg="white", bg=DARK).pack(pady=20)


    container = tk.Frame(main, bg=FRAME_3D, bd=8, relief="ridge")
    container.pack(fill="both", expand=True, padx=10, pady=5)

    left_panel = tk.LabelFrame(container, text="Details", font=("Arial", 12, "bold"), bg=BG, bd=6, relief="ridge")
    left_panel.place(x=10, y=10, width=900, height=420)

    right_panel = tk.LabelFrame(container, text="Portfolio / Analysis", font=("Arial", 12, "bold"), bg=BG, bd=6,
                                relief="ridge")
    right_panel.place(x=920, y=10, width=580, height=420)

    button_frame = tk.Frame(container, bg=FRAME_3D, bd=6, relief="ridge")
    button_frame.place(x=10, y=440, width=1490, height=70)


    table_frame = tk.Frame(container, bg=FRAME_3D, bd=6, relief="ridge")
    table_frame.place(x=10, y=520, width=1490, height=240)
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    global tree
    tree = ttk.Treeview(table_frame, show="headings", selectmode="browse")
    tree.grid(row=0, column=0, sticky="nsew")
    scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scroll_y.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scroll_y.set)


    def load_client_and_portfolio(entry_widgets):
        cid = entry_widgets["Client ID"].get()
        if not cid: return
        data = fetch_client(cid)
        if data:
            fields = ["Client Name", "Mobile", "Email", "PAN", "Demat Acc", "Depository", "Trading Acc", "Nominee",
                      "Nominee PAN"]
            for i, val in enumerate(data):
                entry_widgets[fields[i]].delete(0, tk.END);
                entry_widgets[fields[i]].insert(0, val)
        calculate_portfolio_metrics(cid)
        draw_sector_pie_chart(cid, chart_container)

    def load_stock_details(entry_widgets):
        sid = entry_widgets["Stock ID"].get()
        if not sid: return
        data = fetch_stock(sid)
        if data:
            vals = list(data)
            keys = ["Stock Name", "Sector", "Current Price", "High Price", "Low Price", "Face Value",
                    "Outstanding Shares"]
            for i, k in enumerate(keys):
                if k == "Sector":
                    entry_widgets[k].set(vals[i])
                else:
                    entry_widgets[k].delete(0, tk.END); entry_widgets[k].insert(0, vals[i])

            price, shares, face = float(vals[2]), int(vals[6]), float(vals[5])
            market_cap_lbl.config(text=f"Market Cap : ₹ {price * shares:,.2f}")
            bv_lbl.config(text=f"Book Value : ₹ {face * shares:,.2f}")
            eps = face * 0.15
            pe = price / eps if eps != 0 else 0
            pe_lbl.config(text=f"P/E Ratio : {pe:.2f}")

            draw_stock_price_chart(sid, chart_container)

    def on_tree_select(event):
        sel = tree.selection()
        if not sel: return
        pid = tree.item(sel)['values'][0]
        if current_mode == "CLIENT":
            global current_entries
            current_entries["Client ID"].delete(0, tk.END);
            current_entries["Client ID"].insert(0, pid)
            load_client_and_portfolio(current_entries)
        elif current_mode == "STOCK":
            current_entries["Stock ID"].delete(0, tk.END);
            current_entries["Stock ID"].insert(0, pid)
            load_stock_details(current_entries)

    tree.bind("<<TreeviewSelect>>", on_tree_select)


    def load_client_form():
        global current_mode, current_entries, current_value_lbl, invested_value_lbl, returns_lbl, chart_container
        current_mode = "CLIENT"


        for w in right_panel.winfo_children(): w.destroy()
        chart_container = tk.Frame(right_panel, bg=BG)
        chart_container.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(chart_container, text="Select a Client to view Portfolio Chart", bg=BG, fg=PLACEHOLDER).pack(pady=50)


        left_panel.config(text="Client Details")
        for w in left_panel.winfo_children(): w.destroy()
        current_entries = {}

        fields = ["Client ID", "Client Name", "Mobile", "Email", "PAN", "Demat Acc", "Depository", "Trading Acc",
                  "Nominee", "Nominee PAN"]
        for i, f in enumerate(fields):
            tk.Label(left_panel, text=f, bg=BG, font=("Arial", 11, "bold")).grid(row=i, column=0, sticky="w", pady=6,
                                                                                 padx=10)
            if f == "Depository":
                cb = ttk.Combobox(left_panel, values=["NSDL", "CDSL"], state="readonly", width=28)
                cb.grid(row=i, column=1, pady=6);
                current_entries[f] = cb
            else:
                e = tk.Entry(left_panel, width=30)
                e.grid(row=i, column=1, pady=6);
                current_entries[f] = e
                if f == "Client ID": e.bind("<KeyRelease>", lambda e: load_client_and_portfolio(current_entries))

        tk.Label(left_panel, text="Portfolio Summary", font=("Arial", 13, "bold"), fg=DARK, bg=BG).grid(row=0, column=2,
                                                                                                        padx=40,
                                                                                                        sticky="w")
        current_value_lbl = tk.Label(left_panel, text="Current Value : ₹ --", font=("Arial", 11), bg=BG)
        current_value_lbl.grid(row=1, column=2, padx=40, sticky="w")
        invested_value_lbl = tk.Label(left_panel, text="Invested Value : ₹ --", font=("Arial", 11), bg=BG)
        invested_value_lbl.grid(row=2, column=2, padx=40, sticky="w")
        returns_lbl = tk.Label(left_panel, text="Total Returns : ₹ --", font=("Arial", 11), bg=BG)
        returns_lbl.grid(row=3, column=2, padx=40, sticky="w")

    def load_stock_form():
        global current_mode, current_entries, market_cap_lbl, pe_lbl, bv_lbl, chart_container
        current_mode = "STOCK"

        for w in right_panel.winfo_children(): w.destroy()
        chart_container = tk.Frame(right_panel, bg=BG)
        chart_container.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(chart_container, text="Select a Stock to view Price Range", bg=BG, fg=PLACEHOLDER).pack(pady=50)

        left_panel.config(text="Stock Details")
        for w in left_panel.winfo_children(): w.destroy()
        current_entries = {}

        fields = ["Stock ID", "Stock Name", "Sector", "Current Price", "High Price", "Low Price", "Face Value",
                  "Outstanding Shares"]
        for i, f in enumerate(fields):
            tk.Label(left_panel, text=f, bg=BG, font=("Arial", 11, "bold")).grid(row=i, column=0, sticky="w", pady=6,
                                                                                 padx=10)
            if f == "Sector":
                cb = ttk.Combobox(left_panel,
                                  values=["IT", "Banking", "Finance", "Pharma", "FMCG", "Energy", "Automobile"],
                                  state="readonly", width=28)
                cb.grid(row=i, column=1, pady=6);
                current_entries[f] = cb
            else:
                e = tk.Entry(left_panel, width=30)
                e.grid(row=i, column=1, pady=6);
                current_entries[f] = e
                if f == "Stock ID": e.bind("<KeyRelease>", lambda e: load_stock_details(current_entries))

        tk.Label(left_panel, text="Stock Metrics", font=("Arial", 13, "bold"), fg=DARK, bg=BG).grid(row=0, column=2,
                                                                                                    padx=40, sticky="w")
        market_cap_lbl = tk.Label(left_panel, text="Market Cap : ₹ --", font=("Arial", 11), bg=BG);
        market_cap_lbl.grid(row=1, column=2, padx=40, sticky="w")
        pe_lbl = tk.Label(left_panel, text="P/E Ratio : --", font=("Arial", 11), bg=BG);
        pe_lbl.grid(row=2, column=2, padx=40, sticky="w")
        bv_lbl = tk.Label(left_panel, text="Book Value : ₹ --", font=("Arial", 11), bg=BG);
        bv_lbl.grid(row=3, column=2, padx=40, sticky="w")


    def load_clients_tree():
        for i in tree.get_children(): tree.delete(i)
        cols = ("Client ID", "Client Name", "Mobile", "Email", "PAN", "Depository", "Wallet Balance")
        tree["columns"] = cols
        for col in cols: tree.heading(col, text=col); tree.column(col, anchor="center", width=200)
        conn = get_db_connection();
        cur = conn.cursor()
        cur.execute("SELECT client_id, client_name, mobile, email, pan, depository, wallet_balance FROM client")
        for r in cur.fetchall(): tree.insert("", "end", values=r)
        conn.close()

    def load_stocks_tree():
        for i in tree.get_children(): tree.delete(i)
        cols = ("Stock ID", "Stock Name", "Sector", "Current Price", "High", "Low")
        tree["columns"] = cols
        for col in cols: tree.heading(col, text=col); tree.column(col, anchor="center", width=220)
        conn = get_db_connection();
        cur = conn.cursor()
        cur.execute("SELECT stock_id, stock_name, sector, current_price, high_price, low_price FROM stock")
        for r in cur.fetchall(): tree.insert("", "end", values=r)
        conn.close()


    def add_rec():
        if current_mode == "CLIENT":
            req = ["Client ID", "Client Name", "Mobile", "Email", "PAN", "Demat Acc", "Depository", "Trading Acc",
                   "Nominee", "Nominee PAN"]
            if not validate_fields(req): messagebox.showwarning("Missing", "Fill all fields"); return
            cid = current_entries["Client ID"].get()
            if record_exists("client", "client_id", cid): messagebox.showerror("Error", "ID Exists"); return
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO client (client_id, client_name, mobile, email, pan, demat_acc, depository, trading_acc, nominee, nominee_pan, wallet_balance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)",
                (cid, current_entries["Client Name"].get(), current_entries["Mobile"].get(),
                 current_entries["Email"].get(), current_entries["PAN"].get(), current_entries["Demat Acc"].get(),
                 current_entries["Depository"].get(), current_entries["Trading Acc"].get(),
                 current_entries["Nominee"].get(), current_entries["Nominee PAN"].get()))
            conn.commit();
            conn.close();
            messagebox.showinfo("Success", "Added");
            load_clients_tree()
        elif current_mode == "STOCK":
            req = ["Stock ID", "Stock Name", "Sector", "Current Price", "High Price", "Low Price", "Face Value",
                   "Outstanding Shares"]
            if not validate_fields(req): messagebox.showwarning("Missing", "Fill all fields"); return
            sid = current_entries["Stock ID"].get()
            if record_exists("stock", "stock_id", sid): messagebox.showerror("Error", "ID Exists"); return
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO stock (stock_id, stock_name, sector, current_price, high_price, low_price, face_value, outstanding_shares) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (sid, current_entries["Stock Name"].get(), current_entries["Sector"].get(),
                 current_entries["Current Price"].get(), current_entries["High Price"].get(),
                 current_entries["Low Price"].get(), current_entries["Face Value"].get(),
                 current_entries["Outstanding Shares"].get()))
            conn.commit();
            conn.close();
            messagebox.showinfo("Success", "Added");
            load_stocks_tree()

    def update_rec():
        if current_mode == "CLIENT":
            cid = current_entries["Client ID"].get()
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute(
                "UPDATE client SET client_name=%s, mobile=%s, email=%s, pan=%s, demat_acc=%s, depository=%s, trading_acc=%s, nominee=%s, nominee_pan=%s WHERE client_id=%s",
                (current_entries["Client Name"].get(), current_entries["Mobile"].get(), current_entries["Email"].get(),
                 current_entries["PAN"].get(), current_entries["Demat Acc"].get(), current_entries["Depository"].get(),
                 current_entries["Trading Acc"].get(), current_entries["Nominee"].get(),
                 current_entries["Nominee PAN"].get(), cid))
            conn.commit();
            conn.close();
            messagebox.showinfo("Success", "Updated");
            load_clients_tree()
        elif current_mode == "STOCK":
            sid = current_entries["Stock ID"].get()
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute(
                "UPDATE stock SET stock_name=%s, sector=%s, current_price=%s, high_price=%s, low_price=%s, face_value=%s, outstanding_shares=%s WHERE stock_id=%s",
                (current_entries["Stock Name"].get(), current_entries["Sector"].get(),
                 current_entries["Current Price"].get(), current_entries["High Price"].get(),
                 current_entries["Low Price"].get(), current_entries["Face Value"].get(),
                 current_entries["Outstanding Shares"].get(), sid))
            conn.commit();
            conn.close();
            messagebox.showinfo("Success", "Updated");
            load_stocks_tree()

    def del_rec():
        if current_mode == "CLIENT":
            cid = current_entries["Client ID"].get()
            if client_has_holdings(cid): messagebox.showwarning("Stop", "Client has investments."); return
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute("DELETE FROM client WHERE client_id=%s", (cid,))
            conn.commit();
            conn.close();
            messagebox.showinfo("Deleted", "Client deleted");
            load_clients_tree()
        elif current_mode == "STOCK":
            sid = current_entries["Stock ID"].get()
            conn = get_db_connection();
            cur = conn.cursor()
            cur.execute("DELETE FROM stock WHERE stock_id=%s", (sid,))
            conn.commit();
            conn.close();
            messagebox.showinfo("Deleted", "Stock deleted");
            load_stocks_tree()

    def reset_f():
        for w in current_entries.values():
            if isinstance(w, ttk.Combobox):
                w.set("")
            else:
                w.delete(0, tk.END)

    for i in range(7): button_frame.grid_columnconfigure(i, weight=1)
    btn = {"font": ("Arial", 12, "bold"), "fg": "white", "height": 2}
    tk.Button(button_frame, text="👤 CLIENT", bg=BTN_TEAL, command=lambda: (load_client_form(), load_clients_tree()),
              **btn).grid(row=0, column=0, sticky="nsew", padx=5)
    tk.Button(button_frame, text="📈 STOCK", bg=BTN_BLUE, command=lambda: (load_stock_form(), load_stocks_tree()),
              **btn).grid(row=0, column=1, sticky="nsew", padx=5)
    tk.Button(button_frame, text="➕ ADD", bg=BTN_GREEN, command=add_rec, **btn).grid(row=0, column=2, sticky="nsew",
                                                                                     padx=5)
    tk.Button(button_frame, text="✏️ UPDATE", bg=BTN_GREEN, command=update_rec, **btn).grid(row=0, column=3,
                                                                                            sticky="nsew", padx=5)
    tk.Button(button_frame, text="🗑️ DELETE", bg=BTN_GREEN, command=del_rec, **btn).grid(row=0, column=4, sticky="nsew",
                                                                                         padx=5)
    tk.Button(button_frame, text="♻️ RESET", bg=BTN_GREEN, command=reset_f, **btn).grid(row=0, column=5, sticky="nsew",
                                                                                        padx=5)
    tk.Button(button_frame, text="⛔ EXIT", bg=BTN_RED, command=main.destroy, **btn).grid(row=0, column=6, sticky="nsew",
                                                                                         padx=5)

    load_client_form()
    main.mainloop()



root = tk.Tk()
root.title("Login")
root.state("zoomed")
root.configure(bg=BG)


def login():
    users = {"ezekiel06": "362506", "jenita03": "pass369"}
    if entry_user.get() in users and users[entry_user.get()] == entry_pass.get():
        messagebox.showinfo("Success", "Welcome Admin!")
        root.destroy()
        open_main_window()
    else:
        messagebox.showerror("Error", "Invalid login")


def clear_user(e):
    if entry_user.get() == "Username":
        entry_user.delete(0, tk.END)
        entry_user.config(fg=DARK)


def clear_pass(e):
    if entry_pass.get() == "Password":
        entry_pass.delete(0, tk.END)
        entry_pass.config(show="*", fg=DARK)


logo_frame = tk.Frame(root, bg=BG)
logo_frame.pack(pady=30)

try:
    img = Image.open(r"c:\users\DELL\Desktop\Intern\logo.png")
    img = img.resize((450, 450))
    logo = ImageTk.PhotoImage(img)
    tk.Label(logo_frame, image=logo, bg=BG).pack()
    logo_frame.image = logo
except:
    tk.Label(logo_frame, text="LOGO MISSING", bg=BG).pack()

login_frame = tk.Frame(root, bg=BG)
login_frame.place(relx=0.5, rely=0.5, anchor="center")

entry_user = tk.Entry(login_frame, width=30, font=("Inter", 14), fg=PLACEHOLDER)
entry_user.insert(0, "Username")
entry_user.bind("<FocusIn>", clear_user)
entry_user.pack(pady=8)

entry_pass = tk.Entry(login_frame, width=30, font=("Inter", 14), fg=PLACEHOLDER)
entry_pass.insert(0, "Password")
entry_pass.bind("<FocusIn>", clear_pass)
entry_pass.pack(pady=8)

tk.Button(
    login_frame, text="LOGIN", width=25, height=2,
    bg=BUTTON, fg="white",
    font=("Inter", 12, "bold"),
    command=login
).pack(pady=16)

root.mainloop()
