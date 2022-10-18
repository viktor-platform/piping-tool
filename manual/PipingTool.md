- [Introductie](#Introductie)
  - [Inhoud document](#Inhoud-document)
  - [Wat is de Piping Tool?](#Wat-is-de-Piping-Tool)
  - [Opbouw tool](#Opbouw-tool)
  - [Opbouw invoer](#Opbouw-invoer)
  - [Vragen en suggesties](#Vragen-en-suggesties)
- [Handleiding](#Handleiding)
  - [Navigeren in VIKTOR](#Navigeren-in-VIKTOR)
  - [Stap 1: Aanmaken nieuw project](#Stap-1-Aanmaken-nieuw-project)
  - [Stap 2: Laden van invoer bestanden (algemeen)](#Stap-2-Laden-van-invoer-bestanden-algemeen)
    - [3D grondmodel](#3D-grondmodel)
    - [Sonderingen](#Sonderingen)
    - [Boringen](#Boringen)
  - [Stap 4: Van Project naar Dijkvak](#Stap-4-Van-Project-naar-Dijkvak)
  - [Stap 5: Van Dijkvak naar Uittredepunt](#Stap-5-Van-Dijkvak-naar-Uittredepunt)
    - [Tussenstap 1: Input selectie](#Tussenstap-1-Input-selectie)
    - [Tussenstap 2: Geohydrologie](#Tussenstap-2-Geohydrologie)
    - [Tussenstap 3: Genereren uittredepunten](#Tussenstap-3-Genereren-uittredepunten)
    - [Tussenstap 4: Berekeningen](#Tussenstap-4-Berekeningen)
- [Achtergrond input](#Achtergrond-input)
  - [Invoeren van lijnen uit QGIS](#Invoeren-van-lijnen-uit-QGIS)
    - [Stap 1: Maak een LineString.](#Stap-1-Maak-een-LineString)
    - [Stap 2: Exporteer de laag als shapefile](#Stap-2-Exporteer-de-laag-als-shapefile)
    - [Stap 3: Genereer .zip file](#Stap-3-Genereer-zip-file)
  - [3D grondmodel](#3D-grondmodel-1)
  - [Afsnijden 3D grondmodel](#Afsnijden-3D-grondmodel)
  - [Sloten uit QGIS](#Sloten-uit-QGIS)
    - [Stap 1: Importeer de slootdata in QGIS](#Stap-1-Importeer-de-slootdata-in-QGIS)
    - [Stap 2: Teken polygon van interessegebied](#Stap-2-Teken-polygon-van-interessegebied)
    - [Stap 3: Knip de sloten af op de polygon](#Stap-3-Knip-de-sloten-af-op-de-polygon)
    - [Stap 4: Exporteer de afgesneden lagen](#Stap-4-Exporteer-de-afgesneden-lagen)
  - [Bathymetrie](#Bathymetrie)
    - [Stap 1: Download bathymetrie data](#Stap-1-Download-bathymetrie-data)
    - [Stap 2: Upload bathymetrie data naar QGIS](#Stap-2-Upload-bathymetrie-data-naar-QGIS)
    - [Stap 3: Teken polygon](#Stap-3-Teken-polygon)
    - [Stap 4: Knip de bathymetrie af](#Stap-4-Knip-de-bathymetrie-af)
    - [Stap 5: Exporteer de afgeknipte bathymetrie](#Stap-5-Exporteer-de-afgeknipte-bathymetrie)
- [Technische achtergrond](#Technische-achtergrond)

# Introductie
## Inhoud document
Dit document presenteert de handleiding voor de tool voor het bepalen van het faalmechanisme piping. Dit document is opgesteld als werkhandleiding voor het gebruik van de applicatie in VIKTOR.

## Wat is de Piping Tool?
---Nog te schrijven---

## Opbouw tool
De tool is grofweg ingedeeld in een drietal niveaus:
1.	Project
2.	Dijkvak
3.	Uittredepunt

Het project-niveau is het hoogste niveau en wordt gedefinieerd door de kruinlijn van de dijk die gebruikt wordt om het project aan te maken. Op het projectniveau is het mogelijk om invoer te uploaden en om, op basis van deze invoer, dijkvakken te selecteren. Op het projectniveau wordt het volgende beheerd:

- Intredelijn
- Sloten
- 3D grondmodel
- Sonderingen en boringen
- Bathymetrie

Binnen een project kunnen één of meerdere dijkvakken worden aangemaakt. Deze dijkvakken hoeven niet aan te sluiten of het hele tracé te dekken maar vallen wel binnen de kruinlijn van het project. Het is mogelijk om meerdere dijkvakken aan te maken die overlappen. Berekeningen worden alleen uitgevoerd binnen een dijkvak. Een dijkvak wordt gegenereerd op projectniveau. Alle dijkvakken behoren toe aan een project. Op het dijkvakniveau wordt het volgende beheerd:

- Geohydrologisch model
- Dijkvak grondschematisering
- Achterland en voorland

Binnen een dijkvak worden uittredepunten gedefinieerd. Alle uittredepunten behoren aan een dijkvak toe. Deze uittredepunten representeren locaties waarop een pipingcontroles plaatsvinden. Uittredepunten vormen ook de basis voor de 2D secties voor de terugschrijdende erosie en het genereren van een D-Geoflow file.

## Opbouw invoer
De aanpak die wordt gehanteerd is gebaseerd op het zoveel mogelijk gebruik maken van beschikbare data in standaard formats. Dit gezien het voor de gebruiker vaak praktischer is om met invoerbestanden te werken dan grote hoeveelheid data handmatig in een applicatie invoeren. De minimaal benodigde invoer voor het uitvoeren van berekeningen met de tool is de volgende:
1.	Kruinlijn van de dijk in .zip formaat. Zie [invoer kruinlijn](##Kruinlijn-van-de-dijk) .
2.	Intredelijn in .zip formaat. Zie bijlage.
3.	Grondparameters in .xlsx formaat conform vereiste layout. Zie bijlage.
4.	Grond interpretatie in .xlsx formaat conform vereiste layout. Zie bijlage.

Optionele invoerbestanden zijn:

1.	3D grondmodel in .csv formaat conform vereiste layout. Zie bijlage. Buiten de dekkingsdiepte van dit model wordt de REGIS data gebruikt.
2.	Bathymetrie bestand in .xyz formaat conform vereiste layout. Zie bijlage. Buiten de dekking van dit bestand wordt gebruik gemaakt van AHN data.
3.	Sondering en borings data in .GEF of .xml formaat.
4.	Gegevens over sloten data gebaseerd op uitvoer van legger. Zie handleiding.

## Vragen en suggesties
-- nog te doen --

# Handleiding
## Navigeren in VIKTOR
Navigeren in VIKTOR is gebruiksvriendelijk en kan op een aantal manieren. In de basis is het mogelijk om boven in het scherm van niveau te veranderen.

![Screenshot](./img/Navigeren_in_VIKTOR_1.png?csf=1&web=1&e=sIdfhqg)

In de VIKTOR omgeving is het mogelijk om een nieuw project aan te maken. Op het lagere niveau wordt met tabbladen gewerkt binnen het huidige niveau.

Met het kleine icoon links van het VIKTOR logo kan ook het linker menu worden geopend.

![Screenshot](./img/Navigeren_in_VIKTOR_2.png?csf=1&web=1&e=sIdfhqg)

In het rechter menu kan de gebruiker navigeren. Belangrijk is hier de “Back” (terug) knop om een stap terug te gaan en de “Children” (kinderen) knop waarmee naar onderliggende niveaus kan worden gegaan. Op projectniveau zijn hier de dijkvakken te zien en op dijkvakniveau de uittredepunten.

![Screenshot](./img/Navigeren_in_VIKTOR_3.png?csf=1&web=1&e=sIdfhqg)

Wijzigingen kunnen worden opgeslagen met de "Save" knop. Het is daarbij mogelijk om aan te geven welke wijzingen waarom zijn doorgevoerd.

---

Let op: Afhankelijk van de hoeveelheid data (e.g. sonderingen en uittredepunten) kan het soms enige tijd vergen om de pagina's te updaten. In de rechterbovenhoek zal het blokje "Working" in "Finished" verandering als de data is bijgewerkt.

---

## Stap 1: Aanmaken nieuw project
In de tool is het mogelijk om een nieuw project aan te maken.

Klik op de “[Projects](https://hdsr.viktor.ai/workspaces/1/app/object/1?entity_type=2&limit=10&offset=0&sort=updated_at%3Adesc])” map in de verkenner aan de linkerkant van het scherm. 

![Screenshot](./img/Nieuw_project_aanmaken_1.png?csf=1&web=1&e=sIdfhqg)

Klik op de “Create a new object” knop. Kies bij “Object Type” voor “Dyke”.

![Screenshot](./img/Nieuw_project_aanmaken_2.png?csf=1&web=1&e=sIdfhqg)

Sleep een [kruinlijn bestand in .zip formaat](##Kruinlijn-van-de-dijk) naar het upload scherm. 

Het project krijgt als standaard dezelfde naam als het .zip bestand. Dit kan worden gewijzigd met de “…” knop aan de rechterkant van het project. Hier kan je ook het project verwijderen of kopiëren.

![Screenshot](./img/Nieuw_project_aanmaken_3.png?csf=1&web=1&e=sIdfhqg)

## Stap 2: Laden van invoer bestanden (algemeen)
### 3D grondmodel
 Het 3D grondmodel is de basis van veel van de berekeningen. Het model is gebaseerd op de 3D modellen van TNO als opgesteld voor Sterke Lekdijk maar het is ook mogelijk om andere modellen te gebruiken mits deze in hetzelfde [formaat](##3D-grondmodel) worden gebruikt.

Selecteer de “[Models](https://hdsr.viktor.ai/workspaces/1/app/object/2?entity_type=9&limit=10&offset=0&sort=updated_at%3Adesc) folder” en klik op de “Create” knop.

![Screenshot](./img/Invoer_1.png?csf=1&web=1&e=sIdfhqg)

Sleep het 3D model naar het upload scherm. Het model krijgt als standaard dezelfde naam als het .zip bestand. Dit kan worden gewijzigd met de “…” knop aan de rechterkant van het project. Hier kan je ook het project verwijderen of kopiëren.

![Screenshot](./img/Invoer_2.png?csf=1&web=1&e=sIdfhqg)

De webapplicatie gaat wat minder goed om met grote bestanden. Daarnaast vragen deze bestanden veel geheugen. Het is mogelijk om een grote dataset [af te snijden](##Afsnijden_3D_grondmodel) in het gebied van interesse.

### Sonderingen
Het is mogelijk om sonderingen toe te voegen aan het project. 

Klik op de “[Projects](https://hdsr.viktor.ai/workspaces/1/app/object/1?entity_type=2&limit=10&offset=0&sort=updated_at%3Adesc])” map in de verkenner aan de linkerkant van het scherm en klik op de “Create” knop. Kies bij “Object Type” voor “CPT folder” en geef de folder een naam. Klik dan op “Create and browse”. Het is mogelijk om één of meerdere .gef of .xml bestanden tegelijk te uploaden.

![Screenshot](./img/Invoer_3.png?csf=1&web=1&e=sIdfhqg)

### Boringen
Het is mogelijk om boringen aan het project toe te voegen.

Klik op de “[Projects](https://hdsr.viktor.ai/workspaces/1/app/object/1?entity_type=2&limit=10&offset=0&sort=updated_at%3Adesc])” map in de verkenner aan de linkerkant van het scherm. Klik op de “Create” knop. Kies bij “Object Type” voor “Boreholes folder” en geef de folder een naam. Klik dan op “Create and browse”. In de Boreholes folder klik op “create object” om sonderingen te uploaden. Het is mogelijk om één of meerdere .gef of bestanden tegelijk te uploaden.

![Screenshot](./img/Invoer_4.png?csf=1&web=1&e=sIdfhqg)

## Stap 4: Van Project naar Dijkvak
Binnen een project is het mogelijk om één of meerdere dijkvakken aan te maken.

Selecteer het project en kies voor “[Open](https://hdsr.viktor.ai/workspaces/1/app/editor/1243)”.

![Screenshot](./img/Step_4_1.png?csf=1&web=1&e=sIdfhqg)

Het project opent. In de “Data input” staan de gegevens van het project. In het vak “Traject” staan de gegevens van de kruinlijn. Deze punten kunnen aangepast worden door de punten te wijzigen door op het pijltje naar beneden te drukken of door met het pen icoontje de punten op de kaart te verschuiven. De wijzigingen kunnen worden opgeslagen met “Accept Modification”.

In het "Data input" tab is het ook mogelijk om de metrering van de kruinlijn aan te passen. Dit heeft invloed op de nauwkeurigheid van de 2D bodemopbouw en bepaald de minimale lengte van een dijkvak. Daarnaast is het mogelijk om de richting van de metrering om te draaien en om de oriëntatie t.o.v. de rivier van de kruinlijn aan te passen (het blauwe pijltje dient altijd naar de rivier te wijzen). Met de knop “Detecteer automatisch aslengte” wordt de stapgrootte automatisch gekozen.

Voor de overige invoer open het vak “Input data selectie” met het pijltje. Hier kunnen de [intredelijn](##Intredelijn) (verplicht), [sloten](##Sloten) (optioneel), [bathymetrie](##Sloten) (optioneel) en dijkpalen (optioneel) worden toegevoegd door op de blauwe wolkjes te drukken naast de drop down boxen. Daarnaast kunnen de CPT folder (optioneel), Boringenfolder(optioneel) en het TNO model (verplicht) voor het project worden geselecteerd. Als de data is geupload dan kan deze worden geselecteerd in de dropdown menu’s in het “Input data selectie” vak. Druk op “Update” om de invoer ook op de kaart te laten zien.

NB: Boringen en sonderingen kunnen worden bekeken door op de icoontjes op de kaart te drukken.

![Screenshot](./img/Step_4_2.png?csf=1&web=1&e=sIdfhqg)

In het rechter tab “2D Grondopbouw” kan het 2D grondprofiel worden bekeken. Dit profiel bestaat uit het 3D model aangevuld met het REGIS model. 

In het linker tab "Visualisatie opties" kan hier ook een andere lijn worden gekozen, via upload of op tab "Kaart" getekende lijn worden gekozen. De diepte van het Regis model kan hier worden aangepast. Ook kan de schaal en de maximale afstand tot waar sonderingen en boringen worden weergegeven worden aangepast. Na veranderingen is het altijd noodzakelijk om rechtsonder op "Update" te drukken.

In het rechterscherm kunnen zowel de bodemopbouw uit het 3D model als de geinterpreteerde bodemopbouw en de doorlatendheden worden weergegeven.

NB: Door met de muis over het 2D profiel te gaan verschijnt in de rechterbovenhoek een aantal opties om in en uit te zoomen.

![Screenshot](./img/Step_4_3.png?csf=1&web=1&e=sIdfhqg)

In het "Grondopbouw" tab kunnen het materiaalmodel en de classificatietabel bekenen en aangepast worden. Het materiaalmodel is het geotechnisch model voor het project dat gebruikt wordt om de de berekeningen uit te voren. Dit model wordt typisch door de geotechnisch ingenieurs opgesteld voor het project. Om de lagen van het 3D grondmodel te vertalen naar de juiste geotechnische materialen met de juiste parameters is het mogelijk om wat logische regels te maken. Dit kan in de “Classificatietabel 3D bodemopbouw”. Als voorbeeld kan een regel worden opgesteld dat een laag tussen +1m NAP en +5m NAP die in het 3D model geclassificeerd is als “Klei” wordt vertaald naar “Deklaag”. Later kunnen zowel deze regels als de uitkomsten op dijkvakniveau worden aangepast. Door in het 2D grondobouwscherm te kiezen voor “Geclassificeerde bodemobouw” is ook de classificatie te zien.

Zowel de Materiaaltabel als de Classificatietabel kunnen uit Excel gekopieeërd worden.

Let op: De classificatietabel dient compleet dekkend te zijn. Dus als de gebruiker zoals onderstaande definieerd dat Klei tussen +5m NAP en +1m NAP een deklaag betreft, dient er ook een definitie te zijn voor Klei beneden +1m NAP of boven +5m NAP als deze voorkomt.

![Screenshot](./img/Step_4_4.png?csf=1&web=1&e=sIdfhqg)

In het tab "Genereren Dijkvakken" is het mogelijk een dijkvak aan te maken op basis van bijvoorbeeld de 2D grondopbouw. Dit kan door een naam te geven en een start en eind  kilometrering. Druk op “Maak dijkvak” om het dijkvak aan te maken. Een project kan meerdere dijkvakken hebben en deze kunnen ook overlappen.

![Screenshot](./img/Step_4_5.png?csf=1&web=1&e=sIdfhqg)

Op het Dijkvakniveau is het mogelijk om, als de berekeningen zijn uitgevoerd, de data van het dijkvak te downloaden. Dit kan in het tab "Downloads".

## Stap 5: Van Dijkvak naar Uittredepunt
Als een dijkvak is aangemaakt is de volgende stap om binnen dit dijkvak de uittredepunten te genereren waar de berekeningen worden uitgevoerd. Hiervoor is het nodig om op Dijkvakniveau keuzes te maken. 

Om naar het zojuist aangemaakte Dijkvak te gaan is onder andere mogelijk om op projectniveau op het icoontje “Children” te klikken in de rechterbovenhoek. Dit geeft alle onderliggende onderdelen weer van het project. Kies hier voor “Dijkvak” en [open het gewenste dijkvak](https://hdsr.viktor.ai/workspaces/1/app/editor/1869).

![Screenshot](./img/Step_5_1.png?csf=1&web=1&e=sIdfhqg)

### Tussenstap 1: Input selectie
Nu opent het Dijkvak. In de bovenbalk is het ook mogelijk weer terug te gaan naar het projectniveau. In de viewer is het dijkvak in blauw te zien op de dijk. Het proces van dijkvak naar uittredepunten verloopt in een viertal tussenstappen die te zien zijn in de bovenkant van het scherm. Dit begint bij "Input selectie".

In de eerste tab “Algemeen” is het mogelijk een aantal zaken te laten zien in het scherm alsmede de kilometrering van het dijkvak nog aan te passen en kan de weergave van sonderingen, boringen, grondmodel en sloten worden getoond. Standaard worden alle sloten getoond maar het is mogelijk om hier alleen de sloten in het geselecteerde achterland te laten zien.

![Screenshot](./img/Step_5_2.png?csf=1&web=1&e=sIdfhqg)

In de tab "Materialen" kunnen de specifieke materiaalparameters voor het dijkvak ingevoerd worden. Deze kunnen met de knop "Reset tabellen naar de algemene dijkwaarden" ook worden geladen vanaf het projectniveau en eventueel aangepast naar dijkvakspecifieke waarden. De minimale dikte van de aquifer (gebruikt voor de automatische interpretatie) en de diepte van het Regis model kunnen hier ook worden aangepast.

![Screenshot](./img/Step_5_3.png?csf=1&web=1&e=sIdfhqg)

Voor het uitvoeren van de pipingberekeningen is het noodzakelijk om een 1D ondergrondmodel voor het dijkvak te definiëren. Dit omdat de lokale doorsnedes van het 3D ondergrondmodel niet representatief zijn voor het piping proces in het dijkvak. De tool helpt hier bij in het tab “Ondergrondschematisatie”. Hier kan op een bepaald punt langs de dijk een profiel worden gegeneerd dat vervolgens aangepast kan worden aan de hand van de rest van het vak en de boringen en sonderingen tot een representatief ondergrondprofiel. Dit kan door bij "Locatie meetpunt langs de dijk" een waarde in te vullen corresponderend met de x-as van de grafiek onder "2D bodemopbouw".

De gebruiker dient hier ook aquifers te selecteren voor de berekeningen. Dit kunnen er maximaal twee zijn. Als er meer dan één laag per aquifer is dan kunnen de effectieve eigenschappen van de aquifer worden bepaald aan de hand van de handreiking door te drukken op de knop "Bereken effectieve aquifer eigenschappen". Deze kunnen door de gebruiker aangepast worden. In onderstaand voorbeeld zijn er twee aquifers.

---

Let op: Het Regis model wordt niet automatisch geinterpreteerd. In het voorbeeld is een laag toegevoegd van Pleistoceen zand van -10 m NAP to -30 m NAP die de diepere aquifer weergeeft.

---

![Screenshot](./img/Step_5_4.png?csf=1&web=1&e=sIdfhqg)

Het is ook mogelijk om meer dan één schematisatie te hanteren. Dit kan bijvoorbeeld als er binnen een dijkvak twee mogelijke ondergrondschematisaties gelden. Dit kan door op "Add new row" te drukken of door een nieuwe waarde te kiezen voor "Locatie meetpunt langs de dijk". In onderstaand voorbeeld is een tweede scenario met één aquifer en een wegingsfactor van 0.2 meegegeven. De totale wegingsfactor dient 1.0 te zijn.

De scenario's kunnen worden gevisualiseerd in het rechter tab "Dijkvak" waarbij het te visualiseren scenario kan worden gekozen onder "Scenario te visualiseren" onder de linker tab "Ondergrondschematisatie".

![Screenshot](./img/Step_5_5.png?csf=1&web=1&e=sIdfhqg)

Als laatste is het in deze tussenstap mogelijk om de sloten mee te nemen voor het genereren van uittredepunten. Dit kan in de tab “Selecteer sloten”. De lengte waarin sloten in het achterland nog worden meegenomen kan heir worden ingevoerd. In het voorbeeld is gekozen om de bufferzone in te stellen op 250 m achter de kruinlijn en de watergangen daar af te snijden.

![Screenshot](./img/Step_5_6.png?csf=1&web=1&e=sIdfhqg)

### Tussenstap 2: Geohydrologie
Als de input selectie is afgerond drukt de gebruiker rechtsonder op “Stap 2: Geodydrologie”. Het is altijd mogelijk om weer terug te gaan naar de vorige stap. 

In de tussenstap Geohydrologie worden de stijghoogtes bepaald die van belang zijn voor de berekeningen. Hiervoor kan gekozen worden uit drie modellen die in dit scherm worden beschreven. Hier voert de gebruiker ook het rivierwaterpeil en het polderpeil in. 

Voor niveau 1 kiest de gebruiker een constante dempingsfactor die gebruikt wordt voor het gehele vak. 

Voor niveau 2 dient voor elke aquifer de leklengte ingegeven te worden alsmede de breedte van de dijk. Hier wordt de leklengte dan per locatie berekend conform de handreiking. De tool helpt de gebruiker hier om de per gridvlak van het 3D grondmodel de leklengte voor elke aquifer uit te rekenen en hier ook het gemiddelde van te geven. Op basis van de analyse kan de gebruiker zelf kiezen welke waardes te hanteren en deze later ook aanpassen.  

---

Tip: Voor niveau 2 dient voor elk scenario waardes voor de leklengtes te worden ingegeven.

----


![Screenshot](./img/Step_5_8.png?csf=1&web=1&e=sIdfhqg)

In de tab "Leklengte kaart" kunnen die profielen in meer detail worden geinspecteerd. In dit tab kan ook de lengte van het voorland en achterland voor de kaart worden aangepast en kan gekozen worden om de doorlatendheid uit het 3D grondmodel in plaats van die van de materiaaltabel te hanteren.

Ook kan hier gekozen worden om niet het dijkvakgrondprofiel maar het profiel uit het 3D grondmodel te hanteren voor de leklengte berekening. 

---

Let op: Als "Dijkvaklagen gebruiken" wordt uitgezet kan het zijn dat het grondprofiel niet representatief is voor de beschouwde doorsnede.

---

![Screenshot](./img/Step_5_9.png?csf=1&web=1&e=sIdfhqg)

Bij niveau 3 kan een stijghoogtemodel worden geüpload door de gebruiker.

---

Let op: Het is van belang dat dit model geschikt is voor de piping controles en zodoende de maatgevende waterstanden voor deze controles bevat.

---

---

Tip: Het is te adviseren om controles uit te voeren met meerdere geohydrologische modellen als een grove controle op de input en om de gevoeligheid te bepalen.

---

### Tussenstap 3: Genereren uittredepunten
Als de input selectie is afgerond drukt de gebruiker rechtsonder op “Stap 3: Genereren uittredepunt. Het is altijd mogelijk om weer terug te gaan naar de vorige stap. In dit voorbeeld gaan we door met een Niveau 1 methode met een dempingsfactor van 0.8.

![Screenshot](./img/Step_5_10.png?csf=1&web=1&e=sIdfhqg)

De uittredepunten kunnen op drie manieren worden gegenereerd:
1. Als grid in het achterland.
2. Handmatig door een lijn te tekenenen op de kaart.
3. In de afgesneden sloten onder [Tussenstap 1](####tussenstap-1-input-selectie)

Druk daarna op "maak uittredepunt entiteiten". In het voorbeeld hieronder zijn de oranje uittredepunten aangemaakt. In het tab "Algemeen" kan de weergave van de punten en de sloten worden aangepast.

---

Let op: bij het maken van veel uitredepunt entiteiten kan het enige tijd duren om deze aan te maken en zullen de berekeningen ook enige tijd vergen.

---

![Screenshot](./img/Step_5_11.png?csf=1&web=1&e=sIdfhqg)

Aangemaakte uittredepunten kunnen individueel verwijderd worden. Voor het verwijderen van grote hoeveelheden (of alle) uittredepunten kan de gebruiker het beste teruggaan anaar het Viktor dashboard door op het Viktor logo linkboven te drukken en via de browser naar het project en dan naar het dijkvak te gaan. Daar kunnen meerdere uittredepunten worden geselecteerd om te verwijderen. 

![Screenshot](./img/Step_5_12.png?csf=1&web=1&e=sIdfhqg)

### Tussenstap 4: Berekeningen
Nu de uittredepunten zijn gegenereerd kunnen de berekeningen worden uitgevoerd. Klik op "Stap 4: Berekeningen" in de rechteronderhoek om naar de berekeningen te gaan.

In dit scherm kunnen in de rechter tabs de resultaten van de berekeningen voor opbarsten, heave en Sellmeijer (terugschrijdende erosie) worden ingezien. Deze worden weergegeven voor elk uittredepunt.

![Screenshot](./img/Step_5_13.png?csf=1&web=1&e=sIdfhqg)

In het rechter tab "Bodemopbouw inspectie" kan de bodemopbouw van een geselecteerd uittredepunt worden weergegeven. Hier is zowel de opbouw uit het 3D model als de geinterpreteerde opbouw, de dijkvakopbouw en de opbouw gebruikt voor de berekeningen (Dijkvak Sellmeijer) te zien. De gebruiker kan zo controleren of de gebruikte schematisering juist is voor dit uittredepunt.

![Screenshot](./img/Step_5_14.png?csf=1&web=1&e=sIdfhqg)

# Achtergrond input
WORK IN PROGRESS

## Invoeren van lijnen uit QGIS
Deze instructies gelden voor alle lijnen die worden geimporteerd als shapefile (LineString) in QGIS, bijvoorbeeld de kruinlijn of de intredelijn. Dit zou vergelijkbaar moeten werken in andere GIS software.

### Stap 1: Maak een LineString.
Ga naar de tab "Layer" en click op "Create Layer" en selecteerd "New Shapefile Layer". Geef een naam op voor de laag en selecteer "LineString" als het geometry type. Deze laag wordt toegevoegd aan de Table of Contents aan de linkerkant van het scherm. Rechtsklik op deze nieuwe laag en selecteer "Toggle Editing". Selecteer dan het icoon "Add Line Feature" uit de bovenste toolbar en trek de gewenste lijn op de kaart door links te klikken. Rechtsklik om het tekenen af te sluiten.

### Stap 2: Exporteer de laag als shapefile
Rechtslkik op de laag in de linker Table of Contents en selecteer "Export" en vervolgens "Save Features As". Kies voor "ESR Shapefile" als het formaat en sla het bestand op de gewenste locatie onder de juiste naam op. 

### Stap 3: Genereer .zip file
In de folder waar de shapefile is opgeslagen zijn nu zes bestanden te vinden met verschillende extensies (.cpg, .dbf, .prj, .shp, .qmd, .shx). Voeg deze samen in een .zip bestand. Deze zipfile kan dan worden geupload in de tool.
## 3D grondmodel
(nog te maken)

## Afsnijden 3D grondmodel
 Het is mogelijk om een grote dataset af te snijden in het gebied van interesse. Klik hiervoor op de “[Open](https://hdsr.viktor.ai/workspaces/1/app/editor/2)” knop naast de tekst "Models Folder" in het VIKTOR startscherm. Dit opent een nieuw view waar het mogelijk is om een bron   te selecteren en hier een subset van te maken. Deze kan worden opgeslagen op de computer onder de gewenste bestandsnaam om vervolgens te uploaden indien gewenst.

## Sloten uit QGIS
Deze instructies geven aan hoe een slotenbestand kan worden gemaakt voor gebruik in de tool. Elk Hoogheemraadschap gaat op een iets andere manier om met de slotenbestanden wat het lastig maakt dit generiek toe te lichten. Deze instructie is gebaseerd op de data van HDSR.

De sloten data kan worden gedownload als een .gdf database van https://experience.arcgis.com/experience/36136fad9d1049db830b2661dd074bcb/. Echter kan QGIS niet direct met dit bestandsformaat omgaan. Het is mogelijk hier omheen te werken door met de volgende bestanden in de bijlage te werken:
- De hartlijn van de droge sloten (Leggervak_droge_sloot)
- De hartlijn van de natte sloten (LeggervakLine)
- De polygon van de droge sloten (Kernzone_droge_sloot)
- De polygon van de natte sloten (KernzonePolygon)

De bijlage bevat data voor het gehele waterschap. Dit is meer data dan benodigd voor een specifiek project en QGIS kan worden gebruikt om de data af te knippen over het interessegebied.

### Stap 1: Importeer de slootdata in QGIS
Ga naar het tab "Layer" en klik op "Add Layer" en "Add Vector Layer". Selecteer de box "Directory" en selecteerd "OpenFileGDB" als brontype. Kies de folder van de bijlage voor de dataset.

### Stap 2: Teken polygon van interessegebied
Het is nodig een polygon te tekenen om de sloten in het interessegebied te selecteren. Ga hiervoor naar de tab "Layer" en click "Create Layer" en "New Shapefile Layer". Kies een naam voor de polygon en select "Polygon" als geometry type.

De laag wordt nu toegevoegd aan de table of contents aan de linkerkant van het scherm. Rechtsklik op deze nieuwe laag en selecteer "Toggle Editing". Selecteer het icoon "Add Polygon Feature" van de bovenste toolbar en teken de polygon op de kaart met linkermuisklikken. Het is geadviseerd om zo min mogelijk sloten als nodig te gebruiken om te voorkomen dat de tool erg traag wordt. Rechtsklik om het tekenen af te ronden.

### Stap 3: Knip de sloten af op de polygon
Ga naar de tab "Vector" en klik op "Geoprocessing Tools", dan "Clip" en kies één van de vier sloten lagen zoals boven genoemd als "Input Layer" de gecreërde polygon als "Overlay layer". Klik op "Run" en een nieuwe afgeknipte laag wordt toegevoegd aan de table of contents. Hernoem de laag naar wens en herhaal dit proces voor de andere drie slootlagen.

### Stap 4: Exporteer de afgesneden lagen
Rechtsklik op de laag in de linker table of contents en selecteer "Export" en dan "Save Feature As". Kies "ESRI Shapefile" als het formaat en kies de loactie en naam van de nieuwe ShapeFile. De droge sloot lagen moeten minimaal het woord "droge" in hun naam hebben om correct verwerkt te worden in de tool. 

De ShapeFiles van de vier slootlagen moeten in de dezelfde folder worden opgeslagen en samengevoegd in een zip bestand om in de tool te laden.

## Bathymetrie
Deze korte handleiding is voor het invoeren van bathymetrie gegevens specifiek voor het project. Waar bathymetrische data ontbreekt maakt de tool gebruik van AHN data.

### Stap 1: Download bathymetrie data
Bathymetrische data kan worden gedownload via: https://maps.rijkswaterstaat.nl/geoweb55/index.html?viewer=Bathymetrie_Nederland.Webviewer. Klik eerst op een interessegebied en selecteer dan het geotiff formaat.

### Stap 2: Upload bathymetrie data naar QGIS
Ga naar de tab "Layer" en klik op "Data Source Manager" en selecteerd de .tif file als bronbestand. Dit is een raster laag met met grijstinten voor de hoogtes. Deze file is standaard te groot om te uploaden naar de tool en moet versimpeld worden.

### Stap 3: Teken polygon
Het is nodig een polygon te tekenen om het interessegebied. Ga hiervoor naar de tab "Layer" en click "Create Layer" en "New Shapefile Layer". Kies een naam voor de polygon en select "Polygon" als geometry type. 

De laag wordt nu toegevoegd aan de table of contents aan de linkerkant van het scherm. Rechtsklik op deze nieuwe laag en selecteer "Toggle Editing". Selecteer het icoon "Add Polygon Feature" van de bovenste toolbar en teken de polygon op de kaart met linkermuisklikken. Rechtsklik om het tekenen af te ronden.

### Stap 4: Knip de bathymetrie af
Ga naar de tab "Raster" en klik op "Extraction" en dan op "Clip Raster by Mask Layer". Kies de raster bathymetrie laag als "Input Layer" en de polgyon als "Mask Layer" en druk op "Run".

### Stap 5: Exporteer de afgeknipte bathymetrie
Rechtsklik op de laag in de linker table of contents en selecteer "Export" en dan "Save Feature As". Kies "GeoTIFF" als het formaat en kies de loactie en naam van de nieuwe ShapeFile. Het wordt sterk geadviseerd om de resolutie te wijzigen gezien de bathymetrie data standaard een erg hoge resolutie heeft waardoor veel data moet worden geupload. Verander zowel de horizontale als vertical resolutie naar 5m. Een nieuwe raster file is nu beschikbaar om te uploaden naar de tool.

# Technische achtergrond
(nog te maken)