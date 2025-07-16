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
        self.SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SERVICE_ROLE_KEY)

    def signUp(self,email:str, password:str):
        response = self.supabase.auth.sign_up(
            {
                "email":email,
                "password":password,
            }
        )
        return response

    def updateClientData(self, authUserId:str, fullName:str, phoneNumber:str, cpf:str,active_subscription):
        updateJson = {}
        updateJson['full_name'] = fullName
        updateJson['phone_number'] = phoneNumber
        updateJson['cpf'] = cpf
        if active_subscription is not None:
            updateJson['active_subscription'] = active_subscription

        response = self.supabase.table('clients').update(updateJson).eq('auth_user_id', authUserId).execute()
        return response.data
    
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
        redirect_url = "https://phablo-tavares.github.io/my-auth-redirect/index.html"
        self.supabase.auth.reset_password_email(email=email,options={'redirect_to': redirect_url})
    
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