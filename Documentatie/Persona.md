# Persona — operatorul tehnic al rețelei

Aceasta este o persona fictivă, construită pe baza scenariului proiectului. Ne ajută să proiectăm funcțiile și interfața pentru un utilizator concret, fără să pretindem că profilul provine dintr-un interviu real.

## Cine este Mihai

**Mihai Popescu, 38 de ani**, este inginer electrician și responsabil de exploatarea instalațiilor electrice pentru un ansamblu rezidențial. În scenariul nostru, urmărește cele patru tablouri care alimentează cele 30 de apartamente și colaborează cu echipa de mentenanță.

Mihai cunoaște instalația și poate interpreta curenți, tensiuni, temperaturi și stări ale aparatelor. Folosește aplicații de monitorizare și rapoarte tehnice, dar nu lucrează zilnic cu programare sau configurarea protocoalelor. Are nevoie ca aplicația să-i explice starea rețelei fără să-i ceară să urmărească mesaje tehnice în terminal.

Organizația pentru care lucrează este clientul. Mihai este utilizatorul principal al platformei și cel care trebuie să poată lua o decizie pe baza informațiilor afișate.

> „Dacă apare o temperatură mare în T02, vreau să aflu ce trebuie verificat și dacă pot reduce solicitarea până ajunge echipa. După comandă, vreau să văd ce s-a schimbat.”

## Cum lucrează

La începutul programului, Mihai verifică rețeaua de pe laptopul de serviciu: starea tablourilor, alertele rămase și intervențiile din tura anterioară. Când apare o problemă, deschide tabloul respectiv, urmărește măsurătorile și discută cu echipa care poate interveni local.

În cazul unei alerte urgente, timpul său este împărțit între aplicație, apeluri și verificarea instalației. Are nevoie să găsească repede informațiile importante și să poată reveni ulterior la istoricul deciziilor.

## Ce urmărește

- Să observe o problemă înainte să afecteze mai mulți locatari.
- Să păstreze alimentarea consumatorilor în măsura în care instalația permite.
- Să înțeleagă dacă are de investigat un senzor, o conexiune încălzită sau o piesă defectă.
- Să știe ce intervenție a fost executată și dacă a redus solicitarea.
- Să poată transmite echipei de mentenanță tabloul, piesa și observațiile relevante.

## Ce îl încurcă

- O alertă care spune doar „eroare”, fără loc, moment sau explicație.
- Valori care par actuale, deși legătura s-a pierdut de câteva minute.
- Un buton care arată că intervenția a reușit înainte să existe confirmarea execuției.
- Prea multe alerte repetate pentru aceeași situație, fără o imagine clară a evoluției.
- O concluzie sigură despre un senzor defect, bazată pe informații insuficiente.
- Necesitatea de a căuta în fișiere tehnice pentru a afla de ce a fost respinsă o comandă.

## De ce are nevoie în aplicație

Mihai vrea să pornească de la harta rețelei și să ajungă rapid la tabloul cu probleme. În pagina acestuia are nevoie de valorile recente, istoricul lor, alerte, protocolul activ și momentul ultimei actualizări. Reprezentarea 3D îl ajută să localizeze echipamentele, iar măsurătorile și stările confirmate îi susțin decizia.

Pentru o investigație, are nevoie de o acțiune clară, cum ar fi „Verifică senzorul din T02”. După pornire, vrea să știe ce urmărește sistemul și dacă rezultatul indică o problemă probabilă sau cere verificare locală. În cazul schimbării alimentării, trebuie să vadă traseul folosit, verificările efectuate și confirmarea manevrei.

## Un exemplu de utilizare

1. Mihai primește o alertă de temperatură mare în T02. Deschide tabloul și verifică ora măsurării, curentul și evoluția temperaturii.
2. Pornește verificarea senzorului. Sistemul cere măsurători mai dese din T02 și T03 și le urmărește în contextul sarcinii fiecărui tablou.
3. Dacă modelul electric permite, sistemul aplică o schimbare de alimentare sau reduce un consum flexibil. Mihai vede dacă intervenția a fost executată și dacă a scăzut curentul prin contactul investigat.
4. După un interval de observație, urmărește temperatura. Dacă începe să scadă, poate vedea că solicitarea s-a redus, dar păstrează cererea de verificare a piesei. Dacă senzorul rămâne suspect, solicită verificarea locală, fără să considere comparația cu T03 o dovadă suficientă.
5. Consultă rezultatul investigației și istoricul intervenției. Dacă datele nu permit o concluzie, aplicația îi arată acest lucru.

## Cum arată o experiență reușită pentru el

Mihai identifică repede tabloul și natura alertei, știe cât de recente sunt datele și poate urmări o comandă până la confirmare. După intervenție, vede efectul în măsurători și știe dacă situația este stabilă sau dacă trebuie să trimită echipa de mentenanță.

Pentru proiect, această persona înseamnă că punem alertele, vechimea datelor, explicațiile și confirmările comenzilor la îndemână. Funcțiile urmărite sunt detaliate în [cerințele clientului](./Cerinte_client.md), iar implementarea lor este organizată în [planul de acțiune](./Plan_de_actiune.md).
