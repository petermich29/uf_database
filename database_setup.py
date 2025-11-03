# database_setup.py

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

import config
from models import Base

# --- Initialisation du moteur et de la session ---

# Moteur pour la BDD cible
try:
    engine = create_engine(config.DATABASE_URL) 
    # Moteur pour la BDD par défaut (pour la création)
    default_engine = create_engine(config.DEFAULT_DB_URL) 
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"❌ ERREUR CRITIQUE: Impossible de créer les moteurs de connexion. {e}")
    sys.exit(1)


def get_session():
    """Fournit une nouvelle session de base de données."""
    return SessionLocal()


def init_db():
    """Crée la base de données et les tables si elles n'existent pas."""
    print("--- 1. Initialisation de la Base de Données ---")
    
    # 1. Création de la BDD si elle n'existe pas
    if not database_exists(default_engine.url):
        print(f"Création de la base de données '{config.DB_NAME}'...")
        try:
            create_database(default_engine.url)
            print("Base de données créée avec succès.")
        except Exception as e:
            print(f"❌ ERREUR: Impossible de créer la BDD. Détail: {e}")
            sys.exit(1)
    else:
        print(f"La base de données '{config.DB_NAME}' existe déjà.")
        
    # 2. Création des tables
    print("Création des tables (si elles n'existent pas)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables créées/vérifiées.")
    except Exception as e:
        print(f"❌ ERREUR: Impossible de créer les tables. Détail: {e}")
        sys.exit(1)