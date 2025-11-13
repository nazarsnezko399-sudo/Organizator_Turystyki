import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

# --- KONFIGURACJA BAZY DANYCH I FUNKCJE SQL ---

DB_NAME = 'organizator_wycieczek.db'


def connect_db():
    """Łączy się z bazą danych i zwraca obiekt połączenia."""
    return sqlite3.connect(DB_NAME)


def setup_db():
    """Tworzy tabele bazy danych, jeśli nie istnieją."""
    conn = connect_db()
    cursor = conn.cursor()

    # Tabela przechowująca dane klientów i rezerwacji
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY,
            imie TEXT NOT NULL,
            nazwisko TEXT NOT NULL,
            data_urodzenia TEXT,
            nr_paszportu TEXT UNIQUE,
            waznosc_paszportu TEXT,
            termin_wycieczki TEXT NOT NULL,
            cena_bazowa REAL NOT NULL,
            cena_ostateczna REAL NOT NULL,

            status_platnosci TEXT NOT NULL, 
            nr_faktury TEXT,
            kwota_zaplacona REAL,
            UNIQUE (nr_paszportu, termin_wycieczki)
        );
    ''')
    conn.commit()
    conn.close()


# --- GŁÓWNA KLASA APLIKACJI (GUI) ---

class TravelOrganizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Organizator Wyjazdów Turystycznych (IT Starter Project)")

        # Inicjalizacja bazy danych przy starcie
        setup_db()

        # Zmienne przechowujące aktualnie aktywne elementy GUI
        self.current_frame = None
        self.status_var = tk.StringVar(master)
        self.status_var.set("Oczekuje na płatność")

        self.create_main_menu()

    def create_main_menu(self):
        """Tworzy menu główne aplikacji."""
        self.clear_frame()

        self.current_frame = tk.Frame(self.master, padx=20, pady=20)
        self.current_frame.pack(padx=10, pady=10)

        tk.Label(self.current_frame, text="System Zarządzania Rezerwacjami", font=('Arial', 16, 'bold')).pack(pady=10)
        tk.Label(self.current_frame, text="Wybierz opcję:", font=('Arial', 12)).pack(pady=5)

        # Przyciski głównego menu
        tk.Button(self.current_frame, text="1. Dodaj Nowego Klienta / Rezerwację",
                  command=self.show_add_client_form, width=40, height=2).pack(pady=5)

        tk.Button(self.current_frame, text="2. Zmień Status Płatności / Wprowadź Fakturę",
                  command=self.show_update_payment_form, width=40, height=2).pack(pady=5)

        tk.Button(self.current_frame, text="3. Generuj Raport Wyjazdowy (Lista Płatności)",
                  command=self.show_report_view, width=40, height=2).pack(pady=5)

        tk.Label(self.current_frame, text="PROJEKT NA GITHUB: Pokazuje znajomość Pythona, SQL i Tkinter.",
                 font=('Arial', 9, 'italic')).pack(pady=20)

    def clear_frame(self):
        """Usuwa aktualnie wyświetlaną ramkę/ekran."""
        if self.current_frame:
            self.current_frame.destroy()

    # --- 1. DODAWANIE KLIENTA ---
    def show_add_client_form(self):
        """Formularz dodawania nowego klienta i rezerwacji."""
        self.clear_frame()
        self.current_frame = tk.Frame(self.master, padx=20, pady=20)
        self.current_frame.pack(padx=10, pady=10)

        tk.Label(self.current_frame, text="Dodawanie Nowej Rezerwacji", font=('Arial', 14, 'bold')).grid(row=0,
                                                                                                         column=0,
                                                                                                         columnspan=2,
                                                                                                         pady=10)

        fields = [
            ("Imię:", "imie"),
            ("Nazwisko:", "nazwisko"),
            ("Data Urodzenia (RRRR-MM-DD):", "data_urodzenia"),
            ("Nr Paszportu:", "nr_paszportu"),
            ("Ważność Paszportu (RRRR-MM-DD):", "waznosc_paszportu"),
            ("Termin Wycieczki (RRRR-MM-DD):", "termin_wycieczki"),
            ("Cena Bazowa (PLN):", "cena_bazowa"),
            ("Rabat / Modyfikacja Ceny (PLN, np. -100):", "rabat")
        ]

        self.entries = {}
        for i, (label_text, field_key) in enumerate(fields):
            tk.Label(self.current_frame, text=label_text, anchor='w').grid(row=i + 1, column=0, sticky='w', padx=5,
                                                                           pady=2)
            entry = tk.Entry(self.current_frame, width=30)
            entry.grid(row=i + 1, column=1, padx=5, pady=2)
            self.entries[field_key] = entry

        # Domyślny status
        tk.Label(self.current_frame, text="Status Płatności:", anchor='w').grid(row=len(fields) + 1, column=0,
                                                                                sticky='w', padx=5, pady=2)
        self.default_status = tk.StringVar(self.current_frame)
        self.default_status.set("Oczekuje na płatność")  # Domyślna wartość
        tk.Label(self.current_frame, textvariable=self.default_status, fg='red').grid(row=len(fields) + 1, column=1,
                                                                                      sticky='w', padx=5, pady=2)

        tk.Button(self.current_frame, text="Zapisz Rezerwację", command=self.add_client_to_db).grid(row=len(fields) + 2,
                                                                                                    column=0, pady=10)
        tk.Button(self.current_frame, text="Powrót do Menu", command=self.create_main_menu).grid(row=len(fields) + 2,
                                                                                                 column=1, pady=10)

    def add_client_to_db(self):
        """Pobiera dane z formularza i zapisuje je w bazie danych."""
        try:
            data = {key: entry.get() for key, entry in self.entries.items()}

            # Weryfikacja dat (prosta)
            for date_key in ['data_urodzenia', 'waznosc_paszportu', 'termin_wycieczki']:
                datetime.strptime(data[date_key], '%Y-%m-%d')

            # Obliczenie ceny ostatecznej
            cena_bazowa = float(data['cena_bazowa'])
            rabat = float(data['rabat'] or 0)
            cena_ostateczna = cena_bazowa + rabat  # Rabat jest ujemny, więc działa jako odejmowanie

            # Wstawienie do bazy
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reservations (imie, nazwisko, data_urodzenia, nr_paszportu, waznosc_paszportu, 
                                          termin_wycieczki, cena_bazowa, cena_ostateczna, status_platnosci, 
                                          nr_faktury, kwota_zaplacona)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['imie'], data['nazwisko'], data['data_urodzenia'], data['nr_paszportu'],
                data['waznosc_paszportu'], data['termin_wycieczki'], cena_bazowa, cena_ostateczna,
                "Oczekuje na płatność", None, 0.0
            ))
            conn.commit()
            conn.close()

            messagebox.showinfo("Sukces",
                                f"Rezerwacja dla {data['imie']} {data['nazwisko']} została zapisana.\nCena końcowa: {cena_ostateczna} PLN.")
            self.create_main_menu()  # Powrót do menu

        except ValueError:
            messagebox.showerror("Błąd Wprowadzania",
                                 "Sprawdź format cen/rabatów (muszą być liczbami) lub daty (format RRRR-MM-DD).")
        except sqlite3.IntegrityError:
            messagebox.showerror("Błąd Danych",
                                 "Rezerwacja dla tego numeru paszportu na ten termin wycieczki już istnieje.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas zapisu: {e}")

    # --- 2. AKTUALIZACJA PŁATNOŚCI ---

    def show_update_payment_form(self):
        """Formularz wyszukiwania rezerwacji i aktualizacji płatności/faktury."""
        self.clear_frame()
        self.current_frame = tk.Frame(self.master, padx=20, pady=20)
        self.current_frame.pack(padx=10, pady=10)

        tk.Label(self.current_frame, text="Aktualizacja Płatności i Faktury", font=('Arial', 14, 'bold')).grid(row=0,
                                                                                                               column=0,
                                                                                                               columnspan=3,
                                                                                                               pady=10)

        tk.Label(self.current_frame, text="ID Rezerwacji do Aktualizacji:", anchor='w').grid(row=1, column=0,
                                                                                             sticky='w', padx=5, pady=5)
        self.payment_id_entry = tk.Entry(self.current_frame, width=20)
        self.payment_id_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        tk.Button(self.current_frame, text="Wyszukaj", command=self.load_reservation_details).grid(row=1, column=2,
                                                                                                   padx=5, pady=5)

        # Ramka do wyświetlania szczegółów
        self.details_frame = tk.LabelFrame(self.current_frame, text="Szczegóły Rezerwacji", padx=10, pady=10)
        self.details_frame.grid(row=2, column=0, columnspan=3, pady=15, sticky='ew')



        # Elementy formularza aktualizacji (używamy już zainicjalizowanych obiektów self.)
        # Nie tworzymy ich na nowo, bo są już w self.

        tk.Button(self.current_frame, text="Powrót do Menu", command=self.create_main_menu).grid(row=3, column=0,
                                                                                                 columnspan=3, pady=10)

    def load_reservation_details(self):
        """Pobiera i wyświetla szczegóły rezerwacji do edycji płatności."""
        reservation_id = self.payment_id_entry.get()
        if not reservation_id.isdigit():
            messagebox.showerror("Błąd", "ID musi być liczbą.")
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,))
        reservation = cursor.fetchone()
        conn.close()

        # Czyszczenie ramki szczegółów
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        if reservation:
            reservation_data = {
                'id': reservation[0],
                'imie': reservation[1],
                'nazwisko': reservation[2],
                'termin': reservation[6],
                'cena_ostateczna': reservation[8],
                'status_platnosci': reservation[9],
                'nr_faktury': reservation[10],
                'kwota_zaplacona': reservation[11],
            }

            # Wyświetlenie aktualnych danych
            tk.Label(self.details_frame,
                     text=f"Klient: {reservation_data['imie']} {reservation_data['nazwisko']}").grid(row=0, column=0,
                                                                                                     sticky='w', pady=2)
            tk.Label(self.details_frame, text=f"Termin: {reservation_data['termin']}").grid(row=1, column=0, sticky='w',
                                                                                            pady=2)
            tk.Label(self.details_frame, text=f"Cena końcowa: {reservation_data['cena_ostateczna']} PLN").grid(row=2,
                                                                                                               column=0,
                                                                                                               sticky='w',
                                                                                                               pady=2)

            # Formularz aktualizacji
            tk.Label(self.details_frame, text="Nowy Nr Faktury:").grid(row=3, column=0, sticky='w', padx=5, pady=5)

            self.invoice_entry = tk.Entry(self.details_frame, width=25)
            self.invoice_entry.delete(0, tk.END)
            self.invoice_entry.insert(0, reservation_data['nr_faktury'] if reservation_data['nr_faktury'] else "")
            self.invoice_entry.grid(row=3, column=1, padx=5, pady=5)

            tk.Label(self.details_frame, text="Kwota Zapłacona:").grid(row=4, column=0, sticky='w', padx=5, pady=5)

            self.amount_paid_entry = tk.Entry(self.details_frame, width=25)
            self.amount_paid_entry.delete(0, tk.END)
            self.amount_paid_entry.insert(0, str(reservation_data['kwota_zaplacona']))
            self.amount_paid_entry.grid(row=4, column=1, padx=5, pady=5)

            tk.Label(self.details_frame, text="Status Płatności:").grid(row=5, column=0, sticky='w', padx=5, pady=5)

            self.status_var.set(reservation_data['status_platnosci'])
            self.status_option = ttk.Combobox(self.details_frame, textvariable=self.status_var,
                                              values=["Oczekuje na płatność", "Zapłacono przelewem","Zapłacono gotówką"])
            self.status_option.grid(row=5, column=1, padx=5, pady=5)

            tk.Button(self.details_frame, text="Zapisz Aktualizację",
                      command=lambda: self.update_payment_in_db(reservation_id)).grid(row=6, column=0, columnspan=2,
                                                                                      pady=10)
        else:
            tk.Label(self.details_frame, text=f"Brak rezerwacji o ID: {reservation_id}").grid(row=0, column=0, columnspan=2, pady=10)

    def update_payment_in_db(self, reservation_id):
        """Zapisuje zaktualizowane dane płatności do bazy."""
        try:
            nr_faktury = self.invoice_entry.get()
            kwota_zaplacona = float(self.amount_paid_entry.get())
            status = self.status_var.get()

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reservations SET nr_faktury = ?, kwota_zaplacona = ?, status_platnosci = ? WHERE id = ?
            ''', (nr_faktury, kwota_zaplacona, status, reservation_id))
            conn.commit()
            conn.close()

            messagebox.showinfo("Sukces", f"Płatność dla rezerwacji ID {reservation_id} zaktualizowana.")
            self.show_update_payment_form()  # Odświeżenie

        except ValueError:
            messagebox.showerror("Błąd", "Kwota zapłacona musi być liczbą.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")

    # --- 3. RAPORTOWANIE ---

    def show_report_view(self):
        """Ekran raportowania: wybór terminu i wyświetlenie listy."""
        self.clear_frame()
        self.current_frame = tk.Frame(self.master, padx=20, pady=20)
        self.current_frame.pack(padx=10, pady=10)

        tk.Label(self.current_frame, text="RAPORT WYJAZDOWY: Stan Płatności", font=('Arial', 14, 'bold')).grid(row=0,
                                                                                                               column=0,
                                                                                                               columnspan=3,
                                                                                                               pady=10)

        tk.Label(self.current_frame, text="Wybierz Termin Wycieczki (RRRR-MM-DD):", anchor='w').grid(row=1, column=0,
                                                                                                     sticky='w', padx=5,
                                                                                                     pady=5)
        self.report_date_entry = tk.Entry(self.current_frame, width=20)
        self.report_date_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        tk.Button(self.current_frame, text="Generuj Raport", command=self.generate_report).grid(row=1, column=2, padx=5,
                                                                                                pady=5)
        tk.Button(self.current_frame, text="Powrót do Menu", command=self.create_main_menu).grid(row=2, column=0,
                                                                                                 columnspan=3, pady=10)

        # Treeview na wyniki raportu
        self.report_tree = ttk.Treeview(self.current_frame,
                                        columns=("ID", "Klient", "Cena", "Zapłacono", "Status Płatności", "Nr Faktury"),
                                        show="headings")
        self.report_tree.grid(row=3, column=0, columnspan=3, pady=10, padx=5)

        # Konfiguracja kolumn
        for col in self.report_tree["columns"]:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120, anchor='center')

        self.report_tree.column("Klient", width=150)
        self.report_tree.column("Status Płatności", width=160)

    def generate_report(self):
        """Pobiera i wyświetla dane raportu z bazy dla wybranego terminu."""
        trip_date = self.report_date_entry.get()

        # Weryfikacja daty (tylko format RRRR-MM-DD)
        try:
            datetime.strptime(trip_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Błąd", "Niepoprawny format daty. Użyj RRRR-MM-DD.")
            return

        # Czyszczenie Treeview
        for i in self.report_tree.get_children():
            self.report_tree.delete(i)

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, imie, nazwisko, cena_ostateczna, kwota_zaplacona, status_platnosci, nr_faktury
            FROM reservations WHERE termin_wycieczki = ? ORDER BY nazwisko
        ''', (trip_date,))
        reservations = cursor.fetchall()
        conn.close()

        if not reservations:
            messagebox.showinfo("Informacja", f"Brak rezerwacji na termin: {trip_date}")
            return

        for res in reservations:
            # Kolorowanie statusu dla lepszej widoczności
            if res[5] == "Oczekuje na płatność":
                tag = 'unpaid'
            elif res[5].startswith("Zapłacono"):
                tag = 'paid'
            else:
                tag = ''

            self.report_tree.insert("", tk.END, values=(
                res[0],  # ID
                f"{res[1]} {res[2]}",  # Klient
                f"{res[3]:.2f}",  # Cena
                f"{res[4]:.2f}",  # Zapłacono
                res[5],  # Status
                res[6] if res[6] else "Brak"  # Nr Faktury
            ), tags=(tag,))

        # Konfiguracja tagów kolorowania
        self.report_tree.tag_configure('unpaid', background='#FFDDDD', foreground='red')
        self.report_tree.tag_configure('paid', background='#DDFFDD', foreground='green')


# --- URUCHOMIENIE APLIKACJI ---

if __name__ == '__main__':
    # Upewnienie się, że baza danych jest zainicjalizowana przed uruchomieniem GUI
    setup_db()

    root = tk.Tk()
    app = TravelOrganizerApp(root)
    root.mainloop()