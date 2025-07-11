from supabase import create_client, Client
from dotenv import load_dotenv
import os

class SupabaseClient:
    def __init__(self):
        load_dotenv() 
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_ANON_KEY)

    def getSpendingsByPhoneNumber(self, phoneNumber: str) -> list:
        try:
            response = self.supabase.table("spending").select("*").eq("client_phone_number", phoneNumber).execute()
            return response.data
        except Exception as e:
            print(f"Ocorreu um erro ao buscar os gastos: {e}")
            return []