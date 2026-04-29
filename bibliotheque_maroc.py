#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 Système de Gestion de Bibliothèque Publique - Maroc
Application console pour gérer les livres, les adhérents et les emprunts
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

# ==================== CLASSES MODÈLES ====================

class Livre:
    """Classe représentant un livre dans la bibliothèque"""
    
    def __init__(self, id_livre: int, titre: str, auteur: str, isbn: str, 
                 annee: int, categorie: str, quantite: int = 1):
        self.id_livre = id_livre
        self.titre = titre
        self.auteur = auteur
        self.isbn = isbn
        self.annee = annee
        self.categorie = categorie
        self.quantite_totale = quantite
        self.quantite_disponible = quantite
    
    def to_dict(self) -> dict:
        return {
            'id_livre': self.id_livre,
            'titre': self.titre,
            'auteur': self.auteur,
            'isbn': self.isbn,
            'annee': self.annee,
            'categorie': self.categorie,
            'quantite_totale': self.quantite_totale,
            'quantite_disponible': self.quantite_disponible
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        livre = cls(
            data['id_livre'],
            data['titre'],
            data['auteur'],
            data['isbn'],
            data['annee'],
            data['categorie'],
            data['quantite_totale']
        )
        livre.quantite_disponible = data['quantite_disponible']
        return livre


class Adherent:
    """Classe représentant un adhérent de la bibliothèque"""
    
    TARIFS = {
        'etudiant': 50,
        'enseignant': 100,
        'public': 150,
        'famille': 250
    }
    
    def __init__(self, id_adherent: int, nom: str, email: str, telephone: str,
                 ville: str, type_adh: str, date_inscription: str = None):
        self.id_adherent = id_adherent
        self.nom = nom
        self.email = email
        self.telephone = telephone
        self.ville = ville
        self.type_adh = type_adh
        self.date_inscription = date_inscription or datetime.now().strftime('%Y-%m-%d')
        self.emprunts_actifs: List[int] = []  # IDs des livres empruntés
        self.historique: List[dict] = []
    
    def to_dict(self) -> dict:
        return {
            'id_adherent': self.id_adherent,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone,
            'ville': self.ville,
            'type_adh': self.type_adh,
            'date_inscription': self.date_inscription,
            'emprunts_actifs': self.emprunts_actifs,
            'historique': self.historique
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        adherent = cls(
            data['id_adherent'],
            data['nom'],
            data['email'],
            data['telephone'],
            data['ville'],
            data['type_adh'],
            data['date_inscription']
        )
        adherent.emprunts_actifs = data['emprunts_actifs']
        adherent.historique = data['historique']
        return adherent


class Emprunt:
    """Classe pour gérer les emprunts"""
    
    DUREE_PRET_JOURS = 21  # 3 semaines
    
    def __init__(self, id_emprunt: int, id_adherent: int, id_livre: int,
                 date_emprunt: str = None, date_retour_prevue: str = None):
        self.id_emprunt = id_emprunt
        self.id_adherent = id_adherent
        self.id_livre = id_livre
        self.date_emprunt = date_emprunt or datetime.now().strftime('%Y-%m-%d')
        
        if date_retour_prevue:
            self.date_retour_prevue = date_retour_prevue
        else:
            date_fin = datetime.now() + timedelta(days=self.DUREE_PRET_JOURS)
            self.date_retour_prevue = date_fin.strftime('%Y-%m-%d')
        
        self.date_retour_effectif = None
        self.amende = 0
    
    def to_dict(self) -> dict:
        return {
            'id_emprunt': self.id_emprunt,
            'id_adherent': self.id_adherent,
            'id_livre': self.id_livre,
            'date_emprunt': self.date_emprunt,
            'date_retour_prevue': self.date_retour_prevue,
            'date_retour_effectif': self.date_retour_effectif,
            'amende': self.amende
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        emp = cls(
            data['id_emprunt'],
            data['id_adherent'],
            data['id_livre'],
            data['date_emprunt'],
            data['date_retour_prevue']
        )
        emp.date_retour_effectif = data['date_retour_effectif']
        emp.amende = data['amende']
        return emp
    
    def calculer_amende(self) -> float:
        """Calcule l'amende en cas de retard (2 DH par jour de retard)"""
        if self.date_retour_effectif:
            return self.amende
        
        date_prevue = datetime.strptime(self.date_retour_prevue, '%Y-%m-%d')
        aujourdhui = datetime.now()
        
        if aujourdhui > date_prevue:
            jours_retard = (aujourdhui - date_prevue).days
            return jours_retard * 2
        return 0


# ==================== BIBLIOTHÈQUE ====================

class Bibliotheque:
    """Classe principale de gestion de la bibliothèque"""
    
    def __init__(self, nom: str, ville: str):
        self.nom = nom
        self.ville = ville
        self.livres: Dict[int, Livre] = {}
        self.adherents: Dict[int, Adherent] = {}
        self.emprunts: Dict[int, Emprunt] = {}
        self.prochain_id_livre = 1
        self.prochain_id_adherent = 1
        self.prochain_id_emprunt = 1
        
        self.charger_donnees()
    
    # ========== GESTION DES FICHIERS ==========
    
    def sauvegarder_donnees(self):
        """Sauvegarde toutes les données dans des fichiers JSON"""
        data = {
            'livres': {k: v.to_dict() for k, v in self.livres.items()},
            'adherents': {k: v.to_dict() for k, v in self.adherents.items()},
            'emprunts': {k: v.to_dict() for k, v in self.emprunts.items()},
            'meta': {
                'prochain_id_livre': self.prochain_id_livre,
                'prochain_id_adherent': self.prochain_id_adherent,
                'prochain_id_emprunt': self.prochain_id_emprunt
            }
        }
        
        with open('bibliotheque_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def charger_donnees(self):
        """Charge les données depuis les fichiers JSON"""
        if not os.path.exists('bibliotheque_data.json'):
            self.initialiser_donnees_test()
            return
        
        try:
            with open('bibliotheque_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.livres = {int(k): Livre.from_dict(v) for k, v in data['livres'].items()}
            self.adherents = {int(k): Adherent.from_dict(v) for k, v in data['adherents'].items()}
            self.emprunts = {int(k): Emprunt.from_dict(v) for k, v in data['emprunts'].items()}
            
            meta = data.get('meta', {})
            self.prochain_id_livre = meta.get('prochain_id_livre', max(self.livres.keys(), default=0) + 1)
            self.prochain_id_adherent = meta.get('prochain_id_adherent', max(self.adherents.keys(), default=0) + 1)
            self.prochain_id_emprunt = meta.get('prochain_id_emprunt', max(self.emprunts.keys(), default=0) + 1)
            
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement : {e}")
            self.initialiser_donnees_test()
    
    def initialiser_donnees_test(self):
        """Initialise des données de test inspirées de la culture marocaine"""
        
        # Livres marocains et internationaux
        livres_test = [
            (1, "Le Chardon et le Tartin", "Tahar Ben Jelloun", "978-2-070-12345-6", 2021, "Littérature marocaine", 3),
            (2, "La Nuit sacrée", "Tahar Ben Jelloun", "978-2-020-12345-7", 1987, "Littérature marocaine", 2),
            (3, "Harraga", "Boubacar Boris Diop", "978-2-757-81234-5", 2019, "Littérature africaine", 2),
            (4, "L'Étranger", "Albert Camus", "978-2-070-54321-0", 1942, "Classique", 5),
            (5, "Les Nuits de Strasbourg", "Assia Djebar", "978-2-020-98765-4", 2018, "Roman", 1),
            (6, "Le Maroc des écrivains", "Collectif", "978-995-4-12345-6", 2020, "Essai", 2),
            (7, "Dictionnaire des arts de l'Islam", "BNRM", "978-995-4-98765-4", 2019, "Patrimoine", 1),
            (8, "Contes des mille et une nuits", "Anonyme", "978-2-070-11111-1", 2015, "Jeunesse", 4),
        ]
        
        for livre in livres_test:
            self.livres[livre[0]] = Livre(*livre)
            self.prochain_id_livre = max(self.prochain_id_livre, livre[0] + 1)
        
        # Adhérents test
        adherents_test = [
            (1, "Ahmed Alaoui", "ahmed@email.ma", "0612345678", "Rabat", "public"),
            (2, "Fatima Zahra", "fatima@email.ma", "0612345679", "Casablanca", "etudiant"),
            (3, "Youssef Benali", "youssef@email.ma", "0612345680", "Fès", "enseignant"),
        ]
        
        for adherent in adherents_test:
            self.adherents[adherent[0]] = Adherent(*adherent)
            self.prochain_id_adherent = max(self.prochain_id_adherent, adherent[0] + 1)
    
    # ========== GESTION DES LIVRES ==========
    
    def ajouter_livre(self, titre: str, auteur: str, isbn: str, annee: int, categorie: str, quantite: int = 1):
        """Ajoute un nouveau livre au catalogue"""
        livre = Livre(self.prochain_id_livre, titre, auteur, isbn, annee, categorie, quantite)
        self.livres[self.prochain_id_livre] = livre
        self.prochain_id_livre += 1
        self.sauvegarder_donnees()
        print(f"✅ Livre '{titre}' ajouté avec succès !")
        return livre
    
    def rechercher_livres(self, critere: str, valeur: str) -> List[Livre]:
        """Recherche des livres par critère (titre, auteur, categorie)"""
        resultats = []
        valeur = valeur.lower()
        
        for livre in self.livres.values():
            if critere == 'titre' and valeur in livre.titre.lower():
                resultats.append(livre)
            elif critere == 'auteur' and valeur in livre.auteur.lower():
                resultats.append(livre)
            elif critere == 'categorie' and valeur in livre.categorie.lower():
                resultats.append(livre)
            elif critere == 'tous':
                if (valeur in livre.titre.lower() or 
                    valeur in livre.auteur.lower() or 
                    valeur in livre.categorie.lower()):
                    resultats.append(livre)
        
        return resultats
    
    def afficher_catalogue(self):
        """Affiche tout le catalogue des livres"""
        if not self.livres:
            print("📭 Le catalogue est vide.")
            return
        
        print("\n" + "="*70)
        print(f"📚 CATALOGUE DE LA BIBLIOTHÈQUE - {self.nom} - {self.ville}")
        print("="*70)
        
        for livre in self.livres.values():
            statut = "✅ Disponible" if livre.quantite_disponible > 0 else "❌ Indisponible"
            print(f"\n📖 [{livre.id_livre}] {livre.titre}")
            print(f"   ✍️  Auteur: {livre.auteur}")
            print(f"   📅 Année: {livre.annee} | 📚 Catégorie: {livre.categorie}")
            print(f"   📊 Disponible: {livre.quantite_disponible}/{livre.quantite_totale} | {statut}")
    
    # ========== GESTION DES ADHÉRENTS ==========
    
    def inscrire_adherent(self, nom: str, email: str, telephone: str, ville: str, type_adh: str) -> Adherent:
        """Inscrit un nouvel adhérent"""
        if type_adh not in Adherent.TARIFS:
            type_adh = 'public'
        
        adherent = Adherent(self.prochain_id_adherent, nom, email, telephone, ville, type_adh)
        self.adherents[self.prochain_id_adherent] = adherent
        self.prochain_id_adherent += 1
        self.sauvegarder_donnees()
        
        print(f"\n🎉 Inscription réussie !")
        print(f"   ID Adhérent: {adherent.id_adherent}")
        print(f"   Tarif: {Adherent.TARIFS[type_adh]} DH/an")
        return adherent
    
    def afficher_adherents(self):
        """Affiche la liste des adhérents"""
        if not self.adherents:
            print("📭 Aucun adhérent inscrit.")
            return
        
        print("\n" + "="*60)
        print("👥 LISTE DES ADHÉRENTS")
        print("="*60)
        
        for adherent in self.adherents.values():
            print(f"\n🆔 [{adherent.id_adherent}] {adherent.nom}")
            print(f"   📧 {adherent.email} | 📞 {adherent.telephone}")
            print(f"   📍 {adherent.ville} | 🎫 {adherent.type_adh}")
            print(f"   📅 Inscrit le: {adherent.date_inscription}")
            print(f"   📚 Emprunts actifs: {len(adherent.emprunts_actifs)}")
    
    # ========== GESTION DES EMPRUNTS ==========
    
    def emprunter_livre(self, id_adherent: int, id_livre: int) -> bool:
        """Permet à un adhérent d'emprunter un livre"""
        
        # Vérifications
        if id_adherent not in self.adherents:
            print("❌ Adhérent non trouvé.")
            return False
        
        if id_livre not in self.livres:
            print("❌ Livre non trouvé.")
            return False
        
        adherent = self.adherents[id_adherent]
        livre = self.livres[id_livre]
        
        if livre.quantite_disponible <= 0:
            print("❌ Ce livre n'est plus disponible.")
            return False
        
        if len(adherent.emprunts_actifs) >= 5:
            print("❌ Vous avez atteint la limite de 5 emprunts simultanés.")
            return False
        
        # Création de l'emprunt
        emprunt = Emprunt(self.prochain_id_emprunt, id_adherent, id_livre)
        self.emprunts[self.prochain_id_emprunt] = emprunt
        self.prochain_id_emprunt += 1
        
        # Mise à jour des données
        livre.quantite_disponible -= 1
        adherent.emprunts_actifs.append(id_livre)
        adherent.historique.append({
            'id_livre': id_livre,
            'titre': livre.titre,
            'date_emprunt': emprunt.date_emprunt,
            'date_retour_prevue': emprunt.date_retour_prevue
        })
        
        self.sauvegarder_donnees()
        
        print(f"\n✅ Emprunt effectué avec succès !")
        print(f"   Livre: {livre.titre}")
        print(f"   Date de retour prévue: {emprunt.date_retour_prevue}")
        return True
    
    def retourner_livre(self, id_adherent: int, id_livre: int) -> bool:
        """Gestions des retours de livres et amendes"""
        
        if id_adherent not in self.adherents:
            print("❌ Adhérent non trouvé.")
            return False
        
        adherent = self.adherents[id_adherent]
        
        if id_livre not in adherent.emprunts_actifs:
            print("❌ Ce livre n'est pas emprunté par cet adhérent.")
            return False
        
        # Recherche de l'emprunt actif
        emprunt_actif = None
        for emp in self.emprunts.values():
            if (emp.id_adherent == id_adherent and 
                emp.id_livre == id_livre and 
                emp.date_retour_effectif is None):
                emprunt_actif = emp
                break
        
        if not emprunt_actif:
            print("❌ Emprunt non trouvé.")
            return False
        
        # Calcul de l'amende
        amende = emprunt_actif.calculer_amende()
        emprunt_actif.date_retour_effectif = datetime.now().strftime('%Y-%m-%d')
        emprunt_actif.amende = amende
        
        # Mise à jour
        livre = self.livres[id_livre]
        livre.quantite_disponible += 1
        adherent.emprunts_actifs.remove(id_livre)
        
        self.sauvegarder_donnees()
        
        print(f"\n📚 Retour effectué pour : {livre.titre}")
        if amende > 0:
            print(f"⚠️  Retard de {int(amende/2)} jours - Amende: {amende} DH")
        else:
            print("✅ Pas d'amende, retour dans les délais.")
        
        return True
    
    def afficher_emprunts_actifs(self):
        """Affiche tous les emprunts en cours"""
        emprunts_actifs = [e for e in self.emprunts.values() if e.date_retour_effectif is None]
        
        if not emprunts_actifs:
            print("📭 Aucun emprunt actif.")
            return
        
        print("\n" + "="*70)
        print("📋 EMPRUNTS EN COURS")
        print("="*70)
        
        for emp in emprunts_actifs:
            adherent = self.adherents.get(emp.id_adherent)
            livre = self.livres.get(emp.id_livre)
            amende = emp.calculer_amende()
            
            if adherent and livre:
                print(f"\n📚 {livre.titre}")
                print(f"   👤 Emprunté par: {adherent.nom}")
                print(f"   📅 Date retour prévue: {emp.date_retour_prevue}")
                if amende > 0:
                    print(f"   ⚠️  Amende potentielle: {amende} DH")


# ==================== INTERFACE CONSOLE ====================

def afficher_menu_principal():
    """Affiche le menu principal"""
    print("\n" + "="*50)
    print("📚 BIBLIOTHÈQUE PUBLIQUE DU MAROC")
    print("="*50)
    print("1. 📖 Gestion des livres")
    print("2. 👥 Gestion des adhérents")
    print("3. 🔄 Emprunts et retours")
    print("4. 📊 Consultation")
    print("5. ℹ️  Informations")
    print("0. 🚪 Quitter")
    print("-"*50)

def menu_livres(biblio: Bibliotheque):
    """Sous-menu pour la gestion des livres"""
    while True:
        print("\n" + "="*40)
        print("📖 GESTION DES LIVRES")
        print("="*40)
        print("1. Afficher le catalogue")
        print("2. Rechercher un livre")
        print("3. Ajouter un livre")
        print("0. Retour")
        
        choix = input("\nVotre choix: ")
        
        if choix == '1':
            biblio.afficher_catalogue()
        
        elif choix == '2':
            print("\nRechercher par:")
            print("1. Titre")
            print("2. Auteur")
            print("3. Catégorie")
            print("4. Tous (recherche globale)")
            crit_choix = input("Choix: ")
            
            crit_map = {'1': 'titre', '2': 'auteur', '3': 'categorie', '4': 'tous'}
            critere = crit_map.get(crit_choix, 'tous')
            
            valeur = input("Terme de recherche: ")
            resultats = biblio.rechercher_livres(critere, valeur)
            
            if resultats:
                print(f"\n🔍 {len(resultats)} résultat(s) trouvé(s):")
                for livre in resultats:
                    print(f"   [{livre.id_livre}] {livre.titre} - {livre.auteur} ({livre.annee})")
            else:
                print("❌ Aucun résultat trouvé.")
        
        elif choix == '3':
            print("\n➕ Ajout d'un nouveau livre:")
            titre = input("Titre: ")
            auteur = input("Auteur: ")
            isbn = input("ISBN: ")
            annee = int(input("Année: "))
            categorie = input("Catégorie: ")
            quantite = int(input("Quantité: "))
            
            biblio.ajouter_livre(titre, auteur, isbn, annee, categorie, quantite)
        
        elif choix == '0':
            break

def menu_adherents(biblio: Bibliotheque):
    """Sous-menu pour la gestion des adhérents"""
    while True:
        print("\n" + "="*40)
        print("👥 GESTION DES ADHÉRENTS")
        print("="*40)
        print("1. Afficher tous les adhérents")
        print("2. Inscrire un nouvel adhérent")
        print("0. Retour")
        
        choix = input("\nVotre choix: ")
        
        if choix == '1':
            biblio.afficher_adherents()
        
        elif choix == '2':
            print("\n📝 Inscription d'un nouvel adhérent:")
            nom = input("Nom complet: ")
            email = input("Email: ")
            telephone = input("Téléphone: ")
            ville = input("Ville: ")
            
            print("\nType d'adhésion:")
            print("1. Étudiant (50 DH/an)")
            print("2. Enseignant (100 DH/an)")
            print("3. Public (150 DH/an)")
            print("4. Famille (250 DH/an)")
            
            type_choix = input("Choix (1-4): ")
            type_map = {'1': 'etudiant', '2': 'enseignant', '3': 'public', '4': 'famille'}
            type_adh = type_map.get(type_choix, 'public')
            
            biblio.inscrire_adherent(nom, email, telephone, ville, type_adh)
        
        elif choix == '0':
            break

def menu_emprunts(biblio: Bibliotheque):
    """Sous-menu pour les emprunts et retours"""
    while True:
        print("\n" + "="*40)
        print("🔄 EMPRUNTS ET RETOURS")
        print("="*40)
        print("1. Emprunter un livre")
        print("2. Retourner un livre")
        print("3. Voir les emprunts en cours")
        print("4. Voir mes emprunts (par ID adhérent)")
        print("0. Retour")
        
        choix = input("\nVotre choix: ")
        
        if choix == '1':
            print("\n📥 Emprunter un livre:")
            id_adh = int(input("ID Adhérent: "))
            id_livre = int(input("ID Livre: "))
            biblio.emprunter_livre(id_adh, id_livre)
        
        elif choix == '2':
            print("\n📤 Retourner un livre:")
            id_adh = int(input("ID Adhérent: "))
            id_livre = int(input("ID Livre: "))
            biblio.retourner_livre(id_adh, id_livre)
        
        elif choix == '3':
            biblio.afficher_emprunts_actifs()
        
        elif choix == '4':
            id_adh = int(input("ID Adhérent: "))
            if id_adh in biblio.adherents:
                adherent = biblio.adherents[id_adh]
                if adherent.emprunts_actifs:
                    print(f"\n📚 Emprunts de {adherent.nom}:")
                    for id_livre in adherent.emprunts_actifs:
                        livre = biblio.livres.get(id_livre)
                        if livre:
                            print(f"   - {livre.titre}")
                else:
                    print("📭 Aucun emprunt actif.")
            else:
                print("❌ Adhérent non trouvé.")
        
        elif choix == '0':
            break

def menu_consultation(biblio: Bibliotheque):
    """Sous-menu pour les consultations diverses"""
    while True:
        print("\n" + "="*40)
        print("📊 CONSULTATION")
        print("="*40)
        print("1. Statistiques générales")
        print("2. Livres les plus populaires (simulation)")
        print("3. Chiffres par catégorie")
        print("0. Retour")
        
        choix = input("\nVotre choix: ")
        
        if choix == '1':
            print("\n📊 STATISTIQUES DE LA BIBLIOTHÈQUE")
            print("-"*40)
            print(f"📍 {biblio.nom} - {biblio.ville}")
            print(f"📚 Nombre total de livres: {len(biblio.livres)}")
            print(f"📖 Exemplaires disponibles: {sum(l.quantite_disponible for l in biblio.livres.values())}")
            print(f"👥 Nombre d'adhérents: {len(biblio.adherents)}")
            print(f"🔄 Emprunts actifs: {sum(1 for e in biblio.emprunts.values() if e.date_retour_effectif is None)}")
        
        elif choix == '2':
            print("\n🏆 Top des livres les plus empruntés (données simulées)")
            print("   1. Le Chardon et le Tartin - Tahar Ben Jelloun")
            print("   2. Harraga - Boubacar Boris Diop")
            print("   3. La Nuit sacrée - Tahar Ben Jelloun")
        
        elif choix == '3':
            categories = {}
            for livre in biblio.livres.values():
                if livre.categorie not in categories:
                    categories[livre.categorie] = 0
                categories[livre.categorie] += livre.quantite_totale
            
            print("\n📊 RÉPARTITION PAR CATÉGORIE")
            for cat, nb in sorted(categories.items()):
                print(f"   {cat}: {nb} exemplaires")
        
        elif choix == '0':
            break

def afficher_infos():
    """Affiche les informations sur la bibliothèque et ses horaires"""
    print("\n" + "="*50)
    print("ℹ️  BIBLIOTHÈQUE NATIONALE DU ROYAUME DU MAROC")
    print("="*50)
    print("\n📍 Adresse: Avenue Ibn Khaldoun, Agdal, Rabat")
    print("📞 Téléphone: 05 37 27 23 00")
    print("\n⏰ HORAIRES D'OUVERTURE:")
    print("   Lundi - Vendredi: 09h00 - 19h00")
    print("   Samedi: 10h00 - 16h00")
    print("   Dimanche: Fermé")
    print("\n📅 Horaires Ramadan:")
    print("   Lundi - Vendredi: 09h00 - 16h30")
    print("   Samedi: 10h00 - 14h00")
    print("\n🎫 TARIFS ADHÉSION (par an):")
    print("   Étudiant: 50 DH")
    print("   Enseignant: 100 DH")
    print("   Public général: 150 DH")
    print("   Famille: 250 DH")
    print("\n💰 Amendes: 2 DH par jour de retard")

# ==================== MAIN ====================

def main():
    """Fonction principale du programme"""
    
    print("\n" + "="*60)
    print("📚 BIENVENUE À LA BIBLIOTHÈQUE PUBLIQUE DU MAROC")
    print("="*60)
    
    # Création de la bibliothèque
    biblio = Bibliotheque("Bibliothèque Nationale du Maroc", "Rabat")
    
    while True:
        afficher_menu_principal()
        choix = input("\nVotre choix: ")
        
        if choix == '1':
            menu_livres(biblio)
        elif choix == '2':
            menu_adherents(biblio)
        elif choix == '3':
            menu_emprunts(biblio)
        elif choix == '4':
            menu_consultation(biblio)
        elif choix == '5':
            afficher_infos()
        elif choix == '0':
            print("\n👋 Merci d'avoir utilisé notre service !")
            print("   À bientôt à la bibliothèque ! 📚")
            break
        else:
            print("❌ Choix invalide, veuillez réessayer.")

if __name__ == "__main__":
    main()