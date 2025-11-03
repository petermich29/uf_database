# models.py

from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, 
    UniqueConstraint 
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Définition de la base déclarative pour SQLAlchemy
Base = declarative_base()


# --- TABLES DE RÉFÉRENCE (MÉTA-DONNÉES ACADÉMIQUES) ---

class Composante(Base):
    __tablename__ = 'composantes'
    __table_args__ = {'extend_existing': True}
    
    code = Column(String(10), primary_key=True)
    label = Column(String(100))
    
    mentions = relationship("Mention", backref="composante")


class Domaine(Base):
    __tablename__ = 'domaines'
    __table_args__ = {'extend_existing': True}
    
    code = Column(String(10), primary_key=True)
    label = Column(String(100))
    
    mentions = relationship("Mention", backref="domaine")


class Mention(Base):
    __tablename__ = 'mentions'
    __table_args__ = {'extend_existing': True} 
    
    id_mention = Column(String(50), primary_key=True) 
    
    code_mention = Column(String(20))
    label = Column(String(100))
    
    composante_code = Column(String(10), ForeignKey('composantes.code'))
    domaine_code = Column(String(10), ForeignKey('domaines.code'))
    
    parcours = relationship("Parcours", backref="mention")


class Parcours(Base):
    __tablename__ = 'parcours'
    __table_args__ = {'extend_existing': True}
    
    id_parcours = Column(String(50), primary_key=True)
    code_parcours = Column(String(20))
    label = Column(String(100))
    
    mention_id = Column(String(50), ForeignKey('mentions.id_mention'))
    
    date_creation = Column(Integer, nullable=True)
    date_fin = Column(Integer, nullable=True)


class AnneeUniversitaire(Base):
    __tablename__ = 'annees_universitaires'
    __table_args__ = {'extend_existing': True} 
    
    annee = Column(String(9), primary_key=True)
    inscriptions = relationship("Inscription", backref="annee_univ")


# --- TABLES DE DONNÉES ÉTUDIANT ET INSCRIPTION ---

class Etudiant(Base):
    __tablename__ = 'etudiants'
    
    # Clé Primaire
    code_etudiant = Column(String(50), primary_key=True) 

    # Informations de base
    numero_inscription = Column(String(50)) 
    nom = Column(String(100))
    prenoms = Column(String(150))
    # Taille ajustée après les erreurs de troncation
    sexe = Column(String(20)) 

    # État Civil
    naissance_date = Column(Date, nullable=True)
    naissance_lieu = Column(String(100))
    nationalite = Column(String(50))
    
    # Baccalauréat 
    bacc_annee = Column(Integer, nullable=True)
    # Taille ajustée pour accepter les chaînes longues (ex: 'sciences eco et sociales,maths')
    bacc_serie = Column(String(50)) 
    bacc_centre = Column(String(100))
    
    # Contact
    adresse = Column(String(255))
    telephone = Column(String(50))
    mail = Column(String(100))
    
    # CIN 
    # Taille ajustée pour accepter le numéro + date + lieu de délivrance
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
    # Garantit qu'un étudiant n'a qu'une seule inscription pour un contexte donné
    __table_args__ = (
        UniqueConstraint(
            'code_etudiant', 
            'annee_universitaire', 
            'id_parcours', 
            'niveau',  
            name='uq_etudiant_annee_parcours_niveau' 
        ),
    )