# MLS MLS webová aplikace

Tato aplikace slouží k online objednávání jídla z různých restaurací. Uživatelé se mohou registrovat, prohlížet nabídky restaurací, přidávat položky do košíku a odesílat objednávky. Administrátoři mají přístup k administrátorskému panelu, kde mohou spravovat restaurace a uživatele.

## Struktura aplikace

### Flask Aplikace

Hlavní část aplikace je napsána pomocí Flask frameworku. Flask poskytuje jednoduchý způsob, jak vytvořit webovou aplikaci s Pythonem.

### Databáze

Aplikace používá SQLite databázi k ukládání informací o uživatelích, restauracích, objednávkách a dalších relevantních datech a je uložena v souboru `projekt.db`. Funkce `get_db` spravuje připojení k databázi pomocí objektu `g` z knihovny Flask.

Během práce na projektu jsme zjistili nedostatky, které naše práce měla v původní dokumentaci. Bylo to hlavně skrz databázi. Přidali jsme nové tabulky, skrz evidenci položek daného uživatele v košíku při objednávání a také propojovací tabulku položek a objednávek, abychom přesně věděli, které položky patřily, k jaké objednávce, jelikož jich může být víc.

Bylo nutné přidat tabulku Kosik a Polozky_objednavky, jelikož v rámci objednávky může být více položek a položky mohou patřit k více objednávkám. Potřebovali jsme to evidovat, abychom věděli, ke které objednávce jednotlivé položky patří. V tabulce Kosik se eviduje to, co si daný uživatel (jedná se o uživatele v dané relaci) objednal za položky k objednávce.

## Funkcionality

### Registrace a přihlášení

Uživatelé se mohou registrovat pomocí formuláře na stránce `/registrace`. Při registraci jsou shromažďovány informace jako jméno, příjmení, e-mail, adresa, heslo a telefonní číslo. Přihlášení je umožněno na stránce `/prihlaseni`. Po úspěšném přihlášení jsou uživatelé přesměrováni na hlavní stránku a na základě jejich role mohou provádět operace.

### Prohlížení kategorii restaurací

Uživatelé mohou prohlížet restaurace v dané kategorii na stránce `/restaurace/<typ_restaurace>`.

### Objednávání jídla

Uživatelé mohou přidávat položky do košíku na stránce `/menu/<id_restaurace>`. Po přidání položek do košíku mají možnost provést objednávku, která je poté zobrazena na stránce `/kosik`.

### Objednání a Doručení

Po potvrzení objednávky uživatelé mohou přejít na stránku `/platba`, kde mohou provést platbu za svou objednávku. Po úspěšné platbě je objednávka označena jako "Vyřízena" a připravena k doručení. Poté, když poslíček danou objednávku doručí, potvrdí doručení a stav objednávky se změní na “Doručena”.

### Administrace

Administrátoři mají přístup k administrátorskému panelu na stránce `/admin_panel`. Zde mohou spravovat restaurace a uživatele, mazat restaurace a měnit role uživatelů.

Aplikace obsahuje bezpečnostní mechanismy, jako je hashování hesel pomocí knihovny bcrypt.
