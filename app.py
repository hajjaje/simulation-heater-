
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from CoolProp.CoolProp import PropsSI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ==========================================================
# 1. CONFIGURATION DE LA FENETRE
# ==========================================================

FLUIDE = "Water"

root = tk.Tk()
root.title("Simulation thermodynamique du Heater")
root.geometry("1250x900")
root.minsize(1000, 750)

style = ttk.Style()
style.configure("Title.TLabel", font=("Arial", 15, "bold"))
style.configure("Header.TLabel", font=("Arial", 10, "bold"))


# ==========================================================
# 2. PARAMETRES MODIFIABLES
# ==========================================================

T_entree_var = tk.StringVar(value="30")
P_entree_var = tk.StringVar(value="60")
deltaP_var = tk.StringVar(value="0")
debit_var = tk.StringVar(value="0.038")
rendement_var = tk.StringVar(value="85")
mode_var = tk.StringVar(value="Vapeur saturee")
surchauffe_var = tk.StringVar(value="25")


# ==========================================================
# 3. ORGANISATION GENERALE
# ==========================================================

main = ttk.Frame(root, padding=8)
main.pack(fill="both", expand=True)

main.columnconfigure(0, weight=1)
main.rowconfigure(3, weight=1)

ttk.Label(
    main,
    text="SIMULATION THERMODYNAMIQUE DU HEATER",
    style="Title.TLabel"
).grid(row=0, column=0, pady=(0, 8))


# ==========================================================
# 4. CHAMPS DE SAISIE
# ==========================================================

param_frame = ttk.LabelFrame(
    main, text="Paramètres modifiables", padding=8
)
param_frame.grid(row=1, column=0, sticky="ew", pady=4)

for col in range(4):
    param_frame.columnconfigure(col, weight=1)


def ajouter_champ(parent, texte, variable, ligne, colonne):
    ttk.Label(
        parent, text=texte
    ).grid(
        row=ligne, column=colonne,
        sticky="w", padx=5, pady=4
    )

    entree = ttk.Entry(
        parent, textvariable=variable, width=18
    )
    entree.grid(
        row=ligne, column=colonne + 1,
        sticky="ew", padx=5, pady=4
    )

    return entree


ajouter_champ(
    param_frame, "Température entrée (°C)",
    T_entree_var, 0, 0
)

ajouter_champ(
    param_frame, "Pression entrée absolue (kPa)",
    P_entree_var, 0, 2
)

ajouter_champ(
    param_frame, "Perte de pression ΔP (kPa)",
    deltaP_var, 1, 0
)

ajouter_champ(
    param_frame, "Débit massique (kg/s)",
    debit_var, 1, 2
)

ajouter_champ(
    param_frame, "Rendement thermique (%)",
    rendement_var, 2, 0
)

ttk.Label(
    param_frame, text="État de sortie"
).grid(
    row=2, column=2, sticky="w", padx=5, pady=4
)

ttk.Combobox(
    param_frame,
    textvariable=mode_var,
    values=[
        "Liquide sature",
        "Vapeur saturee",
        "Vapeur surchauffee"
    ],
    state="readonly",
    width=18
).grid(
    row=2, column=3, sticky="ew", padx=5, pady=4
)

ajouter_champ(
    param_frame, "Surchauffe au-dessus de Tsat (°C)",
    surchauffe_var, 3, 0
)

ttk.Label(
    param_frame,
    text="Les pressions sont absolues. ΔP = P entrée - P sortie.",
    foreground="gray"
).grid(
    row=4, column=0, columnspan=4,
    sticky="w", padx=5, pady=4
)


# ==========================================================
# 5. TABLEAU DES RESULTATS
# ==========================================================

result_frame = ttk.LabelFrame(
    main, text="Résultats du calcul", padding=8
)
result_frame.grid(row=2, column=0, sticky="ew", pady=4)

for col in range(4):
    result_frame.columnconfigure(col, weight=1)

result_keys = [
    ("Teb", "Température d'ébullition (°C)"),
    ("Psortie", "Pression de sortie (kPa abs)"),
    ("DeltaP", "Variation de pression ΔP (kPa)"),
    ("Tsortie", "Température de sortie (°C)"),
    ("hentree", "Enthalpie entrée (kJ/kg)"),
    ("hsortie", "Enthalpie sortie (kJ/kg)"),
    ("Q", "Puissance thermique utile (kW)"),
    ("Qfourni", "Puissance à fournir (kW)"),
    ("Debit", "Débit massique (kg/h)"),
    ("Etat", "État thermodynamique de sortie")
]

result_labels = {}

for i, (key, label) in enumerate(result_keys):
    row = i // 2
    col = (i % 2) * 2

    ttk.Label(
        result_frame, text=label + " :"
    ).grid(
        row=row, column=col,
        sticky="w", padx=5, pady=3
    )

    valeur_label = ttk.Label(
        result_frame, text="--",
        font=("Arial", 9, "bold")
    )
    valeur_label.grid(
        row=row, column=col + 1,
        sticky="w", padx=5, pady=3
    )

    result_labels[key] = valeur_label


# ==========================================================
# 6. BOUTONS - PLACES AVANT LES GRAPHIQUES
# ==========================================================

button_frame = ttk.Frame(main)
button_frame.grid(row=4, column=0, sticky="ew", pady=6)

# Les boutons sont définis ici.
# La fonction calculer() sera appelée au clic.

ttk.Button(
    button_frame,
    text="Calculer / Actualiser",
    command=lambda: calculer()
).pack(side="left", padx=5)

ttk.Button(
    button_frame,
    text="Réinitialiser",
    command=lambda: reinitialiser()
).pack(side="left", padx=5)

ttk.Button(
    button_frame,
    text="Quitter",
    command=root.destroy
).pack(side="right", padx=5)


# ==========================================================
# 7. GRAPHIQUES INTEGRES DANS LA FENETRE
# ==========================================================

fig, axes = plt.subplots(
    2, 2, figsize=(12, 6.5)
)

ax1 = axes[0, 0]
ax2 = axes[0, 1]
ax3 = axes[1, 0]
ax4 = axes[1, 1]

fig.tight_layout(pad=3)

canvas = FigureCanvasTkAgg(fig, master=main)
canvas_widget = canvas.get_tk_widget()

canvas_widget.grid(
    row=3, column=0, sticky="nsew", pady=4
)


# ==========================================================
# 8. FONCTION POUR FORMATER LES RESULTATS
# ==========================================================

def format_fr(valeur, decimales=3):
    return f"{valeur:.{decimales}f}".replace(".", ",")


# ==========================================================
# 9. FONCTION PRINCIPALE DE CALCUL
# ==========================================================

def calculer():

    try:
        # Lecture des paramètres
        T_in_C = float(T_entree_var.get().replace(",", "."))
        P_in_kPa = float(P_entree_var.get().replace(",", "."))
        deltaP_kPa = float(deltaP_var.get().replace(",", "."))
        debit = float(debit_var.get().replace(",", "."))
        rendement_pct = float(rendement_var.get().replace(",", "."))
        surchauffe_C = float(surchauffe_var.get().replace(",", "."))

        # Conversion des unités
        P_in = P_in_kPa * 1000
        delta_P = deltaP_kPa * 1000
        P_out = P_in - delta_P

        T_in = T_in_C + 273.15
        rendement = rendement_pct / 100

        # Vérification des données
        if P_in <= 0:
            raise ValueError("La pression d'entrée doit être positive.")

        if delta_P < 0:
            raise ValueError("La perte de pression doit être positive ou nulle.")

        if P_out <= 0:
            raise ValueError(
                "La pression de sortie est nulle ou négative. "
                "Réduisez la perte de pression."
            )

        if debit <= 0:
            raise ValueError("Le débit massique doit être positif.")

        if not 0 < rendement <= 1:
            raise ValueError("Le rendement doit être compris entre 0 et 100 %.")

        if surchauffe_C < 0:
            raise ValueError("La surchauffe ne peut pas être négative.")

        # État d'entrée : vérifier que l'eau est dans un état valide
        h_in = PropsSI("H", "T", T_in, "P", P_in, FLUIDE)

        # Température d'ébullition à la pression de sortie
        T_sat = PropsSI("T", "P", P_out, "Q", 0, FLUIDE)
        T_sat_C = T_sat - 273.15

        # Enthalpies de saturation
        h_liq_sat = PropsSI("H", "P", P_out, "Q", 0, FLUIDE)
        h_vap_sat = PropsSI("H", "P", P_out, "Q", 1, FLUIDE)

        # Définition de l'état de sortie
        mode = mode_var.get()

        if mode == "Liquide sature":
            T_out = T_sat
            h_out = h_liq_sat
            etat = "Liquide saturé"

        elif mode == "Vapeur saturee":
            T_out = T_sat
            h_out = h_vap_sat
            etat = "Vapeur saturée"

        else:
            T_out = T_sat + surchauffe_C
            h_out = PropsSI(
                "H", "T", T_out, "P", P_out, FLUIDE
            )
            etat = "Vapeur surchauffée"

        T_out_C = T_out - 273.15

        # Bilan énergétique
        Q_W = debit * (h_out - h_in)
        Q_fourni_W = Q_W / rendement

        # Mise à jour du tableau
        valeurs = {
            "Teb": f"{format_fr(T_sat_C)} °C",
            "Psortie": f"{format_fr(P_out / 1000, 4)} kPa",
            "DeltaP": f"{format_fr(delta_P / 1000, 4)} kPa",
            "Tsortie": f"{format_fr(T_out_C)} °C",
            "hentree": f"{format_fr(h_in / 1000)} kJ/kg",
            "hsortie": f"{format_fr(h_out / 1000)} kJ/kg",
            "Q": f"{format_fr(Q_W / 1000)} kW",
            "Qfourni": f"{format_fr(Q_fourni_W / 1000)} kW",
            "Debit": f"{format_fr(debit * 3600)} kg/h",
            "Etat": etat
        }

        for key, valeur in valeurs.items():
            result_labels[key].config(text=valeur)

        # --------------------------------------------------
        # Sensibilité : faire varier la perte de pression
        # --------------------------------------------------

        P_triple = PropsSI("PTRIPLE", FLUIDE)

        # Éviter une pression trop basse hors du domaine
        # où la température de saturation est définie.
        P_min = max(P_triple * 1.01, 1000.0)

        if P_in <= P_min:
            raise ValueError(
                "La pression d'entrée est trop faible "
                "pour tracer la courbe de saturation."
            )

        deltaP_max = min(
            max(delta_P * 1.05, P_in * 0.50, 10000.0),
            P_in - P_min
        )

        deltaP_range = np.linspace(0, deltaP_max, 100)
        P_out_range = P_in - deltaP_range

        T_sat_range = []
        Q_sat_range = []

        for P in P_out_range:
            Ts = PropsSI("T", "P", P, "Q", 0, FLUIDE)
            hv = PropsSI("H", "P", P, "Q", 1, FLUIDE)

            T_sat_range.append(Ts - 273.15)

            # Puissance requise pour obtenir de la vapeur saturée
            Q_sat_range.append(
                debit * (hv - h_in) / 1000
            )

        T_sat_range = np.array(T_sat_range)
        Q_sat_range = np.array(Q_sat_range)
        P_out_range_kPa = P_out_range / 1000

        # --------------------------------------------------
        # Graphe 1 : température d'ébullition vs perte de P
        # --------------------------------------------------

        ax1.clear()

        ax1.plot(
            deltaP_range / 1000,
            T_sat_range,
            linewidth=2,
            label="Température de saturation"
        )

        ax1.scatter(
            [delta_P / 1000],
            [T_sat_C],
            s=70,
            zorder=5,
            label="Point de fonctionnement"
        )

        ax1.set_title("Température d'ébullition selon ΔP")
        ax1.set_xlabel("Perte de pression ΔP (kPa)")
        ax1.set_ylabel("Température d'ébullition (°C)")
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=8)

        # --------------------------------------------------
        # Graphe 2 : pression de sortie vs perte de pression
        # --------------------------------------------------

        ax2.clear()

        ax2.plot(
            deltaP_range / 1000,
            P_out_range_kPa,
            linewidth=2,
            label="Pression de sortie"
        )

        ax2.scatter(
            [delta_P / 1000],
            [P_out / 1000],
            s=70,
            zorder=5,
            label="Point de fonctionnement"
        )

        ax2.set_title("Variation de la pression")
        ax2.set_xlabel("Perte de pression ΔP (kPa)")
        ax2.set_ylabel("Pression de sortie absolue (kPa)")
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=8)

        # --------------------------------------------------
        # Graphe 3 : pression de sortie vs température
        # --------------------------------------------------

        ax3.clear()

        ax3.plot(
            P_out_range_kPa,
            T_sat_range,
            linewidth=2,
            label="Courbe de saturation"
        )

        ax3.scatter(
            [P_out / 1000],
            [T_sat_C],
            s=70,
            zorder=5,
            label="Point de fonctionnement"
        )

        ax3.set_title("Pression et température d'ébullition")
        ax3.set_xlabel("Pression de sortie (kPa abs)")
        ax3.set_ylabel("Température de saturation (°C)")
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=8)

        # --------------------------------------------------
        # Graphe 4 : puissance thermique vs pression
        # --------------------------------------------------

        ax4.clear()

        ax4.plot(
            P_out_range_kPa,
            Q_sat_range,
            linewidth=2,
            label="Puissance pour vapeur saturée"
        )

        ax4.scatter(
            [P_out / 1000],
            [Q_W / 1000],
            s=70,
            zorder=5,
            label="Point de fonctionnement"
        )

        ax4.set_title("Puissance thermique selon la pression")
        ax4.set_xlabel("Pression de sortie (kPa abs)")
        ax4.set_ylabel("Puissance thermique (kW)")
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=8)

        fig.tight_layout(pad=2.5)
        canvas.draw()

    except ValueError as e:
        messagebox.showerror(
            "Erreur de saisie",
            str(e)
        )

    except Exception as e:
        messagebox.showerror(
            "Erreur de calcul",
            "Le calcul thermodynamique a échoué.\n\n"
            "Vérifiez les paramètres saisis.\n\n"
            f"Détail : {e}"
        )


# ==========================================================
# 10. REINITIALISATION DES PARAMETRES
# ==========================================================

def reinitialiser():
    T_entree_var.set("30")
    P_entree_var.set("60")
    deltaP_var.set("0")
    debit_var.set("0.038")
    rendement_var.set("85")
    mode_var.set("Vapeur saturee")
    surchauffe_var.set("25")

    calculer()


# ==========================================================
# 11. LANCEMENT DE L'INTERFACE
# ==========================================================

# Calcul initial au démarrage
calculer()

root.mainloop()