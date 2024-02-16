# Anleitung zur Verwendung der AutoOpenFoam-classe

Die autoOpenFoam-Klasse dient zur Steuerung und Verwaltung von Simulationen auf Apple-Systemen. Sie nutzt tmux für die Ausführung von Prozessen in einer simulierten Terminalumgebung.
Da ich keinen Plan habe, wird alles indirekt erledigt und die Funktion weiß daher immer nur indirekt, was gerade passiert. Ich konnte das nicht direkt mit Pydocker oder wie das heißt (grade zufauel nachzu schauen) umsetzen, da dann nicht alle benötigten Variablen gesetzt werden und dies meine Kompetenzen übersteigt. 
## Voraussetzungen

- Apple-System: Die Anleitung ist speziell für die Verwendung auf Apple-Computern erstellt. (Ich habe keine Ahnung, wie tmux auf anderen Systemen funktioniert und ob die Befehle dort auch funktionieren.)
- tmux: tmux muss auf Ihrem System installiert sein. tmux ist ein Terminal-Multiplexer, der es ermöglicht, mehrere Terminal-Sitzungen innerhalb eines einzigen Fensters zu erstellen und zu verwalten. Die Installation kann über Homebrew mit dem Befehl brew install tmux erfolgen.

## Einrichtung und Verwendung
### Initialisierung

Um eine Instanz von autoOpenFoam zu erstellen, müssen Sie den rootpfad Ihrer Projekte, den Namen des Projektordners und optional den Pfad zum Docker-Ordner (standart ist '$HOME/HydrothermalFoam_runs' der shared Docker Ortner) sowie den Namen der Anwendung angeben.
Wenn 'HydrothermalSinglePhaseDarcyFoam' nicht verwendet wird, sollte dies bei der application geändert werden. 
Es könnten noch ein paar Kleinigkeiten in der Funktionsbeschreibung enthalten sein, die eingestellt werden können.

```python
from autoOpenFoam.autoOpenFoam import AutoOpenFoam

autoOpenFoam = AutoOpenFoam(root_path='/pfad/zu/projekten', projekt_ortner='meinProjekt')
```
Es muss darauf geachtet werden, dass wenn dies über eine Schleife ausgeführt werden soll, das Projekt so eingerichtet ist, dass auch alles, was eingestellt wird, ausgeführt wird.
Bei mir war das zum Beispiel so, das ich in das clean.sh noch hinzufügen musste:

    rm gmsh/intrusion_mesh.msh

## Parameter setzen

autoOpenFoam unterscheidet zwischen Modell- und Laufzeitparametern:

- Modellparameter beeinflussen die Konfiguration Ihres Modells.
- Laufzeitparameter steuern, wie und wann die Simulation ausgeführt wird.

Um Parameter zu initialisieren, verwenden Sie init_modelParameter oder init_runParameter:

**Wichtig!!! unter init_runParameter sollte aufjeden fall 'startFrom' initialisieren werden,es ist hart im code drine, kann stonst nicht 'latestTime' automatisch einstellen und es kann sein das ein schon vohandenes model von vorne begint !!!!****

bei mir siht das so aus. die drei punkte ... sind dar ums automatisch dort dan den wert einzufügen.

```python
autoOpenFoam.init_runParameter('startFrom', 'system/controlDict.orig', 19, f'startFrom ...;')

autoOpenFoam.init_modelParameter('parameterName', 'pfad/zur/datei', zeilennummer, 'neuerStandardwert')
```
Um Parameterwerte zu setzen: set_Parameter funzt für run und model Parameter.

```python

autoOpenFoam.set_Parameter(parameterName='wert')
```
### Zusätzliche Funktionen

- funktions_abbruchkreterium: Eine Dict von Funktionen, die als Abbruchkriterien dienen. Diese Funktionen werden regelmäßig während der Simulation überprüft. Wenn eine dieser Funktionen True zurückgibt, wird die Simulation abgebrochen.
**mit foo**
```python
from autoOpenFoam.autoOpenFoam import AutoOpenFoam
autoOpenFoam = AutoOpenFoam(root_path='/pfad/zu/projekten', projekt_ortner='meinProjekt')

def meinAbbruchkriterium2(myVar=None) -> bool|str:
    if myVar is None:
        return 'myVar'
    # Logik zur Bestimmung, ob die Simulation abgebrochen werden soll
    # if foo > ...:
        # return True # berechnug wird abgebrochen
    
    return False
autoOpenFoam.myVar = 4 # name ist voher nicht definirt in autoOpenFoam
autoOpenFoam.funktions_abbruchkreterium['myVar'] = meinAbbruchkriterium2
```
**ohne varible** 
```python
def meinAbbruchkriterium1() -> bool:
    # Logik zur Bestimmung, ob die Simulation abgebrochen werden soll
    return False

autoOpenFoam.funktions_abbruchkreterium['name ist egal'] = meinAbbruchkriterium1
```
- funktions_LETZTE_ENFERNEN_UND_NEUSTARTEN: Eine Dict von Funktionen, die aufgerufen werden, bevor ein Neustart der Simulation durchgeführt wird, nachdem der letzte Zeitschritt entfernt wurde.
    das passirt wenn kein weiterer zeitschrit hinzugekommen ist.  


## Simulation starten und verwalten

Um eine Simulation zu starten, verwenden Sie:
wenn es ein modell gibt mit den gegebenen model Parametern wird das weiter gerechnet auser es wird inder funktion notMove auf True gesetzt

```python

autoOpenFoam.run_start()
```
Um eine laufende Simulation abzubrechen:
Diese Funktion löscht den letzten Zeitschritt, da es sein kann, dass er nicht vollständig ist.
```python

autoOpenFoam.run_abbrechen()
```
**Achtung: Es wird ein while-Loop ausgeführt, und erst zurückkehrt, wenn der Run beendet oder abgebrochen wird.**

## probleme mit AutoOpenFoam (Anmerkungen)
- Wenn dein Projekt bereits gestartet ist, wird run.sh erneut ausgeführt und damit alles, einschließlich clean.sh. 

# OpenFoam bedinen mit Tmux
**wird so inder funktion AutoOpenFoam benuzt**
0. starte den docker cotener 
```bash
docker start hydrothermalfoam
```

1. **set folder:**
```python
import os
root_path = '/Users/.../HydrothermalFoam_runs'
target_folder = 'cooling_intrusion_auto'
folder_path = os.path.join(root_path, target_folder)
folder_path_docker = os.path.join('$HOME/HydrothermalFoam_runs', target_folder)
```

2. **start Tmux session:**
 ```python
import subprocess
    
apple_script = '''
tell application "Terminal"
 do script "tmux attach-session -t mysession || tmux new-session -s mysession"
 activate
end tell
'''
subprocess.run(["osascript", "-e", apple_script], check=True)
    
session_name = "mysession"
try:
    # Überprüfen, ob die tmux-Sitzung bereits existiert
    subprocess.run(["tmux", "has-session", "-t", session_name], check=True)
except subprocess.CalledProcessError:
    # Wenn die Sitzung nicht existiert, erstelle eine neue
    subprocess.run(["tmux", "new-session", "-d", "-s", session_name], check=True)
```
3. **Anhängen an die tmux-Sitzung:** 
```python
# Anhängen an die tmux-Sitzung 'mysession'
subprocess.run(["tmux", "attach-session", "-t", "mysession"])

# Senden eines Befehls an die tmux-Sitzung
subprocess.run(["tmux", "send-keys", "-t", "mysession", "docker attach hydrothermalfoam", "C-m"], check=True)
subprocess.run(["tmux", "send-keys", "-t", "mysession", f"cd {folder_path_docker}", "C-m"], check=True)

```
4. **starten** 
   - direkt starten
        ```python
        subprocess.run(["tmux", "send-keys", "-t", "mysession", "HydrothermalSinglePhaseDarcyFoam_Cpr", "C-m"], check=True)
        ```
   - benutze run.sh
        ```python
        subprocess.run(["tmux", "send-keys", "-t", "mysession", "./run.sh", "C-m"], check=True)
        ```
4. **Abbrechen**
   Achtung, der Prozess wird einfach unterbrochen, wenn er später fortgesetzt werden soll, ist manchmal der letzte Zeitschritt nicht vollständig. In AutoOpenFoam habe ich das so gemacht, dass der letzte Zeitschritt gelöscht wird, wenn abgebrochen wird. 
```python
# Sendet das Signal zum Beenden des aktuellen Prozesses in der tmux-Sitzung 'mysession'
subprocess.run(["tmux", "send-keys", "-t", "mysession", "C-c"], check=True)
```
5. **zurücksetzen (clean.sh)**
```python
subprocess.run(["tmux", "send-keys", "-t", "mysession", "./clean.sh", "C-m"], check=True)
```

