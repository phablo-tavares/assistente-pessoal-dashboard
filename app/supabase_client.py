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
        user = self.supabase.auth.sign_up(
            {
                "email":email,
                "password":password,
            }
        )
        return user.user
    
    def signIn(self,email:str, password:str):
        user = self.supabase.auth.sign_in_with_password(
            {
                "email":email,
                "password":password,
            }
        )
        return user.user
    
    def signOut(self):
        self.supabase.auth.sign_out()
        st.session_state.currentUser = None
        st.rerun()

    def sendResetPasswordEmail(self,email:str):
        self.supabase.auth.reset_password_email(email=email,options={'redirect_to': st.get_option('server.baseUrlPath')})
    
    def resetPassword(self,access_token: str,refresh_token:str,password:str):
        self.supabase.auth.set_session(access_token,refresh_token)
        self.supabase.auth.update_user({'password': password})

    def getClientData(self,authUserId: str):
        try:
            response = (
                self.supabase.table("clients")
                .select(
                    "phone_number,full_name,cpf,active_subscription,email",
                )
                .eq("auth_user_id", authUserId)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Ocorreu um erro ao buscar os dados do cliente: {e}")
            return []

    #TODO melhorar essa tratativa de exceções
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