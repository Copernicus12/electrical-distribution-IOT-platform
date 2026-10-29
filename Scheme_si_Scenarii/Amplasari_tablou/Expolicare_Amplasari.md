# Amplasări fictive pentru tabloul T02

Cele trei planșe urmează stilul desenelor tehnice din exemplele fotografiate: vedere frontală, cote, repere și tabele. Organizarea aparatelor este inspirată din fotografiile tabloului real, iar amplasările sunt adaptate pentru un tablou fictiv al proiectului Electrical Distribution IoT.

Deschide [schema_montare_tablou.pdf](../../Documentatie/schema_montare_tablou.pdf), din folderul de documentație. Fișierul conține toate cele trei planșe A3, în format peisaj, la revizia B. SVG-urile sunt editabile, iar imaginile PNG au 4200 × 2970 px și pot fi inserate în documentație sau prezentări.

| Planșă | Sursă editabilă | Imagine |
| --- | --- | --- |
| 01 — Amplasare interioară | [SVG](./01_Amplasare_interioara_T02.svg) | [PNG](./01_Amplasare_interioara_T02.png) |
| 02 — Amplasare pe ușa batantă | [SVG](./02_Amplasare_usa_batanta_T02.svg) | [PNG](./02_Amplasare_usa_batanta_T02.png) |
| 03 — Amplasare prize laterale | [SVG](./03_Amplasare_prize_laterale_T02.svg) | [PNG](./03_Amplasare_prize_laterale_T02.png) |

## Ce reprezintă fiecare planșă

- **Interiorul:** placă fixă cu opt niveluri de relee și borne, canale de cablu, sursă auxiliară, încălzitor, termostat și bară PE. Sunt marcate pozițiile analizorului PM3255, senzorilor TH110 și CL110, contactelor de ușă și retur și monitorizării consumului încălzitorului. N1 este locașul propus pentru nodul local al tabloului; gateway-ul comun al rețelei rămâne separat.
- **Ușa batantă:** fața de operare cu selectoare, contoare de acționări, afișaj IoT, butoane, puncte de test și aparate modulare. Sunt incluse detaliul deschiderii, contactul de ușă B3 și o legendă cu datele senzorilor. HMI1 este un afișaj fictiv pentru datele colectate; analizorul PM3255 este amplasat în interior. Detaliul spatelui ușii a fost eliminat.
- **Laterala stângă:** placă fixă cu 16 conectori mici, 18 conectori multipolari mari, un port de date IoT XI1 și 13 poziții de rezervă. Tabelul dă coordonatele centrelor conectorilor mari și poziția portului XI1. Originea este colțul stânga-sus al plăcii privite din exterior; X crește spre dreapta și Y în jos. Este inclus și fluxul funcțional senzori → N1 → XI1 → gateway. Prizele laterale sunt conectori industriali, nu prize casnice.

## Senzorii și monitorizările IoT din planșe

Reperele urmăresc măsurătorile prevăzute în [descrierea proiectului](../../README.md) și cele șase tipuri de fluxuri din [modelele de senzori](../../iot_platform/sensors/generator.py). Proiectul folosește inițial senzori software; planșele ilustrează o amplasare fictivă pentru echipamentele corespunzătoare.

| Reper | Echipament sau funcție | Măsurători / amplasare |
| --- | --- | --- |
| PM1 | PowerLogic PM3255 | Tensiune, curent, putere, energie, frecvență și factor de putere; interior |
| B1 | TH110 | Temperatura unei conexiuni electrice; interior |
| B2 | CL110 | Temperatura și umiditatea dulapului; interior |
| B3 | Contact de poziție a ușii | Ușă deschisă / închisă; zona cadrului |
| B4 | Contacte de retur de la aparate | Stare, declanșări și confirmări pentru numărarea acționărilor; interior |
| RT1 / IM1 | Termostat și monitorizarea încălzitorului | Temperatură, cerere de încălzire, stare și consum; interior |
| PV1 | Monitorizarea producției fotovoltaice | Putere și energie din grupul T01–T02; sursa este în afara tabloului |
| N1 | Nod local IoT | Colectează datele și le transmite gateway-ului comun |
| XI1 | Port de date IoT propus | Interfață RJ45 pe placa laterală fixă |

B3, B4 și IM1 reprezintă funcții de monitorizare fără un model hardware ales. Legăturile din planșe arată circulația logică a datelor; nu definesc cablarea TH110 sau CL110 la conectorii multipolari.

## Dimensiunile alese pentru exemplu

| Element | Dimensiuni propuse |
| --- | --- |
| Carcasă | 1000 mm lățime × 2000 mm înălțime × 600 mm adâncime |
| Soclu | 200 mm; înălțime totală cu carcasă: 2200 mm |
| Placă interioară | 900 × 1840 mm |
| Cadru batant | 900 × 1900 mm; deschidere ilustrativă de 110° |
| Placă de conectori laterali | 400 × 1230 mm |

Dimensiunile și reperele sunt alese pentru acest exemplu, fără măsurarea tabloului fotografiat. Desenele sunt fără scară. Arată amplasarea mecanică; conexiunile electrice, pinout-ul și găurile de montaj nu sunt documentate. Reperele PM1, B1–B4, RT1, IM1 și N1 sunt comune planșelor. Celelalte repere de aparataj sunt locale, astfel că F1 de pe placa interioară nu definește o legătură cu F1 de pe ușă. Elementele evidențiate cu verde-albăstrui sunt propuneri IoT sau repere explicative.

## Fotografiile folosite ca referință

Cele trei exemple de desen au stabilit stilul și tipurile de vedere:

- `exemplu_schema_amplasare_interioara.HEIC`
- `exemplu_schema_usa_batanta.HEIC`
- `exemplu_amplasare_prize_laterala.HEIC`

Fotografiile `IMG_0489 2.HEIC`, `IMG_0490.HEIC`, `IMG_0491.HEIC`, `IMG_0492 2.HEIC` și `IMG_0493.HEIC` au oferit referințe pentru interior, cablaj, cadrul batant și spatele conectorilor. `IMG_0494 2.HEIC` și `IMG_0495.heic` au oferit referințe pentru fața de operare și placa exterioară de conectori.

Fotografiile originale au fost păstrate în locația furnizată, fără modificări. Planșele folosesc denumirea proiectului propriu și nu reproduc cartușul sau datele beneficiarului din exemple.
