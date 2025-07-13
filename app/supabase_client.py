from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date
import streamlit as st 

class SupabaseClient:
    def __init__(self):
        load_dotenv() 
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_ANON_KEY)

    def signUp(self,email:str, password:str):
        try:
            user = self.supabase.auth.sign_up(
                {
                    "email":email,
                    "password":password,
                }
            )
            return user.user
        except Exception as e:
            st.error(f'Erro no cadastro, tente novamente mais tarde')
    
    def signIn(self,email:str, password:str):
        try:
            user = self.supabase.auth.sign_in_with_password(
                {
                    "email":email,
                    "password":password,
                }
            )
            return user.user
        except Exception as e:
            st.error(f'Erro no login, tente novamente mais tarde')
    
    def signOut(self,email:str, password:str):
        try:
            self.supabase.auth.sign_out()
            st.session_state.userEmail = None
            st.rerun()
        except Exception as e:
            st.error(f'Erro no logout, tente novamente mais tarde')

    def getSpendings(self, phoneNumber: str, startDate:date, endDate:date) -> list:
        try:
            response = (
                self.supabase.table("spending")
                .select(
                    "spending_value,spending_category,spending_date,spending_description",
                )
                .eq("client_phone_number", phoneNumber)
                .gte("spending_date", startDate.isoformat())
                .lte("spending_date", endDate.isoformat())
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Ocorreu um erro ao buscar os gastos: {e}")
            return []