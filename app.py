from flask import Flask, render_template, request, redirect, url_for, g, session, flash, get_flashed_messages, jsonify
from funkce import prihlasit_uzivatele, odhlasit_uzivatele, uzivatel_prihlasen, aktualni_uzivatel, soucet_cen, cas_do_doruceni #nutné si pohrát se session a udělat i odhlášení
import sqlite3
from datetime import datetime, timedelta
from bcrypt import checkpw, gensalt, hashpw
                            
"UZIVATEL HENRY JONES email: henry@☻jones.cz má roli Admina a heslo je 159"

app = Flask(__name__)
app.secret_key="fhdjalalfllg462"

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('projekt.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db():
    db = g.pop('db', None)
    if db is not None:
        db.close()



@app.before_request
def before_request():
    get_db()
    session['prihlasen'] = uzivatel_prihlasen()
    session['aktualni_uzivatel'] = aktualni_uzivatel()
    session['je_admin'] = je_admin()
    session['je_poslicek'] = je_poslicek()
    # Zkontroluje, zda uživatel je admin před tím, než přistoupí k administračnímu panelu
    if request.endpoint == 'admin_panel':
        if not je_admin():
            return redirect(url_for('index')) # Přesměruje na index.html, pokud  není admin
    

@app.teardown_request
def teardown_request(exception):
    close_db()
    
@app.route('/restaurace/<typ_restaurace>')
def moje_restaurace(typ_restaurace):
    db = get_db()
    restaurace_ve_kategorie = db.execute("SELECT nazev_restaurace, adresa FROM restaurace where typ_restaurace = ?", (typ_restaurace,)).fetchall()
    

    return render_template('moje_restaurace.html', restaurace_ve_kategorie=restaurace_ve_kategorie, typ_restaurace=typ_restaurace)

@app.route('/zobrazeni/<typ>')
def vyhledavani(typ):
    db = get_db()
    if typ == 'restaurace':
        seznam = db.execute("SELECT id_restaurace, nazev_restaurace, adresa FROM restaurace").fetchall()
        nadpis = "Restaurace"
    elif typ == 'kategorie':
        seznam = db.execute("SELECT DISTINCT typ_restaurace FROM restaurace").fetchall()
        nadpis = "Kategorie"
    else:
        return "Neplatný typ"
    
    return render_template('vyhledavani.html', seznam=seznam,nadpis=nadpis)

@app.route('/')
def index():
    db = get_db()
    seznam_restauraci = db.execute("SELECT * FROM restaurace LIMIT 3").fetchall()
    obrazky_restauraci = {
        'Asia Bistro' : 'static/rest1.jpg',
        'Kebabarna' : 'static/rest_kebab.jpg',
        'India Restaurant' : 'static/rest2.jpg',
        'India Brno' : 'static/rest3.jpg',
        'Kebab Brno' : 'static/rest4.jpg'
    }
    obrazky_kategorii = {
        'indicka': 'static/indicka.jpg',
        'turecka': 'static/turecka.jpg',
        'asijska': 'static/asijska.jpg',
        'ceska' : 'static/ceska.jpg'
    }
    seznam_kategorii = db.execute("SELECT DISTINCT typ_restaurace FROM restaurace LIMIT 3 ").fetchall()
    uzivatel_prihlasen = session.get('prihlasen', False)
    aktualni_uzivatel = session.get('aktualni_uzivatel', {})
    session['z_vyhledavani'] = False
    je_admin = session.get('je_admin')
    id_posliceka = session.get('id_uzivatele')
    je_poslicek = session.get('je_poslicek')
    vyrizeny_dotaz =  """
        SELECT o.id_objednavky, o.datum_objednani, o.stav, d.adresa
        FROM objednavka o
        JOIN doruceni d ON o.id_objednavky = d.objednavka_id_objednavky
        WHERE o.stav = 'Vyřízena' OR o.stav = 'doručuje se'
        """
    dorucovane_dotaz = """
    SELECT o.id_objednavky, o.datum_objednani, o.stav, d.adresa
    FROM objednavka o
    JOIN doruceni d ON o.id_objednavky = d.objednavka_id_objednavky
    WHERE o.stav = 'doručuje se' AND o.uzivatel_id_uzivatele= ?
    """
    vyrizeny_objednavky = db.execute(vyrizeny_dotaz).fetchall()
    dorucovane_objednavky = db.execute(dorucovane_dotaz, (id_posliceka,)).fetchall()

    #vyrizeny_objednavky = db.execute(vyrizeny_dotaz).fetchall()
    objednavky_s_polozkami = []

    for objednavka in vyrizeny_objednavky:
        id_objednavky = objednavka['id_objednavky']

        polozky = db.execute("SELECT p.popis, p.nazev FROM polozky_objednavky po JOIN polozky p ON po.id_polozky = p.id_polozky WHERE po.id_objednavky = ?", (id_objednavky,)).fetchall()

        objednavka_s_polozkami = {
            'id_objednavky': objednavka['id_objednavky'],
            'datum_objednani': objednavka['datum_objednani'],
            'adresa': objednavka['adresa'],
            'stav': objednavka['stav'],
            'polozky': polozky,
            }

        objednavky_s_polozkami.append(objednavka_s_polozkami)


    return render_template('index.html',obrazky_kategorii = obrazky_kategorii, obrazky_restauraci = obrazky_restauraci,uzivatel_prihlasen=uzivatel_prihlasen, aktualni_uzivatel=aktualni_uzivatel, je_poslicek = je_poslicek, je_admin = je_admin, seznam_restauraci = seznam_restauraci, seznam_kategorii = seznam_kategorii, vyrizeny_objednavky = objednavky_s_polozkami, dorucovane_objednavky = dorucovane_objednavky)

@app.route('/prijmout_objednavku/<int:id_objednavky>', methods=['POST'])
def prijmout_objednavku(id_objednavky):
    
    try:
        db = get_db()
        db.execute("UPDATE objednavka SET stav = 'doručuje se' WHERE id_objednavky = ?", (id_objednavky,))  
        db.commit()
        if 'cas_doruceni' in request.form:
            cas_doruceni_input = request.form['cas_doruceni']
            cas_doruceni = datetime.strptime(cas_doruceni_input, "%Y-%m-%dT%H:%M")
            db.execute("UPDATE doruceni SET cas_doruceni = ? WHERE objednavka_id_objednavky = ?", (cas_doruceni, id_objednavky))
            db.commit()
        msg = "Objednávka byla přijata a doručuje se."
        print(msg)
    except Exception as e:
        msg = f"Došlo k chybě při přijímání objednávky: {str(e)}"
        print(msg)

    cas_do_doruceni(cas_doruceni)
    return redirect(url_for('index'))

@app.route('/zmenit_role/<int:id_uzivatele>', methods=['POST'])
def zmenit_role(id_uzivatele):
    try:
        nove_role = [int(role) for role in request.form.getlist('role[]')]
        db = get_db()
        # Odstranění stávajících rolí
        db.execute("DELETE FROM role_uzivatel WHERE id_uzivatele = ?", (id_uzivatele,))
        # Přidání nových rolí
        for nova_role in nove_role:
            db.execute("INSERT INTO role_uzivatel (id_uzivatele, id_role) VALUES (?, ?)", (id_uzivatele, nova_role))
        db.commit()
        msg = "Role byly úspěšně aktualizovány."
        print(msg)
    except Exception as e:
        msg = f"Došlo k chybě při aktualizaci rolí: {str(e)}"
        print(msg)
    return redirect(url_for('admin_panel'))

@app.route('/potvrdit_doruceni/<int:id_objednavky>',methods = ['POST'])
def potvrdit_doruceni(id_objednavky):
    try:
        db = get_db()
        db.execute("UPDATE objednavka SET stav = 'doruceno' WHERE id_objednavky = ?", (id_objednavky,))
        db.commit()
        msg = "Doručení objednávky bylo potvrzeno."
        print(msg)
    except Exception as e:
        msg = f"Došlo k chybě: {str(e)}"
        print(msg)

    return redirect(url_for('index'))
# Zkouška menu neboli snaha o inicializování, což by mělo záviset na id_restaurací, jelikož každá restaurace bude mít jiné menu
# Podle dokumentace, kterou jsem si vyhledal, by to možná bylo možné takhle
@app.route('/menu/<int:id_restaurace>')
def zobraz_menu(id_restaurace):
    db = get_db()
    restaurace = db.execute("SELECT * FROM restaurace WHERE id_restaurace = ?", (id_restaurace,)).fetchone()
    # získání nabídky restaurace
    nabidka = db.execute("SELECT * FROM nabidka JOIN restaurace ON (nabidka.restaurace_id_restaurace = restaurace.id_restaurace) WHERE restaurace.id_restaurace = ? ", (id_restaurace,)).fetchall()
    # hodí se asi seznam pro položky
    polozky = []

    # pro každou položku v nabídce
    for polozka in nabidka:
        polozky_nabidky = db.execute("SELECT * FROM polozky WHERE nabidka_id_nabidky = ?", (polozka['id_nabidky'],)).fetchall()
        polozky.extend(polozky_nabidky)

    z_vyhledavani = request.args.get('z_vyhledavani', False)
    session['z_vyhledavani'] = z_vyhledavani

    return render_template('menu.html', restaurace=restaurace, nabidka=nabidka, polozky=polozky, id_restaurace=id_restaurace, z_vyhledavani=z_vyhledavani)


# Přidání položky do košíku
@app.route('/pridat_do_kosiku', methods=['POST'])
def pridat_do_kosiku():
    try:
        # Získání id položky a id uživatele z formuláře
        id_polozky = request.form['id_polozky'] 
        id_uzivatele = session.get('id_uzivatele')

        # Pokud uživatel není přihlášen, přesměruj na přihlašovací stránku
        if not id_uzivatele:
            return redirect(url_for('prihlaseni'))

        # Přidání položky do tabulky Kosik
        db = get_db()
        db.execute("INSERT INTO Kosik (id_uzivatele, id_polozky) VALUES (?, ?)", (id_uzivatele, id_polozky))
        db.commit()

        msg = "Položka byla úspěšně přidána do košíku."
        print(msg)
    except Exception as e:
        msg = f"Došlo k chybě při přidávání do košíku: {str(e)}"
        print(msg)

    return redirect(url_for('index'))



# Zobrazí obsah košíku
@app.route('/kosik')
def zobraz_kosik():
    # Pokud uživatel není přihlášen, přesměruj na přihlašovací stránku
    if 'id_uzivatele' not in session:
        return redirect(url_for('prihlaseni'))

    try:
        db = get_db()
        id_uzivatele = session['id_uzivatele']
        
        # Získání položek v košíku pro aktuálního uživatele
        kosik = db.execute("""
            SELECT p.nazev, p.cena
            FROM Kosik k
            JOIN polozky p ON k.id_polozky = p.id_polozky
            WHERE k.id_uzivatele = ?
        """, (id_uzivatele,)).fetchall()


        return render_template('kosik.html', kosik=kosik)

    except Exception as e:
        msg = f"Došlo k chybě při načítání košíku: {str(e)}"
        print(msg)
        return "Chyba při načítání košíku."

# Objednání obsahu košíku
@app.route('/objednat', methods=['POST'])
def objednat():
    # Pokud uživatel není přihlášen, přesměruj na přihlašovací stránku
    if 'id_uzivatele' not in session:
        return redirect(url_for('prihlaseni'))

    try:
        db = get_db()
        id_uzivatele = session['id_uzivatele']
        

        # Získání položek v košíku pro aktuálního uživatele
        kosik = db.execute("SELECT * FROM Kosik WHERE id_uzivatele = ?", (id_uzivatele,)).fetchall()

        if kosik:
            # Vytvoření nového záznamu objednávky v tabulce "objednavka"
            datum_objednani = datetime.now().strftime("%Y-%m-%d")
            cas_objednani = datetime.now().strftime("%H:%M:%S")
            stav = "Nová"
            historie = "Objednávka vytvořena"
            financni_operace_id_financni_operace = 1
            celkova_castka = soucet_cen(id_uzivatele)
            
          
            
            # Získání ID posledně vložené objednávky
            db.execute("INSERT INTO objednavka (datum_objednani, cas_objednani, uzivatel_id_uzivatele, stav, historie, financni_operace_id_financni_operace) VALUES (?, ?, ?, ?, ?, ?)",
                       (datum_objednani, cas_objednani, id_uzivatele, stav, historie, financni_operace_id_financni_operace))
            db.commit()

           
            id_objednavky = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for polozka in kosik:
                
        
                db.execute("INSERT INTO polozky_objednavky (id_objednavky, id_polozky) VALUES (?,?)",(id_objednavky,polozka['id_polozky']))

            # Přesun položek z košíku do tabulky detail_objednavky (přizpůsobte název tabulky podle vašich aktuálních dat)
           
  

            # Vyčištění položek v košíku pro aktuálního uživatele
            db.execute("DELETE FROM Kosik WHERE id_uzivatele = ?", (id_uzivatele,))
            db.commit()

        return redirect(url_for('platba', celkova_castka = celkova_castka, id_objednavky = id_objednavky))

    except Exception as e:
        msg = f"Došlo k chybě při vytváření objednávky: {str(e)}"
        print(msg)
        return "Chyba při vytváření objednávky."

@app.route('/platba', methods=['GET', 'POST'])
def platba():
    if request.method == 'POST':
        # Zpracování dat z formuláře
        cislo_uctu = request.form['cislo_uctu']
        celkova_castka = request.form['celkova_castka']
        cas_datum_provedeni = datetime.now()
        typ_operace = "platba"
        id_objednavky = request.form['id_objednavky']
        id_uzivatele = session['id_uzivatele']
        cas_doruceni = cas_datum_provedeni + timedelta(minutes=60)
              
    
  
        db = get_db()
        adresa = db.execute("SELECT adresa FROM uzivatel WHERE id_uzivatele = ?", (id_uzivatele,)).fetchone()[0] 
        db.execute("UPDATE objednavka SET stav = 'Vyřízena' WHERE id_objednavky = ?", (id_objednavky,))
        db.commit()
        db.execute("""
            INSERT INTO financni_operace (cas_datum_provedeni, typ_operace, celkova_castka, cislo_uctu)
            VALUES (?, ?, ?, ?)
        """, (cas_datum_provedeni, typ_operace, celkova_castka, cislo_uctu))
        db.commit()
        id_financni_operace = db.execute("SELECT last_insert_rowid() FROM financni_operace").fetchone()[0]
        db.execute("""
            UPDATE objednavka SET financni_operace_id_financni_operace = ? WHERE id_objednavky = ?
        """, (id_financni_operace, id_objednavky))
        db.commit()

        db.execute("""INSERT INTO doruceni (cas_doruceni, uzivatel_id_uzivatele, objednavka_id_objednavky, adresa) VALUES(?,?,?,?)
                   """, (cas_doruceni, id_uzivatele, id_objednavky, adresa))
        db.commit()
        
       
        # Přesměrování na hlavní stránku
        return redirect(url_for('index'))

    else:
        # Zobrazení formuláře
        celkova_castka = request.args.get('celkova_castka')
        id_objednavky = request.args.get('id_objednavky')
        return render_template('platba.html', celkova_castka=celkova_castka, id_objednavky = id_objednavky)

"""@app.route('/hodnoceni/<int:id_objednavky>', methods=['POST'])
def zpracuj_hodnoceni(id_objednavky):
    try:
        hodnoceni = request.form['hodnoceni']
        db = get_db()
        db.execute("UPDATE objednavka SET hodnoceni = ? WHERE id_objednavky = ?", (hodnoceni, id_objednavky))
        db.commit()
        msg = "Hodnocení bylo úspěšně uloženo"
        print(msg)
    except Exception as e:
        msg = f"Došlo k chybě: {str(e)}"
        
        print(msg)
    return redirect(url_for('index'))"""

@app.route('/registrace', methods=['GET', 'POST'])
def registrace():
    if request.method == 'POST':
        jmeno = request.form['jmeno']
        prijmeni = request.form['prijmeni']
        email = request.form['email']
        adresa = request.form['adresa']
        heslo = hashovat_heslo(request.form['heslo'])
        tel_cislo = request.form['tel_cislo']

        try:
            
            db = get_db()
            id = db.execute("INSERT INTO Uzivatel ('jmeno', 'prijmeni', 'email', 'adresa', 'heslo', 'tel_cislo') VALUES (?, ?, ?, ?, ?, ?)", (jmeno, prijmeni, email, adresa, heslo, tel_cislo))
            db.commit()
            novy_uzivatel = id.lastrowid
            role = 2
            db.execute("INSERT INTO role_uzivatel ('id_role', 'id_uzivatele') VALUES (?, ?)", (role,novy_uzivatel))
            db.commit()
            msg = "Registrace proběhla úspěšně"
            print(msg)
        except sqlite3.Error as e:
            msg = "Došlo k chybě při registraci" + str(e)
            print(msg)


        return redirect(url_for('index'))  

    return render_template('registrace.html')



@app.route('/prihlaseni', methods=['POST', 'GET'])
def zobrazit_prihlaseni():
    return prihlaseni()
def overit_heslo(email, heslo):
    db = get_db()
    uzivatel = db.execute("SELECT * FROM Uzivatel WHERE email = ?", (email,)).fetchone()
    if uzivatel and checkpw(heslo.encode('utf-8'), uzivatel['heslo'].encode('utf-8')):
        return uzivatel
    return None

def hashovat_heslo(heslo):
    return hashpw(heslo.encode('utf-8'), gensalt()).decode('utf-8')

def je_admin(id_uzivatele):
    db = get_db()
    role = db.execute("SELECT id_role FROM role_uzivatel where id_uzivatele = ?", (id_uzivatele,)).fetchone()
    return role['id_role'] == 1 if role else False

def je_poslicek(id_uzivatele):
    db = get_db()
    role = db.execute("SELECT id_role FROM role_uzivatel where id_uzivatele = ?", (id_uzivatele,)).fetchone()
    return role['id_role'] == 3 if role else False

def zjisti_roli_uzivatele(id_uzivatele):
    db = get_db()
    admin = db.execute("SELECT id_role FROM role_uzivatel where id_uzivatele = ?", (id_uzivatele,)).fetchone()
    return admin['id_role'] if admin else None

def prihlaseni():
    chybny_udaj = None
    if request.method == 'POST':
        email = request.form['email']
        heslo = request.form['heslo']
        uzivatel = overit_heslo(email,heslo)
        


        if uzivatel:
            prihlasit_uzivatele(uzivatel['id_uzivatele'], uzivatel['jmeno'])
            session['jmeno'] = uzivatel['jmeno']
            session['prijmeni'] = uzivatel['prijmeni']

            return redirect(url_for('index'))
        else:
            chybny_udaj = "Špatně zadán email nebo heslo."
    
    return render_template('prihlaseni.html', chybny_udaj=chybny_udaj)

        
@app.route('/odhlaseni')
def odhlaseni():
    odhlasit_uzivatele()
    return redirect(url_for('index'))



@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    try:
        db = get_db()
        # Zkontroluje, zda uživatel je admin před tím, než přistoupí k administračnímu panelu
        if not je_admin():
            return "Nemáte oprávnění k přístupu na tuto stránku." 
        
        dataUzivatele = db.execute("SELECT id_uzivatele, jmeno, prijmeni FROM uzivatel")
        data = db.execute("SELECT nazev_restaurace FROM restaurace").fetchall()

        return render_template('admin_panel.html', data=data, dataUzivatele=dataUzivatele)
    except Exception as e:
        msg = f"Došlo k chybě při načítání administračního panelu: {str(e)}"
        print(msg)
        app.logger.error(msg)
        return "Administrátorský panel načten úspěšně."

@app.route('/smazat_restauraci', methods=['POST'])
def smazat_restauraci():
    try:
        db = get_db()
        nazev_restaurace = request.form.get('nazev_restaurace')
        smazat_restauraci_v_databazi(db, nazev_restaurace)
        return redirect(url_for('admin_panel'))
    except Exception as e:
        msg = f"Došlo k chybě při mazání restaurace: {str(e)}"
        print(msg)
        return "Chyba při mazání restaurace."

def smazat_restauraci_v_databazi(db, nazev_restaurace):
    db.execute("DELETE FROM restaurace WHERE nazev_restaurace = ?", (nazev_restaurace,))
    db.commit()
 
@app.route('/pridat_restauraci', methods=['POST', 'GET'])
def pridat_restauraci():
    if request.method == 'POST':
        nazev_restaurace = request.form['nazev_restaurace']
        typ_restaurace = request.form['typ_restaurace']
        adresa = request.form['adresa']
        telefonni_cislo = request.form['telefonni_cislo']
        email = request.form['email']

        try:
            db = get_db()
            db.execute("INSERT INTO Restaurace ('nazev_restaurace', 'typ_restaurace', 'adresa', 'telefonni_cislo', 'email') VALUES (?, ?, ?, ?, ?)", (nazev_restaurace, typ_restaurace, adresa, telefonni_cislo, email))
            db.commit()
            msg = "Restaurace byla úspěšně přidána"
            print(msg)
        except:
            msg = "Došlo k chybě při přidávání restaurace"
            print(msg)

    return render_template('pridat_restauraci.html')

def je_admin():
    # Kontroluje, zda má aktuální uživatel roli 'admin'
    if 'id_uzivatele' in session:
        id_uzivatele = session['id_uzivatele']
        db = get_db()
        # Dotaz na tabulku role_uzivatel, zda má uživatel roli 'admin', musi 
        result = db.execute("SELECT COUNT(*) FROM role_uzivatel ru JOIN role r ON ru.id_role = r.id_role WHERE ru.id_uzivatele = ? AND r.nazev = 'Admin'", (id_uzivatele,)).fetchone()
        return result[0] > 0  # True, pokud má uživatel roli 'admin', jinak False
    return False  # Žádné ID uživatele v session, takže není admin
def je_poslicek():
    if 'id_uzivatele' in session:
        id_uzivatele = session['id_uzivatele']
        db = get_db()
        result = db.execute("SELECT COUNT(*) FROM role_uzivatel ru JOIN role r ON ru.id_role = r.id_role WHERE ru.id_uzivatele = ? AND r.nazev = 'Poslicek'", (id_uzivatele,)).fetchone()
        return result[0] > 0
    return False

  

if __name__ == '__main__':
    app.run(debug=True)
