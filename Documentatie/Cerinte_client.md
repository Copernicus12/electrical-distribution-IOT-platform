# Cerințele clientului — Electrical Distribution IoT

Pentru acest proiect, considerăm că beneficiarul este organizația care se ocupă de exploatarea instalației electrice a unui ansamblu rezidențial. Operatorul tehnic folosește platforma pentru monitorizare și intervenții, iar echipa de mentenanță rezolvă problemele care cer verificare sau înlocuire locală.

Cerințele de mai jos sunt formulate din perspectiva unui client ipotetic, pe baza scenariului proiectului. Ele reprezintă o propunere de lucru, fără a presupune că am realizat deja un interviu sau o validare cu un client real. Profilul utilizatorului principal este descris în [persona](./Persona.md).

> „Vreau să văd unde apare o problemă, să înțeleg ce se întâmplă și să pot interveni. După intervenție, vreau să știu dacă situația s-a îmbunătățit.”

Bifăm o cerință după ce funcția este integrată și verificată complet. Cele implementate doar parțial rămân nebifate.

## Ce trebuie să pot vedea

- [ ] **O imagine de ansamblu asupra rețelei.** Vreau să văd cele patru tablouri, transformatorul, sursele fotovoltaice și legăturile dintre ele. Trebuie să pot identifica tabloul cu probleme și traseele de alimentare folosite în acel moment.

- [ ] **Măsurători și stări pentru fiecare tablou.** Vreau să urmăresc tensiunea, curentul, puterea, energia, frecvența, factorul de putere și temperaturile relevante. Mă interesează și umiditatea din dulap, starea ușii, stările întrerupătoarelor și contactoarelor, declanșările, acționările confirmate și funcționarea încălzitorului.

- [ ] **Consumul și producția locală.** Vreau să văd cât consumă grupurile de apartamente și cât produc instalațiile fotovoltaice. Valorile trebuie să aibă unități clare, iar energia consumată trebuie deosebită de puterea dintr-un anumit moment.

- [ ] **Cât de recente sunt datele.** Pentru fiecare tablou, vreau să văd când au fost primite ultimele informații și dacă legătura funcționează. Dacă datele sunt vechi, pagina trebuie să mă anunțe. Lipsa comunicației nu trebuie prezentată automat ca lipsă a alimentării apartamentelor.

- [ ] **Istoricul situației.** Vreau să pot consulta evoluția măsurătorilor, alertele și intervențiile pentru tabloul și perioada care mă interesează. Trebuie să pot compara ce se întâmpla înaintea unei comenzi cu ce s-a întâmplat după executarea ei.

## Cum vreau să aflu și să investighez o problemă

- [ ] **Alerte pe care le pot înțelege.** La suprasarcină, temperatură prea mare, date suspecte sau lipsa mesajelor, vreau o alertă care arată tabloul, echipamentul sau senzorul, momentul și motivul. Trebuie să înțeleg dacă este nevoie de o intervenție imediată sau de o verificare.

- [ ] **Posibilitatea de a cere verificarea unui senzor.** Dacă temperatura din T02 pare neobișnuită, vreau să pot porni din web o investigație. Sistemul poate cere măsurători mai dese din T02 și T03 și poate urmări cum răspund valorile la schimbarea sarcinii. Vreau să văd pașii efectuați și concluzia susținută de măsurători.

- [ ] **O diferențiere cinstită între senzor suspect și problemă reală.** Nu vreau ca o singură valoare greșită să declanșeze singură schimbări automate. În același timp, o temperatură critică reală trebuie păstrată și semnalată. Dacă sistemul nu poate stabili cauza, trebuie să spună asta și să indice nevoia unei verificări locale. Un senzor din alt tablou oferă context, dar nu confirmă singur defectarea senzorului investigat.

- [ ] **Recuperarea sau înlocuirea unui senzor defect.** Vreau să pot cere o verificare nouă și repornirea senzorului, dacă acesta permite. Până la clarificare, sistemul folosește numai datele credibile pentru deciziile automate. Dacă senzorul nu își revine și defectul este confirmat, vreau să apară o solicitare de înlocuire.

## Ce intervenții trebuie să permită platforma

- [ ] **Reducerea solicitării unei piese care se încălzește.** Dacă se încălzește prea tare un contact electric dintr-un contactor sau o piesă acționată mecanic, vreau ca sistemul să verifice un alt traseu de alimentare. După schimbare, urmărește reducerea curentului prin piesa afectată și dacă temperatura începe să scadă, lăsând timp pentru răcire. La nevoie, reduce consumul flexibil. Vreau să văd efectul în web și să rămână semnalată nevoia de verificare a piesei.

- [ ] **Sprijin între tablouri la suprasarcină.** Dacă un tablou rămâne prea încărcat, vreau ca sistemul să verifice dacă poate primi sprijin de la celelalte trei. Sprijinul poate veni de la unul sau mai multe tablouri, în funcție de ce permite calculul electric. Înainte de aplicare, trebuie verificate tensiunile și limitele liniilor și ale transformatorului comun.

- [ ] **Reducerea consumului care poate fi amânat.** Dacă sprijinul nu ajunge, sistemul poate reduce temporar consumurile declarate flexibile în simulator. Consumul esențial are prioritate, iar cantitatea de energie neservită trebuie înregistrată. Dacă problema rămâne nerezolvată, vreau o alertă clară.

- [ ] **Comenzi manuale cu rezultat vizibil.** Vreau să pot cere o măsurătoare nouă, o investigație sau o schimbare de alimentare permisă de model. Intervenția manuală are prioritate temporară față de automatizare, fără să poată ocoli verificările electrice. Dacă o comandă este respinsă, vreau să aflu motivul. Repornirea unui senzor poate fi oferită numai dacă dispozitivul sau modelul simulat o permite.

- [ ] **Confirmarea comenzilor.** Vreau să văd separat că o comandă a fost trimisă, acceptată și executată ori că a fost respinsă sau a expirat. Fiecare comandă trebuie să poată fi urmărită în istoric, împreună cu utilizatorul care a cerut-o și efectul observat. O comandă expirată nu trebuie executată când revine legătura.

- [ ] **Tratarea unei piese defecte.** Dacă o piesă nu mai funcționează, vreau ca partea afectată să fie izolată și izolarea să fie confirmată înainte de căutarea unei alte alimentări. Noul traseu nu trebuie să alimenteze din nou partea defectă. Dacă izolarea sau alimentarea alternativă nu sunt posibile, situația trebuie raportată. În pagină vreau să văd și ce piesă necesită verificare sau înlocuire.

- [ ] **Revenirea controlată la configurația inițială.** După dispariția suprasarcinii, sistemul poate reveni automat dacă regimul inițial este fezabil și stabil. Pentru o piesă defectă, revenirea presupune reparație și verificare. Vreau să văd când și de ce s-a făcut schimbarea.

## Ce se întâmplă când apar probleme de comunicație

- [ ] **Trecerea la alt protocol disponibil.** Dacă serviciul folosit nu mai funcționează, sistemul trebuie să poată încerca MQTT, HTTPS sau WSS și să verifice reluarea schimbului de date. Vreau să văd întârzierile dintre datele primite de la senzori, protocolul activ, motivul și momentul ultimei schimbări. Alegerea trebuie să evite trecerile repetate între protocoale la fluctuații mici.

- [ ] **Continuarea locală și recuperarea datelor.** Dacă legătura cu cloud-ul cade, verificările locale trebuie să poată continua cât timp nodurile și gateway-ul funcționează. Datele neconfirmate se păstrează în limita spațiului configurat și se retransmit la reconectare, cu eliminarea duplicatelor. Dacă lipsesc datele sau confirmările necesare unei manevre, sistemul nu trebuie să o execute. Schimbarea protocolului ajută numai dacă există o alternativă accesibilă.

## Cum trebuie să fie utilizarea aplicației

- [ ] **Accesul să fie controlat.** Utilizatorii intră cu un cont, iar comenzile sunt disponibile numai celor autorizați. Înregistrarea unui cont obișnuit nu trebuie să ofere drepturi administrative.
- [ ] **Informațiile să fie ușor de urmărit.** Starea normală, alerta, lipsa datelor și o comandă în așteptare trebuie să poată fi deosebite prin text și indicatoare vizuale. Mesajele trebuie să ajute operatorul să aleagă următorul pas.
- [ ] **Datele și deciziile să poată fi verificate.** Păstrăm măsurătorile brute, marcajele de calitate și explicația eventualelor corecții. Valorile critice reale nu sunt modificate doar pentru a apărea în intervalul normal.
- [ ] **Actualizarea să aibă un comportament previzibil.** Intervalele de măsurare, pragurile de alertare, vechimea maximă a datelor și timpii de confirmare trebuie definiți și verificați. Valorile finale se stabilesc în etapa de calibrare și se consemnează înaintea testelor de acceptare.
- [ ] **Demonstrația să poată fi repetată.** Aceleași profiluri și aceleași defecte trebuie să poată fi rulate din nou. Timpul de detecție, timpul de reconectare și efectul intervențiilor trebuie măsurate.

## Cum verificăm că prima versiune răspunde cerințelor

Prima versiune urmărește [cele două scheme ale proiectului](../Scheme_si_Scenarii/Scheme%20proiect%20IoT.md). Rețeaua de 20 kV alimentează transformatorul comun, T01 și T03 au câte 8 apartamente, iar T02 și T04 câte 7. Avem două grupuri fotovoltaice și legături de sprijin între tablouri. Măsurătorile merg de la senzori prin gateway la cloud și baza de date, apoi în web; cererile și comenzile urmează sensul invers. Nu presupunem baterii sau echipamente fizice. Pentru acceptarea prototipului, demonstrăm următoarele situații:

- [ ] **Funcționare normală.** Măsurătorile tuturor tablourilor, consumul, producția și momentul actualizării.
- [ ] **Temperatură mare în T02.** Alerta, cererea de investigație, schimbarea curentului și evoluția temperaturii; concluzie limitată la dovezile disponibile.
- [ ] **Senzor cu valori blocate sau eronate.** Marcarea datelor suspecte, folosirea datelor credibile, repornirea dacă este posibilă și solicitarea înlocuirii dacă defectul este confirmat și persistă.
- [ ] **Suprasarcină cu sprijin disponibil sau insuficient.** Verificarea electrică, sprijinul aplicat, reducerea consumului flexibil dacă este necesară și rezultatul măsurat.
- [ ] **Piesă defectă.** Confirmarea izolării, alimentarea alternativă doar dacă este fezabilă și solicitarea de mentenanță.
- [ ] **Căderea protocolului activ, apoi a tuturor căilor.** Alegerea alternativei când există, marcarea datelor vechi, păstrarea locală și recuperarea fără înregistrări duplicate.
- [ ] **Comandă manuală, inclusiv una respinsă sau expirată.** Starea comenzii, motivul respingerii când este cazul și măsurătorile care confirmă efectul celei executate.

Acestea sunt cerințele versiunii urmărite. Stadiul implementării și ordinea lucrărilor se găsesc în [planul de acțiune](./Plan_de_actiune.md).
