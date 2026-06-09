# -*- coding: utf-8 -*-
"""
=====================================================================
  CODE CORRECTEUR QUANTIQUE A 3 QUBITS  (version pedagogique)
  Correction d'une erreur de type "bit-flip" (porte X)
=====================================================================

  Idee generale :
  Un qubit est fragile : une erreur peut inverser sa valeur (porte X).
  Comme on ne peut pas le copier (theoreme de non-clonage), on REPARTIT
  son information sur 3 qubits, on detecte ou se trouve l'erreur sans
  regarder le qubit lui-meme, puis on la corrige.

  Le programme se lit en 5 etapes :
    1. On prepare le qubit a proteger.
    2. On l'encode sur 3 qubits.
    3. On injecte volontairement une erreur (une porte X).
    4. On mesure le "syndrome" : il indique le qubit touche.
    5. On corrige, puis on mesure pour verifier.

  Installation (une seule fois) :  pip install qiskit qiskit-aer matplotlib
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt


# =====================================================================
#  REGLAGES (on peut les modifier facilement)
# =====================================================================

# Etat du qubit a proteger : "zero" -> |0> , "un" -> |1> , "superposition"
ETAT_INITIAL = "superposition"

# Sur quel qubit (0, 1 ou 2) on injecte l'erreur. 1 = celui du milieu.
QUBIT_ERRONE = 1

# Nombre de fois ou l'on repete l'experience (pour avoir des statistiques)
NB_REPETITIONS = 1000


# =====================================================================
#  CONSTRUCTION DU CIRCUIT (les 5 etapes)
# =====================================================================

def construire_circuit(avec_correction):
    """Construit le circuit complet.
    Si avec_correction = False, on saute l'etape 4 (pour montrer l'erreur)."""

    # 3 qubits "de donnees" (le qubit logique) + 2 qubits "ancillas" (pour le syndrome)
    q = QuantumRegister(3, "q")          # q[0], q[1], q[2] : les donnees
    a = QuantumRegister(2, "a")          # a[0], a[1]       : les ancillas
    syndrome = ClassicalRegister(2, "syndrome")   # ou l'on note le syndrome
    sortie = ClassicalRegister(3, "sortie")       # ou l'on note la mesure finale
    qc = QuantumCircuit(q, a, syndrome, sortie)

    # ----- ETAPE 1 : preparer le qubit a proteger -----
    if ETAT_INITIAL == "zero":
        pass                              # |0> : rien a faire, c'est l'etat de depart
    elif ETAT_INITIAL == "un":
        qc.x(q[0])                        # la porte X (= NOT) transforme |0> en |1>
    elif ETAT_INITIAL == "superposition":
        qc.h(q[0])                        # la porte de Hadamard cree (|0> + |1>)/racine(2)

    # ----- ETAPE 2 : encodage sur 3 qubits avec 2 portes CNOT -----
    # On recopie la "structure" du qubit q[0] sur q[1] et q[2].
    #   |0> devient |000>   et   |1> devient |111>
    qc.cx(q[0], q[1])                     # CNOT : q[0] controle q[1]
    qc.cx(q[0], q[2])                     # CNOT : q[0] controle q[2]
    qc.barrier(label="encodage")

    # ----- ETAPE 3 : injecter une erreur (porte X) -----
    qc.x(q[QUBIT_ERRONE])                 # une erreur inverse ce qubit
    qc.barrier(label="erreur")

    # ----- ETAPE 4a : mesurer le syndrome -----
    # On compare les qubits 2 a 2 SANS regarder leur valeur, grace aux ancillas.
    #   a[0] retient si q[0] et q[1] sont differents
    #   a[1] retient si q[1] et q[2] sont differents
    qc.cx(q[0], a[0])
    qc.cx(q[1], a[0])
    qc.cx(q[1], a[1])
    qc.cx(q[2], a[1])
    qc.measure(a[0], syndrome[0])        # on ne mesure QUE les ancillas
    qc.measure(a[1], syndrome[1])
    qc.barrier(label="syndrome")

    # ----- ETAPE 4b : corriger selon le syndrome -----
    # Le syndrome est un nombre (= a[0] + 2*a[1]) qui designe le qubit a reparer :
    #   1  ->  erreur sur q[0]      2  ->  erreur sur q[2]
    #   3  ->  erreur sur q[1]      0  ->  aucune erreur
    if avec_correction:
        with qc.if_test((syndrome, 1)):  # si syndrome = 1
            qc.x(q[0])                   # on repare q[0]
        with qc.if_test((syndrome, 3)):  # si syndrome = 3
            qc.x(q[1])                   # on repare q[1]
        with qc.if_test((syndrome, 2)):  # si syndrome = 2
            qc.x(q[2])                   # on repare q[2]
        qc.barrier(label="correction")

    # ----- ETAPE 5 : mesurer les 3 qubits de donnees pour verifier -----
    qc.measure(q[0], sortie[0])
    qc.measure(q[1], sortie[1])
    qc.measure(q[2], sortie[2])

    return qc


# =====================================================================
#  SIMULATION
# =====================================================================

def simuler(qc):
    """Execute le circuit NB_REPETITIONS fois et renvoie les resultats comptes."""
    simulateur = AerSimulator()
    circuit_pret = transpile(qc, simulateur)
    resultat = simulateur.run(circuit_pret, shots=NB_REPETITIONS).result()
    return resultat.get_counts()


def afficher(titre, comptes):
    """Affiche les resultats. Chaque cle a la forme 'sortie syndrome', ex : '111 11'."""
    print(f"\n{titre}")
    for cle, n in sorted(comptes.items(), key=lambda x: x[1], reverse=True):
        donnees, syn = cle.split(" ")
        print(f"   qubit mesure = {donnees}   (syndrome = {syn})   "
              f"obtenu {n} fois sur {NB_REPETITIONS}")


# =====================================================================
#  PROGRAMME PRINCIPAL
# =====================================================================

print("=" * 60)
print(" CODE CORRECTEUR A 3 QUBITS — correction d'une erreur X")
print("=" * 60)
print(f" Qubit protege : etat '{ETAT_INITIAL}'")
print(f" Erreur injectee sur le qubit numero {QUBIT_ERRONE}")

# On affiche le circuit complet (utile pour bien le visualiser)
circuit_complet = construire_circuit(avec_correction=True)
print("\nSchema du circuit :")
print(circuit_complet.draw(output="text"))

# Sauvegarde d'un schema en image (si la librairie est disponible)
try:
    figure_circuit = circuit_complet.draw(
        output="mpl",
        fold=-1
    )

    figure_circuit.savefig(
        "schema_circuit.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(figure_circuit)

    print("\nSchema enregistre dans schema_circuit.png")

except Exception as e:
    print("\nErreur generation schema :")
    print(e)

# 1) On lance SANS l'etape de correction : l'erreur reste presente
comptes_sans = simuler(construire_circuit(avec_correction=False))
afficher(">>> SANS correction : le qubit reste casse", comptes_sans)

# 2) On lance AVEC l'etape de correction : le qubit est repare
comptes_avec = simuler(construire_circuit(avec_correction=True))
afficher(">>> AVEC correction : le qubit est repare", comptes_avec)

# Histogramme comparatif (sans correction vs avec correction)
figure = plot_histogram(
    [comptes_sans, comptes_avec],
    legend=["Sans correction", "Avec correction"],
    title="Code 3 qubits : avant et apres correction",
)
figure.savefig("histogramme.png", dpi=300, bbox_inches="tight")
print("\nHistogramme enregistre dans histogramme.png")
plt.show()
