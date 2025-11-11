#!/usr/bin/env python3
"""
Génère manifest.json à partir de patrimoine.md (migration v1 → v2)

Usage:
    python tools/generate_manifest.py [--sources-dir sources/]

Ce script:
1. Parse patrimoine.md (format v1.0)
2. Extrait profil investisseur et comptes
3. Génère manifest.json (format v2.0) avec parsers auto-détectés
4. Valide la structure générée
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def parse_patrimoine_md(md_path: Path) -> Dict:
    """Parse patrimoine.md format v1.0 et extrait les données"""
    if not md_path.exists():
        raise FileNotFoundError(f"Fichier patrimoine.md introuvable : {md_path}")

    content = md_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    manifest = {
        "version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "profil_investisseur": {
            "identite": {},
            "professionnel": {},
            "investissement": {}
        },
        "comptes": [],
        "crypto": [],
        "immobilier": []
    }

    current_section = None
    current_etablissement = None
    current_etablissement_code = None

    for line in lines:
        line = line.strip()

        # Section Profil
        if line.startswith("## Profil"):
            current_section = "profil"
            continue

        # Section Epargne
        elif line.startswith("## Epargne") or line.startswith("## Épargne"):
            current_section = "epargne"
            continue

        # Section Crypto
        elif line.startswith("## Crypto"):
            current_section = "crypto"
            continue

        # Section Immobilier
        elif line.startswith("## Immobilier"):
            current_section = "immobilier"
            continue

        # Parser section Profil
        if current_section == "profil" and line.startswith("- "):
            _parse_profil_line(line, manifest["profil_investisseur"])

        # Parser section Epargne
        elif current_section == "epargne":
            if line.startswith("### "):
                # Nouveau établissement
                etab_match = re.match(r"###\s+(\w+)(?:\s+\((.+?)\))?$", line)
                if etab_match:
                    current_etablissement_code = etab_match.group(1)
                    current_etablissement = etab_match.group(2) if etab_match.group(2) else current_etablissement_code

            elif line.startswith("- ") and current_etablissement:
                # Ligne de compte
                _parse_compte_line(line, current_etablissement, current_etablissement_code, manifest["comptes"])

    # Valider profil_risque défini
    if not manifest["profil_investisseur"]["investissement"].get("profil_risque"):
        print("⚠️  Type d'investissement non détecté, utilisation profil 'equilibre' par défaut")
        manifest["profil_investisseur"]["investissement"]["profil_risque"] = "equilibre"

    return manifest


def _parse_profil_line(line: str, profil: Dict):
    """Parse une ligne de profil et remplit le dict"""
    match = re.match(r"-\s*(.+?)\s*:\s*(.+)", line)
    if not match:
        return

    key = match.group(1).strip().lower()
    value = match.group(2).strip()

    # Mapping vers nouvelle structure
    if key == "genre":
        profil["identite"]["genre"] = value

    elif "naissance" in key:
        # Convertir DD/MM/YYYY -> YYYY-MM-DD
        date_match = re.match(r"(\d{2})/(\d{2})/(\d{4})", value)
        if date_match:
            profil["identite"]["date_naissance"] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
        else:
            profil["identite"]["date_naissance"] = value

    elif "situation" in key or "familiale" in key:
        profil["identite"]["situation_familiale"] = value

    elif "enfants" in key or "enfant" in key:
        # Extraire nombre
        nb_match = re.search(r"(\d+)", value)
        if nb_match:
            profil["identite"]["enfants"] = int(nb_match.group(1))
        else:
            profil["identite"]["enfants"] = 0

    elif key == "statut":
        profil["professionnel"]["statut"] = value

    elif key == "profession":
        profil["professionnel"]["profession"] = value

    elif "revenu" in key:
        # Extraire montant
        amount_match = re.search(r"([\d\s,]+)", value)
        if amount_match:
            montant_str = amount_match.group(1).replace(" ", "").replace(",", "")
            try:
                profil["professionnel"]["revenu_mensuel_net"] = int(montant_str)
            except ValueError:
                pass

    elif "investissement" in key or "type" in key or "profil" in key:
        # Mapper type d'investissement vers profil_risque
        value_lower = value.lower()
        if "dynamique" in value_lower or "agressif" in value_lower or "offensif" in value_lower:
            profil["investissement"]["profil_risque"] = "dynamique"
        elif "équilibré" in value_lower or "equilibre" in value_lower or "modéré" in value_lower or "moderate" in value_lower:
            profil["investissement"]["profil_risque"] = "equilibre"
        elif "prudent" in value_lower or "conservateur" in value_lower or "défensif" in value_lower:
            profil["investissement"]["profil_risque"] = "prudent"
        else:
            profil["investissement"]["profil_risque"] = "default"


def _parse_compte_line(line: str, etablissement: str, code_etab: str, comptes: List[Dict]):
    """Parse une ligne de compte et génère une entrée manifest"""
    # Détection fichier référencé
    file_ref = re.search(r'"(.+?\.(?:csv|pdf|json))"', line, re.IGNORECASE)

    if file_ref:
        filename = file_ref.group(1)

        # Détecter type de compte depuis le nom du fichier
        type_compte = _detect_type_compte(filename)

        # Détecter parser strategy
        parser_strategy, fallback_parsers = _detect_parser_strategy(code_etab, type_compte, filename)

        # Générer ID unique
        compte_id = f"{code_etab.lower()}_{type_compte.lower().replace('-', '_')}_{len(comptes) + 1:03d}"

        compte_entry = {
            "id": compte_id,
            "etablissement": _normalize_etablissement(code_etab),
            "type_compte": type_compte,
            "source_file": filename,
            "parser_strategy": parser_strategy,
            "fallback_parsers": fallback_parsers,
            "metadata": {
                "format_version": "auto_detected"
            }
        }

        comptes.append(compte_entry)


def _detect_type_compte(filename: str) -> str:
    """Détecte le type de compte depuis le nom du fichier"""
    filename_upper = filename.upper()

    if "PEA-PME" in filename_upper or "PEA_PME" in filename_upper:
        return "PEA-PME"
    elif "PEA" in filename_upper:
        return "PEA"
    elif "AV" in filename_upper or "ASSURANCE" in filename_upper:
        return "Assurance-vie"
    elif "CTO" in filename_upper:
        return "CTO"
    elif "PER" in filename_upper:
        return "PER"
    elif "LIVRET" in filename_upper:
        return "Livret"
    else:
        return "Compte"


def _normalize_etablissement(code: str) -> str:
    """Normalise le code établissement vers le nom standard"""
    mapping = {
        "CA": "credit_agricole",
        "BFB": "bforbank",
        "SG": "societe_generale",
        "BOB": "boursobank",
        "DGO": "degiro",
        "Spiko": "spiko",
        "Ledger": "ledger",
        "Bitstack": "bitstack",
        "CrypCool": "crypcool",
        "Aave": "aave"
    }

    return mapping.get(code, code.lower())


def _detect_parser_strategy(code_etab: str, type_compte: str, filename: str) -> tuple:
    """
    Détecte le parser strategy approprié et ses fallbacks

    Returns:
        (parser_strategy, fallback_parsers)
    """
    extension = filename.lower().split('.')[-1]

    # Crédit Agricole
    if code_etab == "CA":
        if type_compte in ["PEA", "PEA-PME"]:
            return ("credit_agricole.pea.v2025", ["generic.csv.flexible"])
        elif type_compte == "Assurance-vie":
            return ("credit_agricole.av.v2_lignes", [])

    # Fichiers CSV génériques
    if extension == "csv":
        return ("generic.csv.flexible", [])

    # Par défaut
    return ("generic.csv.flexible", [])


def validate_manifest(manifest: Dict) -> List[str]:
    """Valide la structure du manifest généré"""
    errors = []

    # Vérifier version
    if manifest.get("version") != "2.0.0":
        errors.append("Version invalide (attendue: 2.0.0)")

    # Vérifier profil investisseur
    if "profil_investisseur" not in manifest:
        errors.append("Section profil_investisseur manquante")
    else:
        profil = manifest["profil_investisseur"]
        if not profil.get("investissement", {}).get("profil_risque"):
            errors.append("profil_risque manquant dans investissement")
        else:
            profil_risque = profil["investissement"]["profil_risque"]
            if profil_risque not in ["dynamique", "equilibre", "prudent", "default"]:
                errors.append(f"profil_risque invalide: {profil_risque}")

    # Vérifier comptes
    if not manifest.get("comptes"):
        errors.append("Aucun compte défini")

    for i, compte in enumerate(manifest.get("comptes", [])):
        required = ["id", "etablissement", "type_compte", "source_file", "parser_strategy"]
        for field in required:
            if field not in compte:
                errors.append(f"Compte #{i}: champ '{field}' manquant")

    return errors


def main():
    """Point d'entrée principal"""
    # Déterminer répertoire sources
    if len(sys.argv) > 1:
        sources_dir = Path(sys.argv[1])
    else:
        sources_dir = Path("sources")

    patrimoine_md = sources_dir / "patrimoine.md"
    manifest_output = sources_dir / "manifest.json"

    print("=" * 60)
    print("Génération de manifest.json à partir de patrimoine.md")
    print("=" * 60)
    print()

    # Vérifier existence patrimoine.md
    if not patrimoine_md.exists():
        print(f"❌ Erreur : Fichier introuvable : {patrimoine_md}")
        print()
        print("Usage:")
        print("  python tools/generate_manifest.py [sources_dir]")
        print()
        print("Exemple:")
        print("  python tools/generate_manifest.py sources/")
        return 1

    # Parser patrimoine.md
    print(f"📝 Parsing {patrimoine_md}...")
    try:
        manifest = parse_patrimoine_md(patrimoine_md)
    except Exception as e:
        print(f"❌ Erreur lors du parsing : {e}")
        return 1

    # Afficher résultats
    profil = manifest["profil_investisseur"]
    print(f"✓ Profil détecté : {profil['investissement'].get('profil_risque', 'inconnu')}")
    print(f"✓ {len(manifest['comptes'])} comptes détectés")

    if manifest["comptes"]:
        print()
        print("Comptes détectés :")
        for compte in manifest["comptes"]:
            print(f"  - {compte['id']}: {compte['type_compte']} ({compte['source_file']})")
            print(f"    Parser: {compte['parser_strategy']}")

    # Valider
    print()
    print("🔍 Validation du manifest...")
    errors = validate_manifest(manifest)

    if errors:
        print("❌ Erreurs de validation :")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("✓ Manifest valide")

    # Sauvegarder
    print()
    print(f"💾 Sauvegarde {manifest_output}...")
    try:
        with open(manifest_output, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✅ Manifest généré : {manifest_output}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return 1

    # Instructions suivantes
    print()
    print("=" * 60)
    print("✅ Migration v1 → v2 terminée avec succès")
    print("=" * 60)
    print()
    print("⚠️  Prochaines étapes :")
    print()
    print("1. Vérifier manifest.json et ajuster si nécessaire")
    print("   - Profil investisseur complet ?")
    print("   - Tous les comptes détectés ?")
    print("   - Parsers corrects ?")
    print()
    print("2. Mettre à jour config.yaml :")
    print("   - normalizer.input_file: \"manifest.json\"")
    print("   - analyzer.active_profile_override: null")
    print()
    print("3. Tester avec: python main.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
