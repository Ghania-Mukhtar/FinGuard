import firebase_admin
from firebase_admin import credentials, firestore, storage

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'expense-system-db.appspot.com'
    })

def get_firestore():
    return firestore.client()

def get_bucket():
    return storage.bucket()