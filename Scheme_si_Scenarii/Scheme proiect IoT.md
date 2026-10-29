# Cum funcționează proiectul

## 1. Rețeaua electrică

![Cum sunt legate tablourile](./Schema%201%20-%20Retea%20electrica.svg)

Transformatorul alimentează patru tablouri și 30 de apartamente. Panourile solare adaugă energie. Fiecare tablou se poate ajuta cu celelalte trei, dacă noul traseu poate prelua consumul.

- **Albastru:** alimentarea de la început.
- **Portocaliu punctat:** legături folosite la nevoie.
- **Senzorii** măsoară. **Întrerupătoarele** schimbă traseul alimentării.

## 2. Datele și comenzile

![De la senzori la pagina web și înapoi](./Schema%202%20-%20Tablou%20Gateway%20Cloud%20Web.svg)

**Spre web:** senzorii măsoară → gateway-ul verifică → cloud-ul salvează → pagina web afișează.

**Spre tablouri:** dai o comandă din web → cloud-ul o trimite → gateway-ul o verifică → tabloul o execută.

După schimbare, senzorii trimit măsurători noi. Așa verificăm dacă acțiunea a avut efect.

**Exemplu:** un senzor arată o temperatură mare. Ceri verificarea din web. Sistemul compară doi senzori din tablouri diferite: unul din T02 și unul din T03. Poate schimba traseul alimentării pentru a urmări cum răspund măsurătorile. Dacă senzorul este suspect, cere verificarea lui și folosește numai datele credibile. Dacă problema este la conexiune, încearcă un alt traseu. Când datele nu sunt suficiente, spune că nu poate stabili cauza.

Senzorii din tablouri diferite pot avea temperaturi diferite în mod normal. Comparăm răspunsul lor la schimbarea alimentării, ținând cont de consum și de locul măsurării. Un senzor din T03 nu înlocuiește direct măsurarea temperaturii unei conexiuni din T02.

Gateway-ul este calculatorul local care leagă tablourile de cloud.

### Dacă o piesă este complet stricată

Sistemul izolează partea defectă și confirmă oprirea. Caută un alt tablou care să alimenteze consumatorii sau împarte sarcina între mai multe tablouri, în funcție de cât pot prelua. Dacă piesa stricată este chiar întrerupătorul, izolarea necesită un alt întrerupător funcțional. Schimbarea alimentării se face numai după confirmarea izolării și verificarea limitelor electrice. În web apare o cerere de înlocuire a piesei.

### Dacă se pierde legătura cu senzorii unui tablou

Gateway-ul observă lipsa mesajelor și marchează măsurătorile vechi. În web se observă întârzieri între datele primite de la senzori. Legătura dintre nodul tabloului și gateway comută pe alt protocol disponibil: MQTT, HTTPS sau WSS. Sistemul verifică dacă sosesc din nou datele. Schimbarea protocolului ajută când serviciul folosit nu funcționează, dar nu repară un senzor oprit, un cablu rupt sau pierderea tuturor căilor de comunicație. Dacă niciun protocol nu merge și nodul local încă funcționează, datele sunt păstrate local. Nu se schimbă alimentarea fără informațiile și confirmările necesare; protecțiile locale continuă independent. La reconectare se verifică starea actuală, iar comenzile expirate nu se execută.

Formularea folosită în schemă: „Dacă se încălzește prea tare un contact electric dintr-un contactor sau piesa acționată mecanic”.

Schemele arată funcționarea propusă. La început, totul este simulat; legătura completă cu web-ul și testarea senzorilor urmează să fie implementate.

Surse editabile: [rețeaua](./Schema%201%20-%20Retea%20electrica.puml) și [datele și comenzile](./Schema%202%20-%20Tablou%20Gateway%20Cloud%20Web.puml).

## 3. Amplasarea aparatelor în tabloul T02

Pornind de la exemplele de desene tehnice și fotografiile tabloului, am pregătit trei amplasări fictive:

- [Placa interioară](./Amplasari_tablou/01_Amplasare_interioara_T02.svg): șine, relee, borne, PM3255, TH110, CL110 și celelalte monitorizări conectate funcțional la nodul IoT.
- [Ușa batantă](./Amplasari_tablou/02_Amplasare_usa_batanta_T02.svg): comenzi, contoare, afișaj IoT, contact de ușă, aparate modulare și detaliul deschiderii.
- [Prizele laterale](./Amplasari_tablou/03_Amplasare_prize_laterale_T02.svg): conectori multipolari, port de date IoT și traseul logic al datelor de la senzori la gateway.

[schema_montare_tablou.pdf](../Documentatie/schema_montare_tablou.pdf), din folderul de documentație, conține toate cele trei planșe A3 la revizia B. [Descrierea amplasărilor](./Amplasari_tablou/README.md) explică senzorii IoT, dimensiunile alese și referințele fotografice. Cotele și reperele sunt fictive; aceste planșe arată amplasarea, fără a defini conexiunile electrice.
