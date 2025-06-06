# models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class HistoriqueStatut(BaseModel):
    statut: str
    date: datetime.datetime
    par: str
    commentaire: Optional[str] = ""

class Remboursement(BaseModel):
    id_demande: str
    nom: Optional[str] = None
    prenom: Optional[str] = None
    reference_facture: str
    reference_facture_dossier: str
    description: str
    montant_demande: float
    chemins_factures_stockees: List[str] = Field(default_factory=list)
    chemins_rib_stockes: List[str] = Field(default_factory=list)
    statut: str
    cree_par: str
    date_creation: datetime.datetime
    derniere_modification_par: str
    date_derniere_modification: datetime.datetime
    historique_statuts: List[HistoriqueStatut] = Field(default_factory=list)
    pieces_capture_trop_percu: List[str] = Field(default_factory=list)
    preuve_paiement_banque: Optional[str] = None
    date_paiement_effectue: Optional[datetime.datetime] = None

    class Config:
        str_strip_whitespace = True