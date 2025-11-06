#!/usr/bin/env python
"""Test de résolution des chemins relatifs"""
import os
from pathlib import Path

print("=== TEST DE RÉSOLUTION DES CHEMINS ===\n")

# Simule __file__ depuis tools/analyzer.py
print("1. Dans tools/analyzer.py:")
analyzer_file = os.path.join("tools", "analyzer.py")
config_dir = os.path.join(
    os.path.dirname(os.path.dirname(analyzer_file)),
    "config",
)
print(f"   __file__ simulé: {analyzer_file}")
print(f"   os.path.dirname(__file__): {os.path.dirname(analyzer_file)}")
print(f"   os.path.dirname(os.path.dirname(__file__)): {os.path.dirname(os.path.dirname(analyzer_file))}")
print(f"   config_dir résolu: {config_dir}")
print(f"   Existe? {os.path.exists(config_dir)}\n")

# Simule __file__ depuis tools/utils/portfolio_optimizer.py
print("2. Dans tools/utils/portfolio_optimizer.py:")
optimizer_file = os.path.join("tools", "utils", "portfolio_optimizer.py")
config_dir2 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(optimizer_file))),
    "config",
)
print(f"   __file__ simulé: {optimizer_file}")
print(f"   os.path.dirname(__file__): {os.path.dirname(optimizer_file)}")
print(f"   os.path.dirname(os.path.dirname(__file__)): {os.path.dirname(os.path.dirname(optimizer_file))}")
print(f"   os.path.dirname(os.path.dirname(os.path.dirname(__file__))): {os.path.dirname(os.path.dirname(os.path.dirname(optimizer_file)))}")
print(f"   config_dir résolu: {config_dir2}")
print(f"   Existe? {os.path.exists(config_dir2)}\n")

# Test des chemins dans config.yaml
print("3. Chemins dans config.yaml:")
paths = ["sources/", "templates/", "generated/", "logs/"]
for p in paths:
    exists = os.path.exists(p)
    print(f"   {p}: {'✅' if exists else '❌'}")

print("\n4. Fichiers critiques:")
files = [
    "config/config.yaml",
    "config/analysis.yaml",
    "sources/patrimoine.md",
    "templates/rapport_template.html",
    "templates/rapport.css"
]
for f in files:
    exists = os.path.exists(f)
    print(f"   {f}: {'✅' if exists else '❌'}")
