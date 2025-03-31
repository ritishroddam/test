from app import create_app, socketio
import os

app = create_app()

if __name__ == '__main__':
    # Ensure the cert directory exists
    os.makedirs('cert', exist_ok=True)
    
    # Check if certificates exist, if not generate them
    cert_path = 'cert/cert.pem'
    key_path = 'cert/key.pem'
    
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print("Generating self-signed certificates...")
        os.system(f'openssl req -x509 -newkey rsa:4096 -nodes -out {cert_path} -keyout {key_path} -days 365 -subj "/CN=localhost"')
    
    # Run the app with HTTPS
    socketio.run(
        app,
        ssl_context=(cert_path, key_path),
        debug=True,
        host='0.0.0.0',
        port=8888
    )