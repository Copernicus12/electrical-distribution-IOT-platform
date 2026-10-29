# Plan de acțiune — Electrical Distribution IoT

Urmărim [cele două scheme ale proiectului](../Scheme_si_Scenarii/Scheme%20proiect%20IoT.md): rețeaua de 20 kV alimentează un transformator comun, patru tablouri și 30 de apartamente. T01 și T03 au câte 8 apartamente, iar T02 și T04 câte 7. Cele două grupuri fotovoltaice contribuie la alimentare, iar tablourile se pot sprijini reciproc, în limitele electrice. Totul este inițial simulat; bateriile și echipamentele fizice rămân pentru o etapă ulterioară.

Datele merg de la senzori la gateway pentru verificare, apoi în cloud pentru salvare și în web pentru afișare. Cererile operatorului se întorc pe traseul web → cloud → gateway → tablou, iar măsurătorile noi arată rezultatul.

Bifăm livrările existente pe baza commit-urilor și a fișierelor din proiect. Pentru ce urmează, estimăm câte un obiectiv pe săptămână, începând de luni, 2 noiembrie 2026, cu o pauză de sărbători înaintea checkpointului final din 11–17 ianuarie 2027. Datele sunt orientative; la sfârșitul fiecărei etape verificăm rezultatul și ajustăm pașii rămași. O componentă implementată mai are nevoie de integrare și validare.

## Ce am realizat deja

- [x] **11–12 octombrie — Ideea și propunerea proiectului.** Am descris problema și direcția inițială. Commit-uri: `267e1df`, `7b743b5`.
- [x] **18 octombrie — Senzori și gateway TCP.** Am adăugat procesele de senzori, colectarea datelor și teste pentru componente. Commit: `46c70df`.
- [x] **18–19 octombrie — Baza interfeței web.** Avem Laravel cu Vue, autentificare, tablouri 3D și harta rețelei. Commit-uri: `22344db`, `71bd0b6`, `b5a9e6a`, `423375f`.
- [x] **26 octombrie — Prima implementare a simulatorului și comunicației adaptive.** Există modelul electric, senzori suplimentari, adaptoare MQTT/HTTPS/WSS și logica inițială de sprijin. Commit: `28c189b`.
- [x] **28 octombrie — Scenariul și schemele actuale.** Am explicat investigarea senzorilor, piesele defecte și pierderea comunicației. Commit: `4b54c94`.
- [x] **29 octombrie — Documentele de lucru.** Am pregătit [cerințele clientului](./Cerinte_client.md), [persona](./Persona.md) și acest plan. Aceste fișiere sunt deocamdată locale, fără commit.

## Ce urmează, săptămână cu săptămână

- [ ] **2–8 noiembrie — Verificăm simulatorul și senzorii.** Urmărim consumul, producția și limitele electrice într-o zi simulată de 24 de ore, cu pas de o secundă. Confirmăm că senzorii urmăresc aceeași stare a rețelei și că schimbarea sarcinii se reflectă în măsurători.

- [ ] **9–15 noiembrie — Aducem datele în web.** Legăm gateway-ul de serviciul central, PostgreSQL și dashboard. Începem cu T02, apoi extindem la toate tablourile; afișăm valorile, momentul măsurării și datele învechite.

- [ ] **16–22 noiembrie — Completăm comenzile și istoricul.** Implementăm traseul web → cloud → gateway → tablou și confirmarea execuției prin măsurători noi. Adăugăm alerte, grafice, permisiuni și stările comenzilor, inclusiv respingerea și expirarea.

- [ ] **23–29 noiembrie — Investigăm anomaliile.** Pornim testul din web și comparăm răspunsul senzorilor din T02 și T03 la schimbarea sarcinii, ținând cont de condițiile fiecărui tablou. Afișăm ce s-a schimbat după test. Pentru un senzor suspect folosim datele credibile, încercăm repornirea dacă este posibilă și cerem înlocuirea dacă defectul persistă. Când datele nu ajung pentru o concluzie, cerem verificare locală.

- [ ] **30 noiembrie–6 decembrie — Verificăm reconectarea adaptivă.** Afișăm în web întârzierile dintre măsurători. La pierderea legăturii, trecem la alt protocol disponibil dintre MQTT, HTTPS și WSS și confirmăm că sosesc din nou date. Dacă toate căile cad, păstrăm datele local cât timp nodurile funcționează și le recuperăm fără duplicate. Completăm și legătura gateway–cloud și schimbul de stări între tablouri.

- [ ] **7–13 decembrie — Completăm intervențiile asupra rețelei.** Pentru un contact dintr-un contactor sau o piesă acționată mecanic care se încălzește, schimbăm traseul dacă este posibil și urmărim scăderea curentului, apoi a temperaturii; reducem consumul flexibil la nevoie. Pentru o piesă complet defectă, confirmăm izolarea și căutăm alimentare prin unul sau mai multe tablouri, împărțind sarcina după capacitatea disponibilă. Verificăm prioritatea temporară a comenzilor manuale și revenirea la normal după verificările necesare.

- [ ] **14–20 decembrie — Testăm întregul flux.** Rulăm scenariile de funcționare normală, suprasarcină, încălzire, senzor suspect, piesă defectă și întrerupere a comunicației. Verificăm că stările din pagină corespund celor confirmate în simulator și corectăm problemele găsite.

- [ ] **11–17 ianuarie 2027 — Comparăm rezultatele și pregătim prezentarea.** Pe aceleași profiluri și defecte, comparăm detecția la edge cu cea în cloud, protocolul fix cu selecția adaptivă și reducerea consumului cu sprijinul urmat de reducere. Măsurăm întârzierile, traficul, livrarea și energia neservită; finalizăm graficele, instrucțiunile și demonstrația.

Actualizăm documentația pe parcurs, după fiecare etapă. Pentru detaliile scenariilor folosim [scenariul proiectului](../Scheme_si_Scenarii/Scenariu.txt) și [schemele explicate](../Scheme_si_Scenarii/Scheme%20proiect%20IoT.md). Rezultatele finale vor descrie comportamentul prototipului simulat în condițiile testate.
