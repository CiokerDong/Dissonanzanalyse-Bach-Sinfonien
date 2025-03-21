
from music21 import stream, meter, converter

def Taktart_Analyse(score):
    """
    Bestimmung der Taktart eines Musikstücks: 
    Dreier-Takt, Zweier-Takt oder gemischten Takt
    """
    if not isinstance(score, (stream.Score, stream.Part)):
        raise ValueError("Input must be a music21 stream.Score or stream.Part")

    time_signatures = score.flatten().getElementsByClass(meter.TimeSignature)

    for ts in time_signatures:
        numerator = ts.numerator
        if numerator % 3 == 0:
            return "Dreier-Takt"   #"Wenn der Zähler durch 3 ist, wird 'Dreier-Takt' rückgegeben."
        elif numerator % 2 == 0:
            return "Zweier-Takt"    #"Wenn der Zähler durch 2 ist, wird 'Dreier-Takt' rückgegeben."

    return "gemischter Takt"  #"Wenn der Zähler weder durch 3 noch durch 2 teilbar ist, wird 'gemischter Takt' ausgegeben."


from music21 import duration

def GrundrhythmusallerStimmen_dict(score):
    """
    Im chordify-Zustand den gemeinsamen Grundrhythmus aller Stimmen für jeden Takt bestimmen. 
    Erkenne für jeden Takt die am häufigsten vorkommende Notentyp in allen Stimmen
    und definiere diese als den grundlegenden rhythmischen Typ für diesen Takt. 
    Schließlich füge diesen Typ als Liedtext zu jedem Takt der Partitur hinzu. 
    Diese Programm kann jetzt noch die Partitur bearbeiten, in der jede Stimme eine selbsttändige Notenzeile belegt.
    Rückgabewert:
    dict: {Taktnummer: Rhythmustyp}
    """

    chordified_score = score.chordify()
    rhythmic_patterns = {}

    for measure in chordified_score.getElementsByClass(stream.Measure):
        measure_number = measure.measureNumber
        note_durations = {}


        for element in measure.notesAndRests:
            dur_type = element.duration.type
            if dur_type not in note_durations:
                note_durations[dur_type] = 0
            note_durations[dur_type] += 1


        if note_durations:

            most_common_durations = [
                k for k, v in note_durations.items() if v == max(note_durations.values())
            ]


            most_common_duration = max(
                most_common_durations,
                key=lambda d: duration.Duration(type=d).quarterLength
            )
        else:

            most_common_duration = "unknown"

        rhythmic_patterns[measure_number] = most_common_duration
        
    return rhythmic_patterns


import numpy as np

def Bestimme_betontePosition(score):
    """
    Diese Funktion kann basierend auf den verschiedenen Taktarten und Grundrhytmus-Musteren die betonten Positionen jedes Takts bestimmen.
    Rückgabewert: dict: Die betonten Positionen jedes Takts im Format {Taktnummer: [Offsets]}."
    """

    part1 = score.parts[1]  
    taktart = Taktart_Analyse(score)
    grundrhythmus = GrundrhythmusallerStimmen_dict(score)

    betontePositionen = {}

    # Überprüfung des Durchlaufs des jeden Takts in Parts[1]
    for measure in part1.getElementsByClass(stream.Measure):
        measure_number = measure.measureNumber
        rhythm_type = grundrhythmus.get(measure_number, None)
        print(f"Takt {measure_number}, Grundrhythmus: {rhythm_type}")
         
        if rhythm_type is None:
            print(f"Takt {measure_number}: nichts")
            continue
        if measure.duration is None:
            print(f"Takt {measure_number}: keine Dauerangabe")
            continue

        # Logik für Zweiertakt
        if taktart == "Zweier-Takt":
            # jede 4tel-Note als betonte Position
            if rhythm_type in ["32th", "16th", "eighth"]:
                strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 1)]
            # jede Halbnote als betonte Position
            elif rhythm_type == "quarter":
                strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 2)]
            # jede Ganznote als betonte Position
            elif rhythm_type in ["half", "whole"]:
                strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 4)]
            # Breve als betonte Position
            else:
                strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 8)]

        # Logik für Dreiertakt
        elif taktart == "Dreier-Takt":
            time_signatures = score.flatten().getElementsByClass(meter.TimeSignature)
            for ts in time_signatures:
                denominator = ts.denominator

                # beim 8tel-Takt (3/8, 6/8, 9/8 usw.)
                if denominator == 8:
                    # jede punktierte 4tel-Note als betonte Position
                    if rhythm_type in ["16th", "eighth", "quarter"]:
                        strong_beats = [offset for offset in np.arange(0, measure.duration.quarterLength, 1.5)]
                    else:
                        strong_beats = []

                # beim 16tel-Takt (12/16, usw.)
                elif denominator == 16:
                    # jede punktierte 8tel-Note als betonte Position
                    strong_beats = [offset for offset in np.arange(0, measure.duration.quarterLength, 0.75)]

                # beim 4tel-Takt (3/4, 6/4, usw.)
                elif denominator == 4:
                    # jede 4tel-Note als betonte Position
                    if rhythm_type in ["16th", "eighth"]:
                        strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 1)]
                    # jede punktierte Halbnote als betonte Position
                    elif rhythm_type in ["quarter", "half"]:
                        strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 3)]
                    else:
                        strong_beats = []

                # beim 2tel-Takt (3/2, usw.)
                elif denominator == 2:
                    # jede Halbnote als betonte Position
                    if rhythm_type in ["eighth", "quarter"]:
                        strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 2)]
                    # jede punktierte Ganznote als betonte Position
                    elif rhythm_type in ["half", "whole"]:
                        strong_beats = [offset for offset in range(0, int(measure.duration.quarterLength), 6)]
                    else:
                        strong_beats = []

                else:
                    strong_beats = []

        else:
            strong_beats = []

        betontePositionen[measure_number] = [float(offset) for offset in strong_beats]

    return betontePositionen