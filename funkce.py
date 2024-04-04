from flask import session, g
import sqlite3
from datetime import datetime, timedelta


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('projekt.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db():
    db = g.pop('db', None)
    if db is not None:
        db.close()


def prihlasit_uzivatele(id_uzivatele, jmeno):
    session['id_uzivatele'] = id_uzivatele
    session['jmeno'] = jmeno

def odhlasit_uzivatele():
    session.clear()

def uzivatel_prihlasen():
    return 'id_uzivatele' in session

def aktualni_uzivatel():
    return {
        'id_uzivatele': session.get('id_uzivatele'),
        'jmeno': session.get('jmeno')
    }


def soucet_cen(id_uzivatele):
    try:
        db = get_db()
        soucet = db.execute("""
            SELECT SUM(p.cena) AS celkova_castka
            FROM Kosik k
            JOIN polozky p ON k.id_polozky = p.id_polozky
            WHERE k.id_uzivatele = ?
        """, (id_uzivatele,)).fetchone()

        return soucet['celkova_castka'] if soucet else 0
    except Exception as e:
        msg = f"Došlo k chybě při výpočtu součtu cen: {str(e)}"
        print(msg)
        return 0
    


def cas_do_doruceni(cas_doruceni):
    # Získání aktuálního času
    nyni = datetime.now()
    
    # Výpočet rozdílu mezi časem doručení a aktuálním časem
    rozdil = cas_doruceni - nyni
    
    # Vrácení zbývajícího času v sekundách
    return rozdil.total_seconds()