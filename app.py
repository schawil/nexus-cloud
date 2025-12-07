import os
import subprocess
import libvirt
import uuid
import time
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

# --- CONFIGURATION ---
OS_IMAGES = {
    'ubuntu': "/var/lib/libvirt/images/base-images/ubuntu-22.04-server-cloudimg-amd64.img",
    'debian': "/var/lib/libvirt/images/base-images/debian-12-generic-amd64.qcow2"
}
VM_STORAGE_DIR = "/var/lib/libvirt/images"
GEN_DIR = os.path.join(os.getcwd(), 'generated')
KEYS_DIR = os.path.join(os.getcwd(), 'keys')
os.makedirs(GEN_DIR, exist_ok=True)
os.makedirs(KEYS_DIR, exist_ok=True)

def get_libvirt_conn():
    return libvirt.open('qemu:///system')

@app.route('/')
def index():
    return render_template('index.html')

# --- API MONITORING (CORRIGÉE POUR RAM RÉELLE) ---
@app.route('/api/monitor')
def monitor_api():
    conn = get_libvirt_conn()
    vms_stats = []
    try:
        domains = conn.listAllDomains()
        for dom in domains:
            try:
                name = dom.name()
                state, maxmem, mem, ncpu, cputime = dom.info()
                
                status_text = "Stopped"
                if state == libvirt.VIR_DOMAIN_RUNNING: status_text = "Running"
                elif state == libvirt.VIR_DOMAIN_PAUSED: status_text = "Paused"
                
                ip_addr = "N/A"
                used_mem_mb = mem / 1024 # Par défaut : mémoire allouée

                if state == libvirt.VIR_DOMAIN_RUNNING:
                    # 1. TENTATIVE DE RÉCUPÉRATION IP
                    try:
                        ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                        for _, val in ifaces.items():
                            if val['addrs']:
                                for addr in val['addrs']:
                                    if addr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                                        ip_addr = addr['addr']
                                        break
                    except: pass

                    # 2. TENTATIVE DE RÉCUPÉRATION RAM RÉELLE (RSS)
                    # Cela demande au Guest Agent combien il consomme vraiment
                    try:
                        mem_stats = dom.memoryStats()
                        if 'rss' in mem_stats:
                            # rss est en KB, on convertit en MB
                            used_mem_mb = mem_stats['rss'] / 1024
                    except: 
                        pass # Si le guest agent ne répond pas, on garde la valeur par défaut

                vms_stats.append({
                    'name': name, 
                    'status': status_text, 
                    'ip': ip_addr,
                    'cpu_time': cputime, 
                    'vcpu': ncpu,
                    'max_mem': maxmem / 1024, 
                    'used_mem': used_mem_mb, # Ici c'est maintenant la vraie valeur
                    'timestamp': time.time()
                })
            except libvirt.libvirtError: continue
    finally:
        conn.close()
    return jsonify(vms_stats)

# --- API CONTROL ---
@app.route('/api/vm/<name>/<action>', methods=['POST'])
def vm_action(name, action):
    conn = get_libvirt_conn()
    try:
        dom = conn.lookupByName(name)
        if action == 'start' and not dom.isActive():
            dom.create()
            return jsonify({'success': True})
        elif action == 'stop' and dom.isActive():
            try: dom.destroy()
            except: pass
            return jsonify({'success': True})
        elif action == 'delete':
            if dom.isActive(): dom.destroy()
            dom.undefine()
            return jsonify({'success': True})
    except Exception as e: return jsonify({'success': False, 'msg': str(e)}), 500
    finally: conn.close()
    return jsonify({'success': False}), 400

# --- DEPLOY ---
@app.route('/deploy', methods=['POST'])
def deploy():
    conn = None
    try:
        hostname = request.form['hostname']
        username = request.form['username']
        password = request.form['password']
        vcpu = int(request.form['vcpu'])
        ram = int(request.form['ram'])
        disk_size = int(request.form['disk'])
        os_type = request.form.get('os_type', 'ubuntu')

        # Limites
        if vcpu > 3: vcpu = 3
        if ram > 4096: ram = 4096
        if disk_size > 50: disk_size = 50

        base_image_path = OS_IMAGES.get(os_type, OS_IMAGES['ubuntu'])

        # SSH Logic
        ssh_method = request.form.get('ssh_method')
        final_ssh_pub_key = ""
        generated_key_path = None

        if ssh_method == 'paste':
            final_ssh_pub_key = request.form.get('ssh_key_paste', '').strip()
        elif ssh_method == 'generate':
            key_name = request.form.get('ssh_key_name', '').strip()
            if not key_name: return "Nom clé manquant", 400
            priv_path = os.path.join(KEYS_DIR, key_name)
            pub_path = priv_path + ".pub"
            if os.path.exists(priv_path): return "Clé existe déjà", 409
            
            subprocess.run(['ssh-keygen', '-q', '-t', 'rsa', '-b', '2048', '-N', '', '-f', priv_path], check=True)
            
            real_user = int(os.environ.get('SUDO_UID', os.getuid()))
            real_group = int(os.environ.get('SUDO_GID', os.getgid()))
            os.chown(priv_path, real_user, real_group)
            os.chown(pub_path, real_user, real_group)
            os.chmod(priv_path, 0o600)
            with open(pub_path, 'r') as f: final_ssh_pub_key = f.read().strip()
            generated_key_path = key_name

        conn = get_libvirt_conn()
        try:
            conn.lookupByName(hostname)
            conn.close()
            return "VM existe déjà", 409
        except: pass
        finally: 
            if conn: conn.close()

        request_id = str(uuid.uuid4())[:8]
        vm_disk = f"{VM_STORAGE_DIR}/{hostname}.qcow2"
        seed_iso = f"{GEN_DIR}/{hostname}-seed.iso"
        user_data = f"{GEN_DIR}/{hostname}-user-data"
        meta_data = f"{GEN_DIR}/{hostname}-meta-data"

        subprocess.run(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", base_image_path, vm_disk, f"{disk_size}G"], check=True)

        ssh_block = ""
        if final_ssh_pub_key: ssh_block = f"\n      - {final_ssh_pub_key}"

# CLOUD-INIT BLINDÉ (Network V2 + User)
# DANS app.py -> fonction deploy()
        
# --- CORRECTION CRITIQUE MOT DE PASSE (TEXTE BRUT) ---
        
        # On prépare le bloc SSH
        ssh_block = ""
        if final_ssh_pub_key:
            # Attention aux 6 espaces ici, c'est vital pour le YAML
            ssh_block = f"\n      - {final_ssh_pub_key}"

        ud_content = f"""#cloud-config
hostname: {hostname}
manage_etc_hosts: true

# 1. CRÉATION UTILISATEUR (SANS LE MOT DE PASSE ICI)
users:
  - default
  - name: {username}
    groups: sudo, adm, dialout, cdrom, plugdev, lxd
    shell: /bin/bash
    lock_passwd: false
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:{ssh_block}

# 2. APPLICATION DU MOT DE PASSE EN CLAIR
# C'est ici que la magie opère : on force le mot de passe en texte brut
chpasswd:
  list: |
    {username}:{password}
  expire: true

# 3. CONFIGURATION SSH
ssh_pwauth: true

# 4. RÉSEAU TURBO (V2)
write_files:
  - path: /etc/netplan/99-custom.yaml
    content: |
      network:
        version: 2
        ethernets:
          main:
            match:
              name: "e*"
            dhcp4: true
    permissions: '0600'

# 5. OPTIMISATIONS
package_update: false
package_upgrade: false

runcmd:
  - netplan apply
  - systemctl start qemu-guest-agent
"""
        # ... (suite de la fonction) ...
        with open(user_data, 'w') as f: f.write(ud_content)
        with open(meta_data, 'w') as f: f.write(f"instance-id: {hostname}\nlocal-hostname: {hostname}")
        
        subprocess.run(["cloud-localds", seed_iso, user_data, meta_data], check=True)

        variant = "ubuntu22.04" if os_type == 'ubuntu' else "debian11"
        cmd = ["virt-install", f"--name={hostname}", f"--vcpus={vcpu}", f"--memory={ram}",
               f"--disk=path={vm_disk},device=disk,bus=virtio", f"--disk=path={seed_iso},device=cdrom",
               f"--os-variant={variant}", "--import", "--noautoconsole", "--graphics=none",
               "--network", "network=default,model=virtio"]
        subprocess.run(cmd, check=True)

        return render_template('success.html', hostname=hostname, key_download=generated_key_path)

    except Exception as e: return str(e), 500

@app.route('/download_key/<filename>')
def download_key(filename):
    return send_file(os.path.join(KEYS_DIR, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)