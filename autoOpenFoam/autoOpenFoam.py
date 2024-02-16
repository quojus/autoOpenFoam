import glob
import subprocess
import os
import shutil
import time
from typing import List, Dict, Optional
from enum import Enum, auto
import sys


class Parameter():
    def __init__(self, name: str, root_path, projekt_ortner, path_ab_projekt, line_number,
                 new_content_defold: str = None):
        """
        Initialisiert eine Parameter mit gegebenen Parametern und überprüft, ob der angegebene Pfad existiert.
        Wenn Sie Parameter in den Text einfügen wollen, geben Sie die Variable mit ... an.

        :param name: Der Name der Parameter.
        :param root_path: Der Wurzelpfad, von dem aus die Projektordner zu finden sind.
        :param projekt_ortner: Der Name des Projektordners.
        :param path_ab_projekt: Der relative Pfad vom Projektordner zur Datei, die die Parameter enthält.
        :param line_number: Die Zeilennummer in der Datei, in der die Parameter definiert ist.
        :param new_content_defold: Der neue Standardinhalt der Parameter, der '...' enthält, um den zu ersetzenden Teil zu markieren.
        """
        self.name: str = name
        self.root_path = root_path
        self.projekt_ortner = projekt_ortner
        self.path_ab_projekt = path_ab_projekt

        path = os.path.join(self.root_path, projekt_ortner, self.path_ab_projekt)
        if not os.path.exists(path):
            raise ValueError(f"path exestirt nicht {path}")
        self.line_number = line_number
        self.new_content_defold = new_content_defold
        print(
            f'zeile {self.line_number} im dokument: "{self.get_Line(all=True)}" | deine eingabe: "{self.new_content_defold}"')

    def set_Line(self, wert=None, new_content: str = None, projekt_ortner: str = None):
        if wert is not None and '...' in self.new_content_defold and new_content is None:
            new_content = self.new_content_defold.replace('...', str(wert))
        if projekt_ortner is None:
            projekt_ortner = self.projekt_ortner
        path = os.path.join(self.root_path, projekt_ortner, self.path_ab_projekt)
        if not os.path.exists(path):
            raise ValueError(f"path exestirt nicht {path}")
        if new_content is None:
            new_content = self.new_content_defold
        self.__update_Line(path, self.line_number, new_content)

    def get_Line(self, projekt_ortner=None, all: bool = False) -> str:
        if projekt_ortner is None:
            projekt_ortner = self.projekt_ortner
        path = os.path.join(self.root_path, projekt_ortner, self.path_ab_projekt)
        if not os.path.exists(path):
            raise ValueError(f"path exestirt nicht {path}")
        line = self.__get_line(path, self.line_number).replace('\n', '')
        if '...' in self.new_content_defold and all == False:
            mussWeg = self.new_content_defold.split('...')
            for w in mussWeg:
                line = line.replace(w, '')
        return line

    def __get_line(self, file_path, line_number):
        """Aktualisiert eine spezifische Zeile in einer Datei."""
        with open(file_path, 'r') as file:
            lines = file.readlines()
        return lines[line_number - 1]

    def __getitem__(self):
        return self.name, self.get_Line()

    def __update_Line(self, file_path, line_number, new_content):
        """Aktualisiert eine spezifische Zeile in einer Datei."""
        with open(file_path, 'r') as file:
            lines = file.readlines()
        # print('alte zeihle:', lines[line_number - 1].replace('\n',''))
        # print('neue zeile:', new_content)
        lines[line_number - 1] = new_content + '\n'  # Zeilennummern beginnen bei 1
        with open(file_path, 'w') as file:
            file.writelines(lines)


class FehlerKeinNeuerZeitschrit(Enum):
    WARTEN = auto()
    AUTO_LETZTE_ENFERNEN_UND_NEUSTARTEN = auto()
    INPUT_LETZTE_ENFERNEN_UND_NEUSTARTEN = auto()
    INPUT_NEUSTARTEN = auto()
    RUN_BEENDEN = auto()
    PROGRAM_BEENDEN = auto()


class Zeiteinheit(Enum):
    JAHRE = "Jahre"
    TAGE = "Tage"
    STUNDEN = "Stunden"
    MINUTEN = "Minuten"
    SEKUNDEN = "Sekunden"
    MILLISEKUNDEN = "Millisekunden"


def zeit_in_sekunden(zahl, einheit: Zeiteinheit):
    if einheit == Zeiteinheit.JAHRE:
        return zahl * 365 * 24 * 60 * 60  # Vereinfachte Annahme: 365 Tage pro Jahr
    elif einheit == Zeiteinheit.TAGE:
        return zahl * 24 * 60 * 60
    elif einheit == Zeiteinheit.STUNDEN:
        return zahl * 60 * 60
    elif einheit == Zeiteinheit.MINUTEN:
        return zahl * 60
    elif einheit == Zeiteinheit.SEKUNDEN:
        return zahl
    elif einheit == Zeiteinheit.MILLISEKUNDEN:
        return zahl / 1000
    else:
        return 0


def sekunden_in_einheit(sekunden, einheit: Zeiteinheit):
    if einheit == Zeiteinheit.JAHRE:
        return sekunden / (365 * 24 * 60 * 60)  # Vereinfachte Annahme: 365 Tage pro Jahr
    elif einheit == Zeiteinheit.TAGE:
        return sekunden / (24 * 60 * 60)
    elif einheit == Zeiteinheit.STUNDEN:
        return sekunden / (60 * 60)
    elif einheit == Zeiteinheit.MINUTEN:
        return sekunden / 60
    elif einheit == Zeiteinheit.SEKUNDEN:
        return sekunden
    elif einheit == Zeiteinheit.MILLISEKUNDEN:
        return sekunden * 1000
    else:
        return None


class AutoOpenFoam():
    def __init__(self, root_path: str, projekt_ortner: str, sharedOrtnerDocker: str = '$HOME/HydrothermalFoam_runs',
                 application: str = 'HydrothermalSinglePhaseDarcyFoam', **kwargs):
        """
        Initialisiert eine Instanz des AutoOpenFoam, um Simulationen zu steuern und zu verwalten.

        :param root_path: Der Basispfad, in dem die Projekte gespeichert sind.
        :param projekt_ortner: Der Name des Projektordners, in dem die Simulation durchgeführt wird.
        :param sharedOrtnerDocker: Der Pfad zum gemeinsamen Docker-Ordner. Standardmäßig '$HOME/HydrothermalFoam_runs'.
        :param application: Der Name der Anwendung, die für die Simulation verwendet wird. Standardmäßig 'HydrothermalSinglePhaseDarcyFoam'.
        :param kwargs: Zusätzliche optionale Parameter, darunter:
                       - 'tmuxSessionName': Der Name der tmux-Session. (str)
                       - 'shell': Ein Boolean-Wert, der angibt, ob eine Shell-Sitzung verwendet werden soll (bool).
                       - 'updateTimeSec': Die Aktualisierungsintervallzeit in Sekunden (float).
                       - 'Zeiteinheit' : "Jahre","Tage","Stunden","Minuten","Sekunden" und "Millisekunden"
                       - 'toleranzBeiSuche' : bei such ob das projekt schon berechnet is, toleranz (float) 1 = 100% (glaube ich)
        """
        self.toleranzBeiSuche: float = 0.0  # 1 = 100%
        self.root_path = root_path
        self.tmuxSessionName = kwargs.get('tmuxSessionName', 'mysession')
        self.updateTimeSec = float(kwargs.get('updateTimeSec', 30.0))
        self.zeiteinheit: Zeiteinheit = Zeiteinheit(kwargs.get('zeiteinheit', Zeiteinheit.JAHRE))
        self.toleranzBeiSuche: float = float(kwargs.get('toleranzBeiSuche', 0))
        shell = kwargs.get('shell', True)
        self.application: str = application  # 'HydrothermalSinglePhaseDarcyFoam'
        self.wasMachenBeiFehler: FehlerKeinNeuerZeitschrit = FehlerKeinNeuerZeitschrit.INPUT_LETZTE_ENFERNEN_UND_NEUSTARTEN

        self._modelParameter: Dict[str, Optional[Parameter]] = {}
        self._runParameter: Dict[str, Optional[Parameter]] = {}
        self._runParameter_wertSpeicher: dict = {}
        self.__behalteZeitSchritt: int = 0
        self.__sessionAktiviert: bool = False
        self._home_projekt_ortner: str = projekt_ortner
        self.sharedOrtnerDocker: str = sharedOrtnerDocker
        self.sucheAnderProjekteDieSchonMalMitDennParameterenBerechnetWurden: bool = True
        self.set_projekt_ortner(projekt_ortner)
        self._starte_tmuxSession(shell=shell)
        # funktion dicts
        self.funktions_abbruchkreterium: dict = {}
        self.funktions_LETZTE_ENFERNEN_UND_NEUSTARTEN: dict = {}
        self.funktions_beiAbbruch: dict = {}

    def set_behalteZeitSchritt(self, value: int, zeiteinheit: Zeiteinheit = None):
        """
        Legt fest, wie viele Zeitschritte behalten werden sollen, 0 und die Zwei gösten werden nicht gelöscht.

        :param value: Zeitintervall, z. B. 500 (alle Zeitintervalle, die durch 500 teilbar sind, bleiben erhalten) Die Anzahl der Zeitschritte, die behalten werden sollen. 
        :param zeiteinheit: Die Einheit der Zeit, in der 'value' angegeben wird. Wenn None, wird die aktuell gesetzte Zeiteinheit der classe verwendet.
        """
        if zeiteinheit is None:
            zeiteinheit = self.zeiteinheit
        self.__behalteZeitSchritt = zeit_in_sekunden(value, zeiteinheit)

    def init_modelParameter(self, name, path_ab_projekt, line_number, new_content_defold: str = None):
        """
        Initialisiert und speichert einen Modellparameter. Modellparameter gedacht für permeability oder änliches

        :param name: Der Name des Parameters.
        :param path_ab_projekt: Der relative Pfad zur Datei, in der der Parameter geändert wird, in Bezug auf das Projekt.
        :param line_number: Die Zeilennummer in der Datei, an der der Parameter steht.
        :param new_content_defold: Der neue Wert des Parameters als String. Kann '...' enthalten, um den Teil des Strings anzugeben, der ersetzt werden soll mit der funktion set_Parameter.
        """
        if name in self._runParameter:
            raise f'der name {name} darf nicht in runParameter definiert sein'
        self._modelParameter[name] = Parameter(name, self.root_path, self.projekt_ortner, path_ab_projekt, line_number,
                                               new_content_defold)

    def init_runParameter(self, name, path_ab_projekt, line_number, new_content_defold: str = None):
        """
        Initialisiert und speichert einen runParameter. runParameter gedacht für startFrom endTime_year writeInterval_year oder änliches.
        empfele startFrom auch so zu implimentiren ist Hart gecodet  :)

        :param name: Der Name des Parameters.
        :param path_ab_projekt: Der relative Pfad zur Datei, in der der Parameter geändert wird, in Bezug auf das Projekt.
        :param line_number: Die Zeilennummer in der Datei, an der der Parameter steht.
        :param new_content_defold: Der neue Wert des Parameters als String. Kann '...' enthalten, um den Teil des Strings anzugeben, der ersetzt werden soll mit der funktion set_Parameter.
        """
        if name in self._modelParameter:
            raise f'der name {name} darf nicht in modelParameter definiert sein'
        self._runParameter[name] = Parameter(name, self.root_path, self.projekt_ortner, path_ab_projekt, line_number,
                                             new_content_defold)

    def set_Parameter(self, **kwargs):
        """
        Setzt die Werte für angegebene Parameter.
        ist der Parameter in run/model Parameter definirt wird das dan im projekt ortner geändert.
        :param kwargs: Ein Dictionary von Parameternamen und ihren neuen Werten.
        """
        for k, v in kwargs.items():
            if k in self._modelParameter.keys():
                self._modelParameter[k].set_Line(v)
        for k, v in kwargs.items():
            if k in self._runParameter.keys():
                self._runParameter_wertSpeicher[k] = v
                self._runParameter[k].set_Line(v)

    def get_Parameter(self, nameList: list, projekt_ortner: str = None, **kwargs: object) -> dict:
        """
        Gibt die aktuellen Werte für eine Liste von Parametern zurück.

        :param nameList: Eine Liste von Parameternamen, deren Werte abgefragt werden sollen.
        :param projekt_ortner: Optionaler Parameter, um den Projektordner anzugeben, falls von dem Standard abgewichen werden soll.
        :return: Ein Dictionary mit den Parameternamen als Schlüssel und ihren aktuellen Werten als Werte.
        """
        werteDict: dict = {}
        for k in nameList:
            if k in self._modelParameter.keys():
                werteDict[k] = self._modelParameter[k].get_Line(projekt_ortner)
        for k in nameList:
            if k in self._runParameter.keys():
                werteDict[k] = self._runParameter[k].get_Line(projekt_ortner)
        return werteDict

    def get_modelParameter(self, nameList: list = None, projekt_ortner: str = None, **kwargs: object) -> dict:
        """
        Gibt die aktuellen Werte für eine Liste von Modellparametern zurück. Wenn nichts angegeben ist, werden alle Werte zurückgegeben.

        :param nameList: Eine Liste von Parameternamen, deren Werte abgefragt werden sollen.
        :param projekt_ortner: Optionaler Parameter, um den Projektordner anzugeben, falls von dem Standard abgewichen werden soll.
        :return: Ein Dictionary mit den Parameternamen als Schlüssel und ihren aktuellen Werten als Werte.
        """
        werteDict: dict = {}
        if nameList == None:
            nameList = self._modelParameter.keys()
        for k in nameList:
            if k in self._modelParameter.keys():
                werteDict[k] = self._modelParameter[k].get_Line(projekt_ortner)
        return werteDict

    def get_runParameter(self, nameList: list = None, projekt_ortner: str = None) -> dict:
        """
        Gibt die aktuellen Werte für eine Liste von run Parametern zurück. Wenn nichts angegeben ist, werden alle Werte zurückgegeben.

        :param nameList: Eine Liste von Parameternamen, deren Werte abgefragt werden sollen.
        :param projekt_ortner: Optionaler Parameter, um den Projektordner anzugeben, falls von dem Standard abgewichen werden soll.
        :return: Ein Dictionary mit den Parameternamen als Schlüssel und ihren aktuellen Werten als Werte.
        """
        werteDict: dict = {}
        if nameList == None:
            nameList = self._runParameter.keys()
        for k in nameList:
            if k in self._runParameter.keys():
                werteDict[k] = self._runParameter[k].get_Line(projekt_ortner)
        return werteDict

    def _starte_tmuxSession(self, shell: bool = True, dockerContenerName: str = 'hydrothermalfoam'):
        if self.__sessionAktiviert:
            return
        if shell:
            apple_script = f'''
            tell application "Terminal"
                do script "tmux attach-session -t {self.tmuxSessionName} || tmux new-session -s {self.tmuxSessionName}"
                activate
            end tell
            '''
            subprocess.run(["osascript", "-e", apple_script], check=True)
        else:
            try:
                # Überprüfen, ob die tmux-Sitzung bereits existiert
                subprocess.run(["tmux", "has-session", "-t", self.tmuxSessionName], check=True)
            except subprocess.CalledProcessError:
                # Wenn die Sitzung nicht existiert, erstelle eine neue
                subprocess.run(["tmux", "new-session", "-d", "-s", self.tmuxSessionName], check=True)

        subprocess.run(["tmux", "attach-session", "-t", self.tmuxSessionName])
        time.sleep(0.2)
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, f"docker attach {dockerContenerName}", "C-m"],
                       check=True)
        time.sleep(1)
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, f"cd", "C-m"], check=True)
        time.sleep(0.1)
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, f"cd {self.projekt_path_docker}", "C-m"],
                       check=True)
        time.sleep(0.1)
        self.__sessionAktiviert = True

    def set_projekt_ortner(self, projekt_ortner):
        if '/' in projekt_ortner:
            raise f"dies ist kein gültiges Projekt, nur der ortner name!!!  root_path für zu dem ortner"
        self.projekt_ortner = projekt_ortner
        self.projekt_path = os.path.join(self.root_path, projekt_ortner)
        if not os.path.exists(self.projekt_path):
            raise ValueError(f"path exestirt nicht {self.projekt_path}")
        for var in self._modelParameter.keys():  # update projekt_ortner des variablen_dict
            self._modelParameter[var].projekt_ortner = self.projekt_ortner
        for var in self._runParameter.keys():  # update projekt_ortner des variablen_dict
            self._runParameter[var].projekt_ortner = self.projekt_ortner
        self.projekt_path_docker = os.path.join(self.sharedOrtnerDocker, self.projekt_ortner)
        self._ceck_script('run.sh', zeile='touch ./run_finished')
        self._ceck_script('clean.sh', zeile='rm run_finished')
        if self.__sessionAktiviert:
            subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, f"cd {self.projekt_path_docker}", "C-m"],
                           check=True)
            time.sleep(0.1)
            # subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "C-c"], check=True)
            # time.sleep(0.1)

    def print_all(self):
        for a in self.__dict__.keys():
            print(f"{a}: {self.__dict__[a]}")

    def _ceck_script(self, name, zeile):
        dateipfad = os.path.join(self.projekt_path, name)
        try:
            with open(dateipfad, 'r+') as datei:
                zeilen = datei.readlines()
                zeile_vorhanden = False
                for zeilen_text in zeilen:
                    if zeile in zeilen_text:
                        zeile_vorhanden = True
                        break
                if not zeile_vorhanden:
                    datei.write('\n' + zeile)
                    print(f"In {name} wurde {zeile} hinzugefügt,\ndamit die Klasse erkennt, dass der Lauf beendet ist.")
        except FileNotFoundError:
            print(f"Diese Klasse braucht ein {name} Skript in projekt.")
            quit()

    def get_BerechneteZeitSchritte(self, directory: str = None):
        if directory is None:
            directory = self.projekt_path
        numeric_folders = []  # Liste, um die Pfade der gefundenen Ordner zu speichern
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                if dir_name.isdigit():  # Prüft, ob der Ordnername nur aus Zahlen besteht
                    numeric_folders.append(int(dir_name))
        numeric_folders = sorted(numeric_folders, reverse=True)
        return numeric_folders

    def zeitSchritte_Endfernen(self, zeitSchritte: int = None):
        """
        Entfernt Zeitschritte aus der Simulation, um Speicherplatz zu sparen. Wenn kein spezifischer Wert für 'zeitSchritte' angegeben wird, verwendet die Funktion den intern gespeicherten Standardwert.
        wird automatische beim run ausgeführt.

        :param zeitSchritte: Die Anzahl der Zeitschritte, die behalten werden sollen, bevor ältere entfernt werden. Wenn -1, wird nur der letzte Zeitschritt entfernt.
        """
        if zeitSchritte == -1:
            berechneteZeitSchritte = self.get_BerechneteZeitSchritte()
            if berechneteZeitSchritte[0] != 0:
                zu_loeschender_ordner_pfad = os.path.join(self.projekt_path, f"{berechneteZeitSchritte[0]}")
                print(zu_loeschender_ordner_pfad)
                # Lösche den Ordner und dessen Inhalt rekursiv
                shutil.rmtree(zu_loeschender_ordner_pfad)
            return
        if zeitSchritte is None:
            zeitSchritte = self.__behalteZeitSchritt
        if zeitSchritte <= 0:
            return
        berechneteZeitSchritte = self.get_BerechneteZeitSchritte()
        for i, ordner in enumerate(berechneteZeitSchritte[2:-1]):
            # Überprüfe, ob der Ordner eine Zahl im Namen hat und nicht durch 2000 teilbar ist und nicht der Ordner mit der größten Zahl ist
            if ordner.isdigit() and int(ordner) % zeitSchritte:
                # Passe den vollen Pfad des zu löschenden Ordners an
                zu_loeschender_ordner_pfad = os.path.join(self.projekt_path, str(ordner))
                # Lösche den Ordner und dessen Inhalt rekursiv
                shutil.rmtree(zu_loeschender_ordner_pfad)

    def _funktionDictAusfueren(self, funtionDict:dict) -> bool:
        rugabeWert: bool = False
        for funktionName in funtionDict:
            funktion = funtionDict[funktionName]
            funkAusgabe = funktion()
            print('funkAusgabe1', funkAusgabe)
            if isinstance(funkAusgabe, bool):
                if funktion():
                    self.run_abbrechen()
                    break
            elif isinstance(funkAusgabe, str):
                if ',' in funkAusgabe:
                    var_list = funkAusgabe.replace(' ','').split(',')
                else:
                    var_list = [funkAusgabe]
                var_dict: dict = {}
                for var in var_list:
                    if var not in self.__dict__.keys():
                        raise f'kreterum nicht erfühlt {var} ist nicht definiert'
                    else:
                        var_dict[var] = self.__dict__[funkAusgabe]
                funkAusgabe = funktion(**var_dict)
                def printmy(**kwargs):
                    for key, value in kwargs.items():
                        print(f'{key}: {value}')
                printmy(**var_dict)
                print('funkAusgabe',funkAusgabe)
                if funkAusgabe:
                    rugabeWert = True
        return rugabeWert

    def __ceckRun(self):
        """
        Überprüft regelmäßig, ob die Simulation abgeschlossen ist, und führt Aktionen aus, wenn Fehler auftreten oder die Simulation beendet ist.
        """

        fertig = os.path.join(self.projekt_path, "run_finished")
        if os.path.exists(fertig):
            os.remove(fertig)
        zeit_speiche = -1
        anzahl = 0
        startzeitBerechnung = time.time()
        text = ''
        while not os.path.exists(fertig):
            time.sleep(self.updateTimeSec)

            self.zeitSchritte_Endfernen()

            if self._funktionDictAusfueren(self.funktions_abbruchkreterium):
                self.run_abbrechen()
                break
                    
            maxZeit = float(self.get_BerechneteZeitSchritte()[0])
            if zeit_speiche == maxZeit:
                text = ''
                print(
                    f'\nFehler, es wurde nicht weiter gerechnet letztesmal: {sekunden_in_einheit(zeit_speiche, self.zeiteinheit)} {self.zeiteinheit.value} wir sind noch bei: {sekunden_in_einheit(maxZeit, self.zeiteinheit)} {self.zeiteinheit.value}')
                if anzahl <= 1:
                    print('vermutlich letzter Zeitschritt nicht vollständig')
                    if self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.WARTEN:
                        time.sleep(self.updateTimeSec)
                    elif self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.PROGRAM_BEENDEN:
                        # sollte noch alles geschlossen werden
                        quit()
                    elif self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.RUN_BEENDEN:
                        self.run_abbrechen()
                        break
                    elif self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.INPUT_NEUSTARTEN:
                        input('Letzter Zeitschritt prüfen\nZum Neustart Enter drücken')
                        subprocess.run(
                            ["tmux", "send-keys", "-t", self.tmuxSessionName, "HydrothermalSinglePhaseDarcyFoam_Cpr",
                             "C-m"],
                            check=True)
                    elif self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.INPUT_LETZTE_ENFERNEN_UND_NEUSTARTEN or self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.AUTO_LETZTE_ENFERNEN_UND_NEUSTARTEN:
                        if self.wasMachenBeiFehler == FehlerKeinNeuerZeitschrit.INPUT_LETZTE_ENFERNEN_UND_NEUSTARTEN:
                            input(
                                'Der letzte Zeitschritt wird gelöscht und mit dem vorhergehenden fortgefahren.\nZum Neustart Enter drücken')
                        maxZeit = float(self.get_BerechneteZeitSchritte()[0])
                        if zeit_speiche == maxZeit:
                            self._funktionDictAusfueren(self.funktions_LETZTE_ENFERNEN_UND_NEUSTARTEN)
                            print('neu start')
                            self.run_abbrechen()
                            time.sleep(0.5)
                            subprocess.run(
                                ["tmux", "send-keys", "-t", self.tmuxSessionName, f"cd {self.projekt_path_docker}",
                                 "C-m"],
                                check=True)
                            time.sleep(0.5)
                            subprocess.run(
                                ["tmux", "send-keys", "-t", self.tmuxSessionName,
                                 "HydrothermalSinglePhaseDarcyFoam_Cpr", "C-m"],
                                check=True)
                        else:
                            print('Funktioniert doch!')
                else:
                    print('Fehler ignorieren Fehler konnte nicht behoben werden')

                    subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "C-c"], check=True)
                    time.sleep(1)
                    break

            zeit_speiche = maxZeit
            sys.stdout.write('\b' * len(text))
            text = f'Berechnete zeit: {sekunden_in_einheit(zeit_speiche, self.zeiteinheit)} {self.zeiteinheit.value} Laufzeit: {round(time.time() - startzeitBerechnung)} S'
            sys.stdout.write(text)
            # Leeren des Ausgabepuffers, um die Ausgabe sofort anzuzeigen
            sys.stdout.flush()
            anzahl += 1
        print('Rechnung geändert')

    def run_weiter(self):
        """
        Setzt die Simulation fort, indem sie in einer tmux-Session den Simulationsbefehl ausführt.
        """
        if 'startFrom' in self._runParameter.keys():
            self.set_Parameter(startFrom='latestTime')

        time.sleep(0.2)
        # subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "C-u", "clear-history", "C-m"], check=True)
        print('docker', self.projekt_path_docker)
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, self.application, "C-m"],
                       check=True)
        time.sleep(0.2)
        self.__ceckRun()

    def sind_dicts_gleich(self, dict1, dict2, toleranz=None):
        for key in dict1:
            if key not in dict2:
                return False  # Die Schlüssel sind nicht gleich

            val1 = dict1[key]
            val2 = dict2[key]

            if isinstance(val1, str) and isinstance(val2, str):
                try:
                    val1 = float(val1)
                    val2 = float(val2)
                except ValueError:
                    return False  # Eine der Zeichenfolgen kann nicht in eine Zahl umgewandelt werden

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if toleranz is not None:
                    if abs(val1 - val2) > toleranz * abs(val1):
                        return False  # Die numerischen Werte unterscheiden sich um mehr als die Toleranz
                elif val1 != val2:
                    return False  # Die numerischen Werte sind nicht gleich
            elif val1 != val2:
                return False  # Die nicht-numerischen Werte sind nicht gleich

        return True  # Alle Schlüssel/Werte-Paare sind gleich

    def ist_schon_berechnet(self, toleranz: float = None) -> str | None:
        """
        Überprüft, ob eine ähnliche Simulation bereits durchgeführt wurde, basierend auf den Modellparametern und einer angegebenen Toleranz.

        :param toleranz: Die Toleranz, innerhalb derer Parameterwerte als gleich betrachtet werden. Wenn None, wird der intern gespeicherte Toleranzwert verwendet.
        :return: Den Namen des Projekts, das bereits mit ähnlichen Parametern berechnet wurde, oder None, wenn kein solches Projekt gefunden wurde.
        """
        if toleranz is not None:
            toleranz = self.toleranzBeiSuche
        # Finde alle Ordner, die mit "..." beginnen
        names_folderList = glob.glob(os.path.join(self.root_path, f"{self.projekt_ortner}*"))
        my_data = self.get_modelParameter(list(self._modelParameter.keys()))
        for names_folder in names_folderList:
            if names_folder.split('/')[-1] == self.projekt_ortner:
                continue
            folder_data = self.get_modelParameter(list(self._modelParameter.keys()), names_folder)

            if self.sind_dicts_gleich(folder_data, my_data, toleranz):
                return names_folder
        return None

    def run_start(self, notMove: bool = False):
        """
        Startet die Simulation, indem zuerst geprüft wird, ob eine ähnliche Simulation bereits durchgeführt wurde. Wenn ja, wird diese fortgesetzt; wenn nein, wird eine neue Simulation gestartet.
        :param notMove: Wechseln Sie nicht den Ordner, in dem es sich befindet. (bool) normal auf False
        """
        langer_strich = '-' * 50  # Erzeugt einen langen Strich aus 50 Bindestrichen
        print(langer_strich)
        schon_da = self.ist_schon_berechnet()
        if schon_da is not None and self.sucheAnderProjekteDieSchonMalMitDennParameterenBerechnetWurden and not notMove:
            schon_da = str(schon_da).split('/')[-1]
            print(f'wurde schon mal berechnet, rechen in Projekt {schon_da} weiter ')

            self._runParameter_wertSpeicher = self.get_runParameter()
            self.set_projekt_ortner(schon_da)
            # run parameter in das neue projekt mit übernemen
            for key in self._runParameter_wertSpeicher.keys():
                self.set_Parameter(**{key: self._runParameter_wertSpeicher[key]})
            self.run_weiter()
            self.set_projekt_ortner(self._home_projekt_ortner)
            return

        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "./run.sh", "C-m"], check=True)
        print('Neu Berechnung beginnt')
        self.__ceckRun()
        print("Prozess beendet.")
        self.projekt_abschlissen()

    def projekt_abschlissen(self):
        if self.projekt_ortner != self._home_projekt_ortner:
            return
        # projekt kopieren
        name = self.dict_zu_keyValue_string(self._modelParameter)
        destination_directory = os.path.join(self.root_path,
                                             f'{self.projekt_ortner}_{name}_{time.strftime("%Y%m%d-%H%M")}')
        shutil.copytree(self.projekt_path, destination_directory)
        # projekt zurück setzen
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "./clean.sh", "C-m"], check=True)
        time.sleep(2)
        while True:
            berechneteZeitSchritte = self.get_BerechneteZeitSchritte()
            if len(berechneteZeitSchritte[:-1]) == 0:
                break


    def run_abbrechen(self) :
        """
        Bricht die laufende Simulation ab und führt notwendige Aufräumarbeiten durch. (löscht den lezten zeitschrit könnte nicht zuende berechnet sein) )
        """
        subprocess.run(["tmux", "send-keys", "-t", self.tmuxSessionName, "C-c"], check=True)
        time.sleep(0.2)
        self.zeitSchritte_Endfernen(-1)
        self._funktionDictAusfueren(self.funktions_beiAbbruch)
        time.sleep(0.1)


    def dict_zu_keyValue_string(self, d):
        keyValue_paare = []
        for key, value in d.items():
            if isinstance(value, Parameter):
                value = value.get_Line()
            keyValue_paare.append(f"{key}{value}")
        resultierender_string = "_".join(keyValue_paare)
        return resultierender_string



