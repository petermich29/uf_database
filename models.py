# models.py (Mis à jour pour inclure la table Institution)

from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, 
    UniqueConstraint, Text 
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Définition de la base déclarative pour SQLAlchemy
Base = declarative_base()


# -------------------------------------------------------------------
# --- NOUVELLE TABLE DE RÉFÉRENCE: INSTITUTION ----------------------
# -------------------------------------------------------------------

class Institution(Base):
    __tablename__ = 'institutions'
    __table_args__ = {'extend_existing': True}
    
    # Clé Primaire : Identifiant unique de l'institution
    id_institution = Column(String(32), primary_key=True) 
    
    # Nom de l'institution (Ex: Université de Fianarantsoa)
    nom = Column(String(255), nullable=False, unique=True)
    
    # Type : 'Public' ou 'Privé'
    type_institution = Column(String(10), nullable=False)
    
    # Champ de description libre
    description = Column(Text, nullable=True)
    
    # Relation : Une institution peut avoir plusieurs composantes
    composantes = relationship("Composante", back_populates="institution")
    
    # Remarque : Les champs de métadonnées (date_creation) ont été omis pour coller 
    # au style des autres tables du fichier (simplicité).


# -------------------------------------------------------------------
# --- TABLES DE RÉFÉRENCE (MÉTA-DONNÉES ACADÉMIQUES) ---
# -------------------------------------------------------------------

class Composante(Base):
    __tablename__ = 'composantes'
    __table_args__ = {'extend_existing': True}
    
    code = Column(String(10), primary_key=True)
    label = Column(String(100))
    description = Column(Text, nullable=True) 
    
    # NOUVELLE CLÉ ÉTRANGÈRE vers l'Institution
    id_institution = Column(String(32), ForeignKey('institutions.id_institution'), nullable=True) 
    
    # NOUVELLE RELATION vers l'Institution
    institution = relationship("Institution", back_populates="composantes")
    
    mentions = relationship("Mention", backref="composante")


class Domaine(Base):
    __tablename__ = 'domaines'
    __table_args__ = {'extend_existing': True}
    
    code = Column(String(10), primary_key=True)
    label = Column(String(100))
    description = Column(Text, nullable=True) 
    
    mentions = relationship("Mention", backref="domaine")


class Mention(Base):
    __tablename__ = 'mentions'
    __table_args__ = {'extend_existing': True} 
    
    id_mention = Column(String(50), primary_key=True) 
    
    code_mention = Column(String(20))
    label = Column(String(100))
    description = Column(Text, nullable=True) 
    
    composante_code = Column(String(10), ForeignKey('composantes.code'))
    domaine_code = Column(String(10), ForeignKey('domaines.code'))
    
    parcours = relationship("Parcours", backref="mention")


class Parcours(Base):
    __tablename__ = 'parcours'
    __table_args__ = {'extend_existing': True}
    
    id_parcours = Column(String(50), primary_key=True)
    code_parcours = Column(String(20))
    label = Column(String(100))
    description = Column(Text, nullable=True) 
    
    mention_id = Column(String(50), ForeignKey('mentions.id_mention'))
    
    date_creation = Column(Integer, nullable=True)
    date_fin = Column(Integer, nullable=True)


class AnneeUniversitaire(Base):
    __tablename__ = 'annees_universitaires'
    __table_args__ = {'extend_existing': True} 
    
    annee = Column(String(9), primary_key=True)
    description = Column(Text, nullable=True) 
    
    inscriptions = relationship("Inscription", backref="annee_univ")


# -------------------------------------------------------------------
# --- TABLES DE DONNÉES ÉTUDIANT ET INSCRIPTION (INCHANGÉES) ---
# -------------------------------------------------------------------

class Etudiant(Base):
    __tablename__ = 'etudiants'
    
    # Clé Primaire
    code_etudiant = Column(String(50), primary_key=True) 

    # Informations de base
    numero_inscription = Column(String(50)) 
    nom = Column(String(100))
    prenoms = Column(String(150))
    sexe = Column(String(20)) 

    # État Civil
    naissance_date = Column(Date, nullable=True)
    naissance_lieu = Column(String(100))
    nationalite = Column(String(50))
    
    # Baccalauréat 
    bacc_annee = Column(Integer, nullable=True)
    bacc_serie = Column(String(50)) 
    bacc_centre = Column(String(100))
    
    # Contact
    adresse = Column(String(255))
    telephone = Column(String(50))
    mail = Column(String(100))
    
    # CIN 
    cin = Column(String(100))
    cin_date = Column(Date, nullable=True)
    cin_lieu = Column(String(100))

    inscriptions = relationship("Inscription", backref="etudiant")


class Inscription(Base):
    __tablename__ = 'inscriptions'
    
    code_inscription = Column(String(50), primary_key=True)
    
    # Clés étrangères
    code_etudiant = Column(String(50), ForeignKey('etudiants.code_etudiant'))
    annee_universitaire = Column(String(9), ForeignKey('annees_universitaires.annee'))
    id_parcours = Column(String(50), ForeignKey('parcours.id_parcours'))
    
    niveau = Column(String(20))
    formation = Column(String(20), nullable=True)
    
    # Contrainte d'unicité pour les inscriptions
    __table_args__ = (
        UniqueConstraint(
            'code_etudiant', 
            'annee_universitaire', 
            'id_parcours', 
            'niveau',  
            name='uq_etudiant_annee_parcours_niveau' 
        ),
    )