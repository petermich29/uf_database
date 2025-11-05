# import_data.py

import pandas as pd
import sys
import logging
from tqdm import tqdm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError
from datetime import date 

import config
import database_setup
from models import (
    Institution, Composante, Domaine, Mention, Parcours, 
    AnneeUniversitaire, Etudiant, Inscription
)

# Configuration du logging (inchangée)
logging.basicConfig(filename='import_errors.log', 
                    filemode='w', 
                    encoding='utf-8',
                    level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def safe_string(s):
    """
    Conserve les caractères spéciaux et accents (UTF-8) tout en gérant les espaces (strip).
    """
    if s is None or not isinstance(s, str):
        return s
    
    s = s.strip()
    
    return s.encode('utf-8', errors='ignore').decode('utf-8')


# ----------------------------------------------------------------------
# FONCTIONS D'IMPORTATION UNITAIRE DE LA STRUCTURE ACADÉMIQUE
# ----------------------------------------------------------------------

def _import_institutions(session: Session) -> bool:
    """Charge et importe la table Institution."""
    print("\n--- Importation des Institutions ---")
    try:
        df_inst = pd.read_excel(config.INSTITUTION_FILE_PATH)
        df_inst.columns = df_inst.columns.str.lower().str.replace(' ', '_')
        df_inst = df_inst.where(pd.notnull(df_inst), None)
        
        df_inst['institution_id'] = df_inst['institution_id'].astype(str).apply(safe_string)
        df_inst_clean = df_inst.drop_duplicates(subset=['institution_id']).dropna(subset=['institution_id'])
        
        for _, row in tqdm(df_inst_clean.iterrows(), total=len(df_inst_clean), desc="Institutions"):
            session.merge(Institution(
                id_institution=row['institution_id'], 
                nom=safe_string(row['institution_nom']),
                type_institution=safe_string(row['institution_type'])
            ))
        
        session.commit()
        print("✅ Importation des Institutions terminée.")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: Impossible de lire ou d'importer le fichier Institutions. {e}", file=sys.stderr)
        session.rollback()
        return False


def _import_composantes(session: Session, df: pd.DataFrame):
    """Importe les Composantes (dépend d'Institution)."""
    print("\n--- Importation des Composantes ---")
    df_composantes = df[['composante', 'label_composante', 'institution_id']].drop_duplicates(subset=['composante']).dropna(subset=['composante'])
    
    for _, row in tqdm(df_composantes.iterrows(), total=len(df_composantes), desc="Composantes"):
        session.merge(Composante(
            code=row['composante'], 
            label=safe_string(row['label_composante']),
            id_institution=row['institution_id'] # Clé Étrangère
        ))


def _import_domaines(session: Session, df: pd.DataFrame):
    """Importe les Domaines."""
    print("\n--- Importation des Domaines ---")
    df_domaines = df[['domaine', 'label_domaine']].drop_duplicates(subset=['domaine']).dropna(subset=['domaine'])
    
    for _, row in tqdm(df_domaines.iterrows(), total=len(df_domaines), desc="Domaines"):
        session.merge(Domaine(code=row['domaine'], label=safe_string(row['label_domaine'])))


def _import_mentions(session: Session, df: pd.DataFrame):
    """Importe les Mentions (dépend de Composante et Domaine)."""
    print("\n--- Importation des Mentions ---")
    df_mentions_source = df[['mention', 'label_mention', 'id_mention', 'composante', 'domaine']].drop_duplicates(subset=['id_mention']).dropna(subset=['id_mention'])
    
    for _, row in tqdm(df_mentions_source.iterrows(), total=len(df_mentions_source), desc="Mentions"):
        session.merge(Mention(
            id_mention=row['id_mention'],           
            code_mention=safe_string(row['mention']),
            label=safe_string(row['label_mention']),
            composante_code=row['composante'], 
            domaine_code=row['domaine']
        ))
    return df_mentions_source # Retourne le DF source pour la jointure des Parcours


def _import_parcours(session: Session, df: pd.DataFrame, df_mentions_source: pd.DataFrame):
    """Importe les Parcours (dépend de Mention), en utilisant id_mention directement."""
    print("\n--- Importation des Parcours ---")
    
    # 1. Préparation des Parcours - UTILISER ID_MENTION DIRECTEMENT DU DF PRINCIPAL (si elle y est)
    # Nous assumons que df contient la colonne 'id_mention' nettoyée
    df_parcours = df[['id_parcours', 'parcours', 'label_parcours', 'id_mention', 'date_creation', 'date_fin']].copy()
    
    # Remplacer df_parcours_merged par df_parcours
    df_parcours = df_parcours.drop_duplicates(subset=['id_parcours'], keep='first').dropna(subset=['id_parcours', 'id_mention'])

    nombre_parcours_uniques = len(df_parcours)
    
    # La variable row['id_mention'] est désormais directement disponible
    for _, row in tqdm(df_parcours.iterrows(), total=nombre_parcours_uniques, desc="Parcours"):
        
        # Gestion sécurisée des dates
        date_creation_val = int(row['date_creation']) if pd.notna(row['date_creation']) and row['date_creation'] is not None else None
        date_fin_val = int(row['date_fin']) if pd.notna(row['date_fin']) and row['date_fin'] is not None else None
        
        session.merge(Parcours(
            id_parcours=row['id_parcours'], 
            code_parcours=safe_string(row['parcours']), 
            label=safe_string(row['label_parcours']),
            # Utilisation de l'ID correct récupéré du fichier source
            mention_id=row['id_mention'], 
            date_creation=date_creation_val,
            date_fin=date_fin_val
        ))
    
    # Retirer le paramètre df_mentions_source si cette solution est adoptée dans l'orchestrateur.


def _load_and_clean_metadata():
    """Charge et nettoie le fichier de métadonnées académiques."""
    try:
        df = pd.read_excel(config.METADATA_FILE_PATH)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        df = df.where(pd.notnull(df), None)
        print(f"Fichier de métadonnées académiques chargé. {len(df)} lignes trouvées.")
        
        # --- Nettoyage initial et obligatoire des clés critiques ---
        df['institution_id'] = df['institution_id'].astype(str).apply(safe_string) 
        df['composante'] = df['composante'].astype(str).apply(safe_string)
        df['domaine'] = df['domaine'].astype(str).apply(safe_string)
        df['id_mention'] = df['id_mention'].astype(str).apply(safe_string) 
        df['id_parcours'] = df['id_parcours'].astype(str).apply(safe_string)
        
        return df
        
    except Exception as e:
        print(f"❌ ERREUR: Impossible de lire le fichier de métadonnées académiques. {e}", file=sys.stderr)
        return None
        
# ----------------------------------------------------------------------
# FONCTION ORCHESTRATRICE DE LA STRUCTURE ACADÉMIQUE
# ----------------------------------------------------------------------

def import_metadata_to_db():
    """
    Orchestre l'importation de la structure académique (Institutions, Composantes, Domaines, 
    Mentions, Parcours) dans le bon ordre.
    """
    print(f"\n--- 2. Démarrage de l'importation des métadonnées ---")
    session = database_setup.get_session()

    try:
        # 1. Importation des Institutions (étape critique)
        if not _import_institutions(session):
            return

        # 2. Chargement et nettoyage du DF de métadonnées
        df_metadata = _load_and_clean_metadata()
        if df_metadata is None:
            return

        # 3. Importation ordonnée des entités restantes
        _import_composantes(session, df_metadata) # Dépend d'Institution
        _import_domaines(session, df_metadata)
        
        df_mentions_source = _import_mentions(session, df_metadata) # Dépend de Composante/Domaine

        _import_parcours(session, df_metadata, df_mentions_source) # Dépend de Mention

        session.commit()
        print("\n✅ Importation des métadonnées académiques (Composante, etc.) terminée avec succès.")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERREUR D'IMPORTATION (Métadonnées): {e}", file=sys.stderr)
    finally:
        session.close()


# ----------------------------------------------------------------------
# FONCTIONS D'IMPORTATION UNITAIRE DES INSCRIPTIONS
# ----------------------------------------------------------------------

def _load_and_clean_inscriptions():
    """Charge et nettoie le fichier d'inscriptions."""
    try:
        df = pd.read_excel(config.INSCRIPTION_FILE_PATH)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Conversion des colonnes de dates au format Python Date
        date_cols = ['naissance_date', 'cin_date']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True).dt.date
            
        df = df.where(pd.notnull(df), None) 
        print(f"Fichier XLSX d'inscriptions chargé. {len(df)} lignes trouvées.")
        
        # --- Renommage critique pour la jointure/FK (fait ici pour que 'id_parcours' soit la colonne de travail) ---
        if 'id_parcours_caractere' in df.columns:
            df.rename(columns={'id_parcours_caractere': 'id_parcours'}, inplace=True) 
        
        # Nettoyage de la clé étrangère du parcours
        if 'id_parcours' in df.columns:
             df['id_parcours'] = df['id_parcours'].astype(str).apply(safe_string) 

        return df
        
    except Exception as e:
        print(f"❌ ERREUR: Impossible de lire le fichier XLSX d'inscriptions. {e}", file=sys.stderr)
        return None


def _import_annees_universitaires(session: Session, df: pd.DataFrame):
    """Importe les Années Universitaires."""
    print("\n--- Importation des Années Universitaires ---")
    annees = df['annee_universitaire'].drop_duplicates().dropna()
    for annee in tqdm(annees, desc="Années Univ."):
        session.merge(AnneeUniversitaire(annee=safe_string(annee)))
    session.commit()
    print("✅ Années Universitaires insérées/mises à jour.")


def _import_etudiants(session: Session, df: pd.DataFrame):
    """Importe les Étudiants avec gestion d'erreurs (commit par ligne)."""
    print("\n--- Importation des Étudiants (Ligne par Ligne FORCÉE) ---")
    df_etudiants = df.drop_duplicates(subset=['code_etudiant']).dropna(subset=['code_etudiant'])
    etudiant_errors = 0
    
    for index, row in tqdm(df_etudiants.iterrows(), total=len(df_etudiants), desc="Import Etudiants"):
        code_etudiant = row.get('code_etudiant', 'N/A')
        
        try:
            naissance_date_val = row['naissance_date'] if isinstance(row['naissance_date'], date) else None
            cin_date_val = row['cin_date'] if isinstance(row['cin_date'], date) else None
            
            session.merge(Etudiant(
                code_etudiant=safe_string(code_etudiant), 
                numero_inscription=safe_string(row.get('numero_inscription')),
                nom=safe_string(row['nom']), 
                prenoms=safe_string(row['prenoms']),
                sexe=safe_string(row['sexe']), 
                naissance_date=naissance_date_val, 
                naissance_lieu=safe_string(row.get('naissance_lieu')),
                nationalite=safe_string(row.get('nationalite')),
                bacc_annee=int(row['bacc_annee']) if pd.notna(row['bacc_annee']) and row['bacc_annee'] is not None else None,
                bacc_serie=safe_string(row.get('bacc_serie')), 
                bacc_centre=safe_string(row.get('bacc_centre')),
                adresse=safe_string(row.get('adresse')), 
                telephone=safe_string(row.get('telephone')), 
                mail=safe_string(row.get('mail')),
                cin=safe_string(row.get('cin')), 
                cin_date=cin_date_val, 
                cin_lieu=safe_string(row.get('cin_lieu'))
            ))
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            etudiant_errors += 1
            e_msg = str(e.orig).lower() if hasattr(e, 'orig') and e.orig else str(e)
            
            # Gestion d'erreurs (inchangée)
            if "stringdatarighttruncation" in e_msg:
                 col_suspecte = "Taille de VARCHAR inconnue"
                 if "varying(50)" in e_msg: col_suspecte = "VARCHAR(50) - (bacc_serie)"
                 elif "varying(100)" in e_msg: col_suspecte = "VARCHAR(100) - (cin ou lieu)"
                 elif "varying(20)" in e_msg: col_suspecte = "VARCHAR(20) - (sexe)"
                 print(f"❌ [ETUDIANT] Ligne Excel {row.name} ({code_etudiant}) - ERREUR: Valeur trop longue (TRONCATION sur {col_suspecte})")
                 logging.error(f"ETUDIANT: {code_etudiant} | ERREUR TRONCATION sur {col_suspecte} | Détail: {e_msg} | LIGNE_EXCEL_IDX: {row.name}")
            else:
                 print(f"❌ [ETUDIANT] Ligne Excel {row.name} ({code_etudiant}) - ERREUR: {e_msg}")
                 logging.error(f"ETUDIANT: {code_etudiant} | Erreur: {e_msg} | LIGNE_EXCEL_IDX: {row.name}")
             
    print(f"\n✅ Insertion des étudiants terminée. {etudiant_errors} erreur(s) individuelle(s) détectée(s).")


def _import_inscriptions(session: Session, df: pd.DataFrame):
    """Importe les Inscriptions avec gestion d'erreurs (commit par lot)."""
    print("\n--- Importation des Inscriptions ---")
    
    cles_requises = ['code_inscription', 'code_etudiant', 'annee_universitaire', 'id_parcours', 'niveau']
    df_inscriptions = df.dropna(subset=cles_requises)
    
    errors_fk, errors_uq, errors_data, errors_other = 0, 0, 0, 0
    
    for index, row in tqdm(df_inscriptions.iterrows(), total=len(df_inscriptions), desc="Import Inscriptions"):
        code_inscription = row.get('code_inscription', 'N/A')
        
        try:
            session.merge(Inscription(
                code_inscription=safe_string(code_inscription), 
                code_etudiant=safe_string(row['code_etudiant']), 
                annee_universitaire=safe_string(row['annee_universitaire']), 
                id_parcours=row['id_parcours'], 
                niveau=safe_string(row['niveau']), 
                formation=safe_string(row.get('formation'))
            ))
            
            if (index + 1) % 500 == 0:
                session.commit()
                
        # Gestion des erreurs (inchangée, mais dans une fonction dédiée)
        except IntegrityError as e:
            session.rollback()
            e_msg = str(e.orig).lower()
            if "violates foreign key constraint" in e_msg: errors_fk += 1
            elif "violates unique constraint" in e_msg: errors_uq += 1
            else: errors_other += 1
            
            logging.error(f"INSCRIPTION (Intégrité): {code_inscription} | Détail: {e.orig} | LIGNE_EXCEL_IDX: {row.name}")
        except DataError as e:
            session.rollback()
            errors_data += 1
            logging.error(f"INSCRIPTION (Données): {code_inscription} | Détail: {e.orig} | LIGNE_EXCEL_IDX: {row.name}")
        except Exception as e:
            session.rollback()
            errors_other += 1
            logging.error(f"INSCRIPTION (Autre): {code_inscription} | Erreur: {e} | LIGNE_EXCEL_IDX: {row.name}")
    
    # Commit final et affichage du récapitulatif
    try:
        session.commit()
        print("\n✅ Importation des inscriptions terminée.")
        print(f"\n--- Récapitulatif des erreurs d'insertion ---")
        print(f"Erreurs Clé Étrangère (FK): {errors_fk}")
        print(f"Erreurs Contrainte Unique (UQ): {errors_uq}")
        print(f"Erreurs Format de Données: {errors_data}")
        print(f"Autres erreurs: {errors_other}")
        print(f"Voir 'import_errors.log' pour les détails complets.")
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERREUR CRITIQUE PENDANT LE COMMIT FINAL: {e}", file=sys.stderr)


# ----------------------------------------------------------------------
# FONCTION ORCHESTRATRICE DES INSCRIPTIONS
# ----------------------------------------------------------------------

def import_inscriptions_to_db():
    """
    Orchestre l'importation des données des étudiants et des inscriptions.
    """
    print(f"\n--- 3. Démarrage de l'importation des inscriptions et étudiants ---")
    
    df_inscriptions = _load_and_clean_inscriptions()
    if df_inscriptions is None:
        return
        
    session = database_setup.get_session()
    
    try:
        # 1. Années Universitaires (prérequis pour Inscription)
        _import_annees_universitaires(session, df_inscriptions)

        # 2. Étudiants
        _import_etudiants(session, df_inscriptions)

        # 3. Inscriptions (dépend de Etudiant, AnneeUniversitaire, Parcours)
        _import_inscriptions(session, df_inscriptions)

    finally:
        session.close()


# ----------------------------------------------------------------------
# BLOC PRINCIPAL
# ----------------------------------------------------------------------

if __name__ == '__main__':
    # Exemple d'appel des fonctions orchestratrices
    import_metadata_to_db()
    import_inscriptions_to_db()

    # À ce stade, vous pourriez appeler import_pedagogie_to_db() si vous l'ajoutez