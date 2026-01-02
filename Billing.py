from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ================= DATABASE =================
def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="Billing"
    )
def get_engine():
    return create_engine(
        "mysql+mysqlconnector://root:12345@localhost/Billing"
    )
db = db_connect()
cur = db.cursor()

# ================= STYLES =================
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_HEAD = ("Segoe UI", 14, "bold")

BG_HEADER = "#0f172a"
BG_SIDEBAR = "#1e293b"
BG_CONTENT = "#f1f5f9"

BG_BUTTON = "#2563eb"
BTN_SUCCESS = "#16a34a"
BTN_DANGER = "#dc2626"
FG_WHITE = "white"


# ================= UTIL =================
def clear():
    for w in content.winfo_children():
        w.destroy()


def table(cols):
    tree = ttk.Treeview(content, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=160, anchor=CENTER)
    tree.pack(fill=BOTH, expand=True)
    return tree

def popup_form(title, fields, save_cmd):
    win = Toplevel(dash)
    win.title(title)
    win.geometry("350x350")

    Label(win, text=title, font=FONT_HEAD).pack(pady=10)
    entries = {}

    for f in fields:
        Label(win, text=f).pack()
        e = Entry(win)
        e.pack(pady=4)
        entries[f] = e

    Button(win, text="SAVE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: save_cmd(entries, win)
           ).pack(pady=15)

def crud_buttons(add, update, delete):
    f = Frame(content, bg=BG_CONTENT)
    f.pack(pady=10)

    Button(f, text="ADD", bg=BTN_SUCCESS,
           fg=FG_WHITE, font=FONT_HEAD,
           command=add).pack(side=LEFT, padx=10)

    Button(f, text="UPDATE", bg=BG_BUTTON,
           fg=FG_WHITE, font=FONT_HEAD,
           command=update).pack(side=LEFT, padx=10)

    Button(f, text="DELETE", bg=BTN_DANGER,
           fg=FG_WHITE, font=FONT_HEAD,
           command=delete).pack(side=LEFT, padx=10)

# ================= CUSTOMERS =================
def save_customer(e, w, mode):
    if mode == "add":
        cur.execute(
            "INSERT INTO customer VALUES (%s,%s,%s,%s)",
            (
                e["Customer ID"].get(),
                e["Name"].get(),
                e["Phone"].get(),
                e["Email"].get()
            )
        )

    elif mode == "update":
        cur.execute("""
            UPDATE customer
            SET customer_name=%s,
                phone=%s,
                email=%s
            WHERE customer_id=%s
        """, (
            e["Name"].get(),
            e["Phone"].get(),
            e["Email"].get(),
            e["Customer ID"].get()
        ))

    db.commit()
    w.destroy()
    customers()

def customers():
    clear()
    Label(content, text="Customers",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # 🔍 Search + Filter
    search_var = StringVar()
    filter_var = StringVar(value="All")

    top = Frame(content, bg=BG_CONTENT)
    top.pack(pady=5)

    Label(top, text="Search:", bg=BG_CONTENT).pack(side=LEFT)
    Entry(top, textvariable=search_var, width=25).pack(side=LEFT, padx=6)

    Label(top, text="Filter By:", bg=BG_CONTENT).pack(side=LEFT, padx=6)
    filter_cb = ttk.Combobox(
        top, textvariable=filter_var,
        state="readonly", width=15,
        values=["All", "ID", "Name", "Phone", "Email"]
    )
    filter_cb.pack(side=LEFT)

    tree = table(("ID", "Name", "Phone", "Email"))

    # ---------------------------
    # REFRESH FUNCTION
    # ---------------------------
    def refresh(*args):
        tree.delete(*tree.get_children())
        val = f"%{search_var.get()}%"
        f = filter_var.get()

        if f == "ID":
            q, p = "SELECT * FROM customer WHERE customer_id LIKE %s", (val,)
        elif f == "Name":
            q, p = "SELECT * FROM customer WHERE customer_name LIKE %s", (val,)
        elif f == "Phone":
            q, p = "SELECT * FROM customer WHERE phone LIKE %s", (val,)
        elif f == "Email":
            q, p = "SELECT * FROM customer WHERE email LIKE %s", (val,)
        else:
            q = """SELECT * FROM customer
                   WHERE customer_id LIKE %s
                      OR customer_name LIKE %s
                      OR phone LIKE %s
                      OR email LIKE %s"""
            p = (val, val, val, val)

        cur.execute(q, p)
        for r in cur.fetchall():
            tree.insert("", END, values=r)

    search_var.trace("w", refresh)
    filter_cb.bind("<<ComboboxSelected>>", refresh)

    refresh()

    # ---------------------------
    # DELETE FUNCTION (MOVE UP)
    # ---------------------------
    def delete_customer_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Select a customer to delete")
            return

        cid = tree.item(selected)["values"][0]

        if messagebox.askyesno("Confirm", "Delete selected customer?"):
            cur.execute("DELETE FROM customer WHERE customer_id=%s", (cid,))
            db.commit()
            refresh()

    # ---------------------------
    # FORM FUNCTION
    # ---------------------------
    def customer_form(mode):
        win = Toplevel(dash)
        win.title(mode.capitalize() + " Customer")
        win.geometry("350x350")

        entries = {}
        fields = ["Customer ID", "Name", "Phone", "Email"]

        for f in fields:
            Label(win, text=f).pack()
            e = Entry(win)
            e.pack(pady=4)
            entries[f] = e

        if mode == "update":
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select", "Select a customer first")
                win.destroy()
                return

            data = tree.item(selected)["values"]
            for f, v in zip(fields, data):
                entries[f].insert(0, v)

        Button(win, text="SAVE",
               bg=BG_BUTTON, fg=FG_WHITE,
               font=FONT_HEAD,
               command=lambda: save_customer(entries, win, mode)
               ).pack(pady=15)

    # ---------------------------
    # BUTTONS (NOW SAFE)
    # ---------------------------
    btn_frame = Frame(content, bg=BG_CONTENT)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="ADD",
           bg=BTN_SUCCESS, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: customer_form("add")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="UPDATE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: customer_form("update")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="DELETE",
           bg=BTN_DANGER, fg=FG_WHITE,
           font=FONT_HEAD,
           command=delete_customer_selected
           ).pack(side=LEFT, padx=10)


# ================= PRODUCTS =================
def save_product(e, w, mode):
    if mode == "add":
        cur.execute(
            "INSERT INTO product VALUES (%s,%s,%s,%s)",
            (
                e["ID"].get(),
                e["Name"].get(),
                e["Category"].get(),
                e["Price"].get()
            )
        )

    elif mode == "update":
        cur.execute("""
            UPDATE product
            SET product_name=%s,
                category=%s,
                price=%s
            WHERE product_id=%s
        """, (
            e["Name"].get(),
            e["Category"].get(),
            e["Price"].get(),
            e["ID"].get()
        ))

    db.commit()
    w.destroy()
    products()

def products():
    clear()
    Label(content, text="Products",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # 🔍 Search + Dropdown
    search_var = StringVar()
    filter_var = StringVar(value="All")

    top = Frame(content, bg=BG_CONTENT)
    top.pack(pady=5)

    Label(top, text="Search:", bg=BG_CONTENT).pack(side=LEFT)
    Entry(top, textvariable=search_var, width=25).pack(side=LEFT, padx=6)

    Label(top, text="Filter By:", bg=BG_CONTENT).pack(side=LEFT, padx=6)

    filter_cb = ttk.Combobox(
        top,
        textvariable=filter_var,
        state="readonly",
        width=15,
        values=["All", "ID", "Name", "Category"]
    )
    filter_cb.pack(side=LEFT)

    tree = table(("ID", "Name", "Category", "Price"))

    # ---------------------------
    # REFRESH
    # ---------------------------
    def refresh(*args):
        tree.delete(*tree.get_children())
        val = f"%{search_var.get()}%"
        f = filter_var.get()

        if f == "ID":
            q, p = "SELECT * FROM product WHERE product_id LIKE %s", (val,)
        elif f == "Name":
            q, p = "SELECT * FROM product WHERE product_name LIKE %s", (val,)
        elif f == "Category":
            q, p = "SELECT * FROM product WHERE category LIKE %s", (val,)
        else:
            q = """
                SELECT * FROM product
                WHERE product_id LIKE %s
                   OR product_name LIKE %s
                   OR category LIKE %s
            """
            p = (val, val, val)

        cur.execute(q, p)
        for r in cur.fetchall():
            tree.insert("", END, values=r)

    search_var.trace("w", refresh)
    filter_cb.bind("<<ComboboxSelected>>", refresh)
    refresh()

    # ---------------------------
    # DELETE SELECTED
    # ---------------------------
    def delete_product_selected():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a product to delete")
            return

        pid = tree.item(sel)["values"][0]

        if messagebox.askyesno("Confirm", "Delete selected product?"):
            cur.execute("DELETE FROM product WHERE product_id=%s", (pid,))
            db.commit()
            refresh()

    # ---------------------------
    # ADD / UPDATE FORM
    # ---------------------------
    def product_form(mode):
        win = Toplevel(dash)
        win.title(mode.capitalize() + " Product")
        win.geometry("350x350")

        fields = ["ID", "Name", "Category", "Price"]
        entries = {}

        for f in fields:
            Label(win, text=f).pack()
            e = Entry(win)
            e.pack(pady=4)
            entries[f] = e

        if mode == "update":
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Select", "Select a product first")
                win.destroy()
                return

            data = tree.item(sel)["values"]
            for f, v in zip(fields, data):
                entries[f].insert(0, v)

        Button(
            win, text="SAVE",
            bg=BG_BUTTON, fg=FG_WHITE,
            font=FONT_HEAD,
            command=lambda: save_product(entries, win, mode)
        ).pack(pady=15)

    # ---------------------------
    # BUTTONS
    # ---------------------------
    btn_frame = Frame(content, bg=BG_CONTENT)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="ADD",
           bg=BTN_SUCCESS, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: product_form("add")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="UPDATE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: product_form("update")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="DELETE",
           bg=BTN_DANGER, fg=FG_WHITE,
           font=FONT_HEAD,
           command=delete_product_selected
           ).pack(side=LEFT, padx=10)



# ================= INVOICES =================
def save_invoice(e, w, mode):
    if mode == "add":
        cur.execute(
            "INSERT INTO invoice VALUES (%s,%s,%s,%s)",
            (
                e["Invoice ID"].get(),
                e["Customer ID"].get(),
                e["Date"].get(),
                e["Total"].get()
            )
        )

    elif mode == "update":
        cur.execute("""
            UPDATE invoice
            SET customer_id=%s,
                invoice_date=%s,
                total_amount=%s
            WHERE invoice_id=%s
        """, (
            e["Customer ID"].get(),
            e["Date"].get(),
            e["Total"].get(),
            e["Invoice ID"].get()
        ))

    db.commit()
    w.destroy()
    invoices()

def invoices():
    clear()
    Label(content, text="Invoices",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # 🔍 Search + Dropdown
    search_var = StringVar()
    filter_var = StringVar(value="All")

    top = Frame(content, bg=BG_CONTENT)
    top.pack(pady=5)

    Label(top, text="Search:", bg=BG_CONTENT).pack(side=LEFT)
    Entry(top, textvariable=search_var, width=25).pack(side=LEFT, padx=6)

    Label(top, text="Filter By:", bg=BG_CONTENT).pack(side=LEFT, padx=6)

    filter_cb = ttk.Combobox(
        top,
        textvariable=filter_var,
        state="readonly",
        width=15,
        values=["All", "Invoice ID", "Customer ID", "Date"]
    )
    filter_cb.pack(side=LEFT)

    tree = table(("Invoice ID", "Customer ID", "Date", "Total"))

    # ---------------------------
    # REFRESH
    # ---------------------------
    def refresh(*args):
        tree.delete(*tree.get_children())
        val = f"%{search_var.get()}%"
        f = filter_var.get()

        if f == "Invoice ID":
            q, p = "SELECT * FROM invoice WHERE invoice_id LIKE %s", (val,)
        elif f == "Customer ID":
            q, p = "SELECT * FROM invoice WHERE customer_id LIKE %s", (val,)
        elif f == "Date":
            q, p = "SELECT * FROM invoice WHERE invoice_date LIKE %s", (val,)
        else:
            q = """
                SELECT * FROM invoice
                WHERE invoice_id LIKE %s
                   OR customer_id LIKE %s
                   OR invoice_date LIKE %s
            """
            p = (val, val, val)

        cur.execute(q, p)
        for r in cur.fetchall():
            tree.insert("", END, values=r)

    search_var.trace("w", refresh)
    filter_cb.bind("<<ComboboxSelected>>", refresh)
    refresh()

    # ---------------------------
    # DELETE SELECTED
    # ---------------------------
    def delete_invoice_selected():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select an invoice to delete")
            return

        iid = tree.item(sel)["values"][0]

        if messagebox.askyesno("Confirm", "Delete selected invoice?"):
            cur.execute("DELETE FROM invoice WHERE invoice_id=%s", (iid,))
            db.commit()
            refresh()

    # ---------------------------
    # ADD / UPDATE FORM
    # ---------------------------
    def invoice_form(mode):
        win = Toplevel(dash)
        win.title(mode.capitalize() + " Invoice")
        win.geometry("350x350")

        fields = ["Invoice ID", "Customer ID", "Date", "Total"]
        entries = {}

        for f in fields:
            Label(win, text=f).pack()
            e = Entry(win)
            e.pack(pady=4)
            entries[f] = e

        if mode == "update":
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Select", "Select an invoice first")
                win.destroy()
                return

            data = tree.item(sel)["values"]
            for f, v in zip(fields, data):
                entries[f].insert(0, v)

        Button(
            win, text="SAVE",
            bg=BG_BUTTON, fg=FG_WHITE,
            font=FONT_HEAD,
            command=lambda: save_invoice(entries, win, mode)
        ).pack(pady=15)

    # ---------------------------
    # BUTTONS
    # ---------------------------
    btn_frame = Frame(content, bg=BG_CONTENT)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="ADD",
           bg=BTN_SUCCESS, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: invoice_form("add")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="UPDATE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: invoice_form("update")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="DELETE",
           bg=BTN_DANGER, fg=FG_WHITE,
           font=FONT_HEAD,
           command=delete_invoice_selected
           ).pack(side=LEFT, padx=10)


# ================= PAYMENTS =================
def save_payment(e, w, mode):
    if mode == "add":
        cur.execute(
            "INSERT INTO payment VALUES (%s,%s,%s,%s,%s)",
            (
                e["Payment ID"].get(),
                e["Invoice ID"].get(),
                e["Mode"].get(),
                e["Date"].get(),
                e["Amount"].get()
            )
        )

    elif mode == "update":
        cur.execute("""
            UPDATE payment
            SET invoice_id=%s,
                payment_mode=%s,
                payment_date=%s,
                amount=%s
            WHERE payment_id=%s
        """, (
            e["Invoice ID"].get(),
            e["Mode"].get(),
            e["Date"].get(),
            e["Amount"].get(),
            e["Payment ID"].get()
        ))

    db.commit()
    w.destroy()
    payments()

def payments():
    clear()
    Label(content, text="Payments",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # 🔍 Search + Dropdown
    search_var = StringVar()
    filter_var = StringVar(value="All")

    top = Frame(content, bg=BG_CONTENT)
    top.pack(pady=5)

    Label(top, text="Search:", bg=BG_CONTENT).pack(side=LEFT)
    Entry(top, textvariable=search_var, width=25).pack(side=LEFT, padx=6)

    Label(top, text="Filter By:", bg=BG_CONTENT).pack(side=LEFT, padx=6)

    filter_cb = ttk.Combobox(
        top,
        textvariable=filter_var,
        state="readonly",
        width=15,
        values=["All", "Payment ID", "Invoice ID", "Mode"]
    )
    filter_cb.pack(side=LEFT)

    tree = table(("Payment ID", "Invoice ID", "Mode", "Date", "Amount"))

    # ---------------------------
    # REFRESH
    # ---------------------------
    def refresh(*args):
        tree.delete(*tree.get_children())
        val = f"%{search_var.get()}%"
        f = filter_var.get()

        if f == "Payment ID":
            q, p = "SELECT * FROM payment WHERE payment_id LIKE %s", (val,)
        elif f == "Invoice ID":
            q, p = "SELECT * FROM payment WHERE invoice_id LIKE %s", (val,)
        elif f == "Mode":
            q, p = "SELECT * FROM payment WHERE payment_mode LIKE %s", (val,)
        else:
            q = """
                SELECT * FROM payment
                WHERE payment_id LIKE %s
                   OR invoice_id LIKE %s
                   OR payment_mode LIKE %s
            """
            p = (val, val, val)

        cur.execute(q, p)
        for r in cur.fetchall():
            tree.insert("", END, values=r)

    search_var.trace("w", refresh)
    filter_cb.bind("<<ComboboxSelected>>", refresh)
    refresh()

    # ---------------------------
    # DELETE SELECTED
    # ---------------------------
    def delete_payment_selected():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a payment to delete")
            return

        pid = tree.item(sel)["values"][0]

        if messagebox.askyesno("Confirm", "Delete selected payment?"):
            cur.execute("DELETE FROM payment WHERE payment_id=%s", (pid,))
            db.commit()
            refresh()

    # ---------------------------
    # ADD / UPDATE FORM
    # ---------------------------
    def payment_form(mode):
        win = Toplevel(dash)
        win.title(mode.capitalize() + " Payment")
        win.geometry("350x350")

        fields = ["Payment ID", "Invoice ID", "Mode", "Date", "Amount"]
        entries = {}

        for f in fields:
            Label(win, text=f).pack()
            e = Entry(win)
            e.pack(pady=4)
            entries[f] = e

        if mode == "update":
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Select", "Select a payment first")
                win.destroy()
                return

            data = tree.item(sel)["values"]
            for f, v in zip(fields, data):
                entries[f].insert(0, v)

        Button(
            win, text="SAVE",
            bg=BG_BUTTON, fg=FG_WHITE,
            font=FONT_HEAD,
            command=lambda: save_payment(entries, win, mode)
        ).pack(pady=15)

    # ---------------------------
    # BUTTONS
    # ---------------------------
    btn_frame = Frame(content, bg=BG_CONTENT)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="ADD",
           bg=BTN_SUCCESS, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: payment_form("add")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="UPDATE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: payment_form("update")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="DELETE",
           bg=BTN_DANGER, fg=FG_WHITE,
           font=FONT_HEAD,
           command=delete_payment_selected
           ).pack(side=LEFT, padx=10)


# ================= TAX =================
def save_tax(e, w, mode):
    if mode == "add":
        cur.execute(
            "INSERT INTO tax VALUES (%s,%s,%s,%s,%s)",
            (
                e["Tax ID"].get(),
                e["Invoice ID"].get(),
                e["Type"].get(),
                e["Percent"].get(),
                e["Amount"].get()
            )
        )

    elif mode == "update":
        cur.execute("""
            UPDATE tax
            SET invoice_id=%s,
                tax_type=%s,
                tax_percent=%s,
                tax_amount=%s
            WHERE tax_id=%s
        """, (
            e["Invoice ID"].get(),
            e["Type"].get(),
            e["Percent"].get(),
            e["Amount"].get(),
            e["Tax ID"].get()
        ))

    db.commit()
    w.destroy()
    tax()

def tax():
    clear()
    Label(content, text="Tax",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # 🔍 Search + Dropdown
    search_var = StringVar()
    filter_var = StringVar(value="All")

    top = Frame(content, bg=BG_CONTENT)
    top.pack(pady=5)

    Label(top, text="Search:", bg=BG_CONTENT).pack(side=LEFT)
    Entry(top, textvariable=search_var, width=25).pack(side=LEFT, padx=6)

    Label(top, text="Filter By:", bg=BG_CONTENT).pack(side=LEFT, padx=6)

    filter_cb = ttk.Combobox(
        top,
        textvariable=filter_var,
        state="readonly",
        width=15,
        values=["All", "Tax ID", "Invoice ID", "Type"]
    )
    filter_cb.pack(side=LEFT)

    tree = table(("Tax ID", "Invoice ID", "Type", "Percent", "Amount"))

    # ---------------------------
    # REFRESH
    # ---------------------------
    def refresh(*args):
        tree.delete(*tree.get_children())
        val = f"%{search_var.get()}%"
        f = filter_var.get()

        if f == "Tax ID":
            q, p = "SELECT * FROM tax WHERE tax_id LIKE %s", (val,)
        elif f == "Invoice ID":
            q, p = "SELECT * FROM tax WHERE invoice_id LIKE %s", (val,)
        elif f == "Type":
            q, p = "SELECT * FROM tax WHERE tax_type LIKE %s", (val,)
        else:
            q = """
                SELECT * FROM tax
                WHERE tax_id LIKE %s
                   OR invoice_id LIKE %s
                   OR tax_type LIKE %s
            """
            p = (val, val, val)

        cur.execute(q, p)
        for r in cur.fetchall():
            tree.insert("", END, values=r)

    search_var.trace("w", refresh)
    filter_cb.bind("<<ComboboxSelected>>", refresh)
    refresh()

    # ---------------------------
    # DELETE SELECTED
    # ---------------------------
    def delete_tax_selected():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select a tax record to delete")
            return

        tid = tree.item(sel)["values"][0]

        if messagebox.askyesno("Confirm", "Delete selected tax record?"):
            cur.execute("DELETE FROM tax WHERE tax_id=%s", (tid,))
            db.commit()
            refresh()

    # ---------------------------
    # ADD / UPDATE FORM
    # ---------------------------
    def tax_form(mode):
        win = Toplevel(dash)
        win.title(mode.capitalize() + " Tax")
        win.geometry("350x350")

        fields = ["Tax ID", "Invoice ID", "Type", "Percent", "Amount"]
        entries = {}

        for f in fields:
            Label(win, text=f).pack()
            e = Entry(win)
            e.pack(pady=4)
            entries[f] = e

        if mode == "update":
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Select", "Select a tax record first")
                win.destroy()
                return

            data = tree.item(sel)["values"]
            for f, v in zip(fields, data):
                entries[f].insert(0, v)

        Button(
            win, text="SAVE",
            bg=BG_BUTTON, fg=FG_WHITE,
            font=FONT_HEAD,
            command=lambda: save_tax(entries, win, mode)
        ).pack(pady=15)

    # ---------------------------
    # BUTTONS
    # ---------------------------
    btn_frame = Frame(content, bg=BG_CONTENT)
    btn_frame.pack(pady=10)

    Button(btn_frame, text="ADD",
           bg=BTN_SUCCESS, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: tax_form("add")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="UPDATE",
           bg=BG_BUTTON, fg=FG_WHITE,
           font=FONT_HEAD,
           command=lambda: tax_form("update")
           ).pack(side=LEFT, padx=10)

    Button(btn_frame, text="DELETE",
           bg=BTN_DANGER, fg=FG_WHITE,
           font=FONT_HEAD,
           command=delete_tax_selected
           ).pack(side=LEFT, padx=10)

def kpi_card(parent, title, value, bg):
    card = Frame(parent, bg=bg, width=220, height=90)
    card.pack(side=LEFT, padx=10)
    card.pack_propagate(False)

    Label(card, text=title, bg=bg, fg="white",
          font=("Segoe UI", 12, "bold")).pack(pady=5)

    Label(card, text=value, bg=bg, fg="white",
          font=("Segoe UI", 18, "bold")).pack()
def alert_card(parent, title, value, color):
    card = Frame(parent, bg=color, width=260, height=80)
    card.pack(side=LEFT, padx=10)
    card.pack_propagate(False)

    Label(card, text=title, bg=color, fg="white",
          font=("Segoe UI", 12, "bold")).pack(pady=(10, 0))

    Label(card, text=value, bg=color, fg="white",
          font=("Segoe UI", 16, "bold")).pack()

def analytics():
    clear()

    Label(content, text="Analytics Dashboard",
          font=FONT_TITLE, bg=BG_CONTENT).pack(pady=10)

    # ================= KPI SECTION =================
    engine = get_engine()

    df_invoice = pd.read_sql("SELECT * FROM invoice", engine)
    df_payment = pd.read_sql("SELECT * FROM payment", engine)
    df_tax = pd.read_sql("SELECT * FROM tax", engine)
    df_customer = pd.read_sql("SELECT * FROM customer", engine)

    kpi_frame = Frame(content, bg=BG_CONTENT)
    kpi_frame.pack(pady=10)

    total_revenue = df_invoice["total_amount"].sum() if not df_invoice.empty else 0
    total_invoices = len(df_invoice)
    total_customers = len(df_customer)
    total_payments = df_payment["amount_paid"].sum() if not df_payment.empty else 0
    total_tax = df_tax["tax_amount"].sum() if not df_tax.empty else 0

    kpi_card(kpi_frame, "Total Revenue", f"₹ {total_revenue:.2f}", "#2563eb")
    kpi_card(kpi_frame, "Invoices", total_invoices, "#16a34a")
    kpi_card(kpi_frame, "Customers", total_customers, "#9333ea")
    kpi_card(kpi_frame, "Payments", f"₹ {total_payments:.2f}", "#f59e0b")
    kpi_card(kpi_frame, "Tax Collected", f"₹ {total_tax:.2f}", "#dc2626")


    # ================= DATE FILTER UI =================
    filter_frame = Frame(content, bg=BG_CONTENT)
    filter_frame.pack(pady=5)

    Label(filter_frame, text="From (YYYY-MM-DD):", bg=BG_CONTENT).pack(side=LEFT)
    from_date = Entry(filter_frame, width=12)
    from_date.pack(side=LEFT, padx=5)

    Label(filter_frame, text="To (YYYY-MM-DD):", bg=BG_CONTENT).pack(side=LEFT)
    to_date = Entry(filter_frame, width=12)
    to_date.pack(side=LEFT, padx=5)

    # ================= GRAPH FRAME =================
    graph_frame = Frame(content, bg=BG_CONTENT)
    graph_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # ================= LOAD + DRAW FUNCTION =================
    def draw_graph():
        for w in graph_frame.winfo_children():
            w.destroy()

        engine = get_engine()
        df_invoice = pd.read_sql("SELECT * FROM invoice", engine)
        df_payment = pd.read_sql("SELECT * FROM payment", engine)
        df_tax = pd.read_sql("SELECT * FROM tax", engine)

        # -------- DATE CONVERSION --------
        if not df_invoice.empty:
            df_invoice["invoice_date"] = pd.to_datetime(df_invoice["invoice_date"])

        if not df_payment.empty:
            df_payment["payment_date"] = pd.to_datetime(df_payment["payment_date"])

        # -------- APPLY FILTER --------
        try:
            f = from_date.get()
            t = to_date.get()

            if f:
                f = pd.to_datetime(f)
                df_invoice = df_invoice[df_invoice["invoice_date"] >= f]
                df_payment = df_payment[df_payment["payment_date"] >= f]

            if t:
                t = pd.to_datetime(t)
                df_invoice = df_invoice[df_invoice["invoice_date"] <= t]
                df_payment = df_payment[df_payment["payment_date"] <= t]

            if not df_tax.empty and not df_invoice.empty:
                df_tax = df_tax[df_tax["invoice_id"].isin(df_invoice["invoice_id"])]

        except:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format")
            return

        # ================= MATPLOTLIB FIGURE =================
        fig = Figure(figsize=(11, 7), dpi=100)
        axs = fig.subplots(2, 2)
        fig.suptitle("Billing Management Analytics", fontsize=16)

        # -------- 1. TOTAL SALES --------
        if not df_invoice.empty:
            sales = df_invoice.groupby("invoice_date")["total_amount"].sum()
            axs[0, 0].plot(sales.index, sales.values, marker="o")
            axs[0, 0].set_title("Total Sales Over Time")
            axs[0, 0].set_xlabel("Date")
            axs[0, 0].set_ylabel("Total Amount")

        # -------- 2. PAYMENT MODE --------
        if not df_payment.empty:
            mode = df_payment["payment_mode"].value_counts()
            axs[0, 1].pie(mode, labels=mode.index, autopct="%1.1f%%", startangle=90)
            axs[0, 1].set_title("Payment Mode Distribution")

        # -------- 3. TAX TYPE --------
        if not df_tax.empty:
            sns.barplot(
                x="tax_type",
                y="tax_amount",
                data=df_tax,
                ax=axs[1, 0]
            )
            axs[1, 0].set_title("Tax Amount by Type")

        # -------- 4. INVOICE AMOUNT --------
        if not df_invoice.empty:
            sns.histplot(
                df_invoice["total_amount"],
                bins=10,
                kde=True,
                ax=axs[1, 1]
            )
            axs[1, 1].set_title("Invoice Amount Distribution")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # ================= APPLY BUTTON =================
    Button(
        filter_frame,
        text="Apply Filter",
        bg=BG_BUTTON,
        fg="white",
        command=draw_graph
    ).pack(side=LEFT, padx=10)

    # Initial load (no filter)
    draw_graph()



# ================= DASHBOARD =================
def dashboard():
    global dash, content

    dash = Tk()
    dash.geometry("1300x750")
    dash.title("Billing Dashboard")

    Label(dash, text="BILLING MANAGEMENT SYSTEM",
          font=FONT_TITLE, bg=BG_HEADER,
          fg="white", pady=15).pack(fill=X)

    main = Frame(dash)
    main.pack(fill=BOTH, expand=True)

    sidebar = Frame(main, bg=BG_SIDEBAR, width=230)
    sidebar.pack(side=LEFT, fill=Y)

    def side_btn(text, cmd):
        Button(sidebar, text=text, bg=BG_BUTTON,
               fg="white", font=FONT_HEAD,
               width=18, height=2,
               command=cmd).pack(pady=6)

    Label(sidebar, text="MENU",
          font=FONT_HEAD, bg=BG_SIDEBAR,
          fg="white").pack(pady=15)

    side_btn("CUSTOMERS", customers)
    side_btn("PRODUCTS", products)
    side_btn("INVOICES", invoices)
    side_btn("PAYMENTS", payments)
    side_btn("TAX", tax)
    side_btn("ANALYTICS", analytics)

    Button(sidebar, text="LOGOUT",
           bg="red", fg="white",
           font=FONT_HEAD,
           command=lambda:[dash.destroy(), login_screen()]
           ).pack(pady=30)

    content = Frame(main, bg="#f1f5f9")
    content.pack(side=LEFT, fill=BOTH, expand=True)

    Label(content, text="Welcome to Billing Dashboard",
          font=("Segoe UI", 24, "bold"),
          bg="#f1f5f9").pack(pady=200)

    dash.mainloop()

# ================= LOGIN =================
def login_screen():
    global root, user_entry, pass_entry

    root = Tk()
    root.attributes("-fullscreen", True)
    root.title("Billing Login")

    bg_img = Image.open(r"C:\Users\Vy-Ventures\Downloads\background.png")
    bg_img = bg_img.resize(
        (root.winfo_screenwidth(), root.winfo_screenheight())
    )
    bg = ImageTk.PhotoImage(bg_img)
    Label(root, image=bg).place(x=0, y=0, relwidth=1, relheight=1)
    root.bg = bg

    card = Frame(root, bg="white")
    card.place(relx=0.7, rely=0.5, anchor=CENTER, width=420, height=360)

    Label(card, text="Welcome Back",
          font=("Segoe UI", 24, "bold"),
          bg="white").pack(pady=20)

    Label(card, text="Username", bg="white").pack()
    user_entry = Entry(card)
    user_entry.pack(ipady=6, padx=40, fill=X)

    Label(card, text="Password", bg="white").pack(pady=10)
    pass_entry = Entry(card, show="*")
    pass_entry.pack(ipady=6, padx=40, fill=X)

    Button(card, text="LOGIN",
           bg=BG_BUTTON, fg="white",
           font=("Segoe UI", 14, "bold"),
           command=check_login).pack(pady=25)

    Button(card, text="EXIT",
           bg="white", fg="red",
           command=root.destroy).pack()

    root.mainloop()

def check_login():
    user = user_entry.get()
    pwd = pass_entry.get()

    con = db_connect()
    c = con.cursor()
    c.execute("SELECT * FROM login WHERE username=%s AND password=%s",
              (user, pwd))
    result = c.fetchone()
    con.close()

    if result:
        root.destroy()
        dashboard()
    else:
        messagebox.showerror("Error", "Invalid Login")


# ================= START =================
login_screen()
