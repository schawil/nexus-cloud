#!/bin/bash

# COULEURS POUR LE STYLE
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   INSTALLATION DE NEXUS CLOUD (IaaS)    ${NC}"
echo -e "${BLUE}=========================================${NC}"

# 1. VÉRIFICATION SUDO
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Erreur : Veuillez lancer ce script avec sudo.${NC}"
    echo "Usage : sudo ./setup.sh"
    exit 1
fi

# 2. PRÉPARATION DES DOSSIERS DE TRAVAIL
echo -e "${GREEN}[+] Création de l'arborescence...${NC}"
mkdir -p keys
mkdir -p generated
# On met les droits pour que l'utilisateur non-root puisse lire les clés générées
if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" keys generated
    echo "-> Dossiers 'keys' et 'generated' configurés pour l'utilisateur $SUDO_USER."
fi

# 3. INSTALLATION DES DÉPENDANCES SYSTÈME
echo -e "${GREEN}[+] Installation des paquets KVM & Python...${NC}"
apt update -qq
# Installation silencieuse (-y) des outils de virtualisation et de l'iso maker

apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager python3-pip cloud-image-utils net-tools python3-flask python3-libvirt

# 4. GESTION DES IMAGES CLOUD (TÉLÉCHARGEMENT AUTO)
IMAGE_DIR="/var/lib/libvirt/images/base-images"
echo -e "${GREEN}[+] Configuration du stockage d'images : $IMAGE_DIR${NC}"
mkdir -p $IMAGE_DIR
# On donne les droits de lecture à tout le monde sur les images de base
# Vous pouvez restreindre cela selon vos besoins
chmod 755 /var/lib/libvirt/images/

# --- UBUNTU 22.04 ---
if [ ! -f "$IMAGE_DIR/ubuntu-22.04-server-cloudimg-amd64.img" ]; then
    echo "-> Téléchargement de l'image Ubuntu 22.04 (Cela peut prendre du temps)..."
    wget -q --show-progress -O $IMAGE_DIR/ubuntu-22.04-server-cloudimg-amd64.img https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
else
    echo "-> Image Ubuntu détectée (OK)."
fi

# ---  DEBIAN 12  ---
if [ ! -f "$IMAGE_DIR/debian-12-generic-amd64.qcow2" ]; then
    echo "-> Téléchargement de l'image Debian 12..."
    wget -q --show-progress -O $IMAGE_DIR/debian-12-generic-amd64.qcow2 https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2
else
    echo "-> Image Debian détectée (OK)."
fi

# Permissions finales sur les images
chmod 644 $IMAGE_DIR/*

# 5. CONFIGURATION DU RÉSEAU KVM
echo -e "${GREEN}[+] Activation du réseau virtuel (NAT)...${NC}"
virsh net-start default 2>/dev/null
virsh net-autostart default 2>/dev/null

# 6. AJOUT UTILISATEUR AU GROUPE LIBVIRT
if [ -n "$SUDO_USER" ]; then
    usermod -aG libvirt "$SUDO_USER"
    echo "-> Utilisateur $SUDO_USER ajouté au groupe libvirt."
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}   INSTALLATION TERMINÉE AVEC SUCCÈS !   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo "1. Redémarrez votre session (Logout/Login) pour valider les droits KVM."
echo "2. Lancez l'application : sudo python3 app.py"
echo "3. Accédez à : http://localhost:5000"