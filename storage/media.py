from db.firebase import get_bucket
import os

def upload_receipt(local_file_path, claim_id):
    """Upload image to Firebase Storage"""
    try:
        bucket = get_bucket()
        filename = f"receipts/claim_{claim_id}_{os.path.basename(local_file_path)}"
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_file_path)
        blob.make_public()
        url = blob.public_url
        print(f"File uploaded: {url}")
        return url
    except Exception as e:
        print("Upload failed:", e)
        return None