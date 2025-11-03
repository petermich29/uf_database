# main.py

import database_setup
import import_data
import sys

# --- SOLUTION CRITIQUE POUR L'ENCODAGE WINDOWS ---
# Force l'encodage de sortie (stdout/stderr) en UTF-8 pour gérer les caractères spéciaux
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    print("Encodage de sortie forcé en UTF-8.")
except Exception:
    pass

if __name__ == "__main__":
    # 1. Initialisation de la BDD et des tables
    database_setup.init_db()
    
    # 2. Importation des données de métadonnées
    import_data.import_metadata_to_db()
    
    # 3. Importation des données d'inscription
    import_data.import_inscriptions_to_db()
    
    print("\nProcessus d'initialisation et d'importation terminé.")